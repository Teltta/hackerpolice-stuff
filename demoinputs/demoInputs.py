import os, re, sys, msvcrt, shutil, subprocess, time, json
from colorama import init, Fore
init(True)

dumperName = "demo-dumper-v3.exe"

def cls():
    mapping = {"win32":"cls", "linux":"clear", "darwin":"clear", "cygwin":"cls"}
    os.system(mapping.get(sys.platform, "clear"))

def Pause(text:str=None) -> str:
    if text: print(text)
    return msvcrt.getwch()

def progress_bar(foreground:str="█", background:str="░", length:int=12, progress:float=0.7) -> str:
    if progress < 0:
        progress = progress * -1
    if progress > 1:
        progress = progress - int(progress)
    temp = int(length*progress)
    return "".join([foreground for i in range(temp)]+[background for i in range(length-temp)])

def get_bundled_exe():
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, dumperName)
    return os.path.abspath(dumperName)

def parseDemoInputs() -> dict[str, list[str]]:
    cwd = os.getcwd()

    files = os.listdir(cwd)
    dirFiles = [t for t in files if t.endswith(".dem")]
    dirFiles.reverse()
    demAmount = len(dirFiles)

    targetExe = os.path.join(cwd, dumperName)
    bundledExe = get_bundled_exe()

    lineRegex = re.compile(r"([0-9]+)\: ([\+\-a-z0-9]+) ([0-9]+) \s+-> ([\+\-a-zA-Z\_]+)")
                    
    shutil.copy2(bundledExe, targetExe)

    m: dict[str, list[str]] = {}
    # toWrite: dict[str, list[str]] = {}
    outputFileName = "demoinputs.txt"
    
    i = 0
    for file in dirFiles:
        subprocess.run(f"{targetExe} inputs \"{file}\" {outputFileName}", stdout=subprocess.DEVNULL)
        
        with open(outputFileName, "rt", encoding="utf-8", errors="ignore") as file_:
            if not file_.readable():
                continue
            lines = file_.readlines()

        i += 1
        os.system(f"title {progress_bar(length=60, progress=i/demAmount)}")

        print(f"File: {file}")

        consecutiveCount = 0
        triggerbot =  False
        for line in lines:
            _match = lineRegex.match(line)
            if not _match:
                continue

            tick, command, commandNum, commandString = _match.groups()
            
            # e = toWrite.get(file)
            # if e is None:
            #     toWrite[file] = []
            # toWrite[file].append(f"{tick}: {command} {commandNum}   {commandString}")
            
            match (command):
                case "+attack":
                    consecutiveCount += 1
                case "-attack":
                    consecutiveCount -= 1
                case _:
                    continue
            
            if consecutiveCount >= 2:
                print(f"    {Fore.GREEN}{tick}{Fore.RESET}: {Fore.RED}Triggerbot")
                
                exists = m.get(file)
                if exists is None:
                    m[file] = []
                
                m[file].append(tick)

                triggerbot = True
        
        if triggerbot:
            print("")

    time.sleep(.5)
    if os.path.exists(targetExe):
        try: os.remove(targetExe)
        except PermissionError:
            print("")
            print("Could not delete exe (still in use?)")

    demoinputsPath = os.path.join(cwd, outputFileName)
    if os.path.exists(demoinputsPath):
        try: os.remove(demoinputsPath)
        except PermissionError:
            pass

    # with open("allDemo0Inputs.txt", "wt") as f:
    #     if f.writable():
    #         f.write(json.dumps(toWrite, indent=4))

    return m

if __name__ == "__main__":
    output = parseDemoInputs()

    cls()
    if output:
        print("Triggerbot Matches: ")
        print("")
        for key, value in output.items():
            print(key)
            print(f"Ticks: {Fore.RED}{f'{Fore.RESET}, {Fore.RED}'.join(value)}")
            print("")
    else:
        print("No triggerbot instances.")

    print("")
    print("Press [ESC] to exit.")
    while True:
        c = ord(Pause())
        if c == 27:
            break
