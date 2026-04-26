import os, string, re, json, sys, msvcrt, shutil, subprocess, time
from colorama import init, Fore
from typing import Any, Callable, Generator, Iterable
init(True)

configPath = "\\demosearch.cfg"
forceUpdate = False
dumperName = "demo-dumper.exe"

defaultCfg = {
    "demoPath": "\\tf\\demos",
    "gamePaths": ["\\Program Files (x86)\\Steam\\steamapps\\common\\Team Fortress 2",
                  "\\SteamLibrary\\Team Fortress 2",
                  "\\SteamLibrary\\steamapps\\common\\Team Fortress 2"],
    "pathBlacklist": [],
    "limitAmount": 1000,
    "oldestFirst": False,
    "_lastModify": {}
}

cwd = os.getcwd()
configFullpath = f"{cwd.strip("\\")}\\{configPath.strip("\\")}"
if not os.path.isfile(configFullpath):
    with open(configFullpath, "wt") as file:
        file.write(json.dumps(defaultCfg, indent=4))

    print(f"Created config at {configFullpath}.\nYou can change the values to your liking or keep them as default, and then re-run the program.\n\nPress enter to exit...")
    input()
    sys.exit()

with open(configFullpath, "rt") as file_:
    config:dict[str, str] = json.loads((file_.read())) or defaultCfg

class List(list):
    def find_all(self, /, *, key: Callable|type) -> Generator[Any]:
        if isinstance(key, (type)):
            for item in self:
                if isinstance(item, key):
                    yield item
        else:
            for item in self:
                try:
                    if key(item):
                        yield item
                except:continue
    
    def find(self, /, *, key: Callable|type) -> Any:
        if isinstance(key, (type)):
            for item in self:
                if isinstance(item, key):
                    return item
        else:
            for item in self:
                try:
                    if key(item):
                        return item
                except:continue
        return None


missing = 0
for key in defaultCfg.keys():
    if config.get(key) is None:
        print(f"{Fore.YELLOW}Missing {key} from config, using \"{defaultCfg[key]}\"")
        missing += 1
if missing:
    print()

def get_drive_letters():
    return [
        f"{d}:"
        for d in string.ascii_uppercase
        if os.path.exists(f"{d}:\\")
    ]

def cls():
    mapping = {"win32":"cls", "linux":"clear", "darwin":"clear", "cygwin":"cls"}
    os.system(mapping.get(sys.platform, "clear"))

def Pause(text:str=None) -> str:
    if text: print(text)
    return msvcrt.getwch()

def parseInput(_in:str) -> list[str]:
    isContinuation = False; d = []; toJoin = []
    for split in _in.strip().split():
        if isContinuation:
            endsWith = split.endswith("\"")
            if endsWith: toJoin.append(split[:-1])
            else: toJoin.append(split)
            if endsWith: isContinuation = False; d.append(" ".join(toJoin)); toJoin.clear()
        else:
            if split.startswith("\""):isContinuation = True; toJoin.append(split[1:])
            else: d.append(split)
    if toJoin: d.append(" ".join(toJoin))
    return d

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

def flatten_iterable(iterable:list | tuple) -> list:
    output = []
    for item in iterable:
        if isinstance(item, (list, tuple)):
            output.extend(flatten_iterable(item))

        else:
            output.append(item)

    return output

steamID64Offset = 76561197960265728
def steamId64To32(id: int):
    return f"[U:1:{id-steamID64Offset}]"
    # return id-steamID64Offset

def find_name_in_demos(targets_:list[str]):
    targets = [t.lower() for t in targets_]
    matches = 0
    needsUpdate = False

    with open(configFullpath, "rt") as file_:
        config:dict[str, str] = json.loads((file_.read())) or defaultCfg

    demoPath = config.get("demoPath", defaultCfg["demoPath"])
    gamePaths = config.get("gamePaths", defaultCfg["gamePaths"])
    pathBlacklist = config.get("pathBlacklist", defaultCfg["pathBlacklist"])
    limitAmount = config.get("limitAmount", defaultCfg["limitAmount"])
    oldestFirst = config.get("oldestFirst", defaultCfg["oldestFirst"])

    for drive in get_drive_letters():
        for path in gamePaths:
            gamePath = f"{drive}\\{re.sub(r'^[A-Za-z]:', '', path.strip('\\'))}"

            if os.path.exists(gamePath):
                fullPath = f"{gamePath}\\{demoPath.strip('\\')}"
                if fullPath in pathBlacklist:
                    continue

                if not os.path.exists(fullPath):
                    continue
                print("")
                print(f"Path: {fullPath}")
                dumpFile = os.path.join(fullPath, "demo_dump.json")

                dirFiles = sorted([os.path.getmtime(os.path.join(fullPath, t)) for t in os.listdir(fullPath) if t.endswith(".dem")], reverse=True)
                demAmount = len(dirFiles)
                matchAmount = 0
                newestFile = int(dirFiles[0])

                _lastModifyCurrentDir: dict[str, int] = config.get("_lastModify", {}).get(fullPath, 0)

                targetExe = os.path.join(fullPath, dumperName)
                if newestFile > _lastModifyCurrentDir or not os.path.isfile(dumpFile) or forceUpdate:
                    print("")
                    print("Parsing demos...", end="\r")
                    bundledExe = get_bundled_exe()
                    
                    shutil.copy2(bundledExe, targetExe)
                    subprocess.run(targetExe, cwd=fullPath, stdout=subprocess.DEVNULL)

                    config["_lastModify"][fullPath] = newestFile
                    needsUpdate = True
                    print("Parsing demos... Done")

                with open(dumpFile, encoding="utf-8") as dump:
                    dumpBytes = dump.read()
                    dumpData: dict[str, dict[str, str]] = json.loads(dumpBytes)
                    amount = 0
                    dump.close()

                    print("")
                    print("Analyzing demos...")
                    print("")
                    for root, _, files in os.walk(fullPath):
                        files.sort(key=lambda f: os.path.getmtime(os.path.join(root, f)))

                        fileAmount = sum(1 for x in os.listdir(fullPath) if os.path.isfile(os.path.join(root, x)) and x.endswith(".dem"))
                        filesRead = 0

                        if not oldestFirst:
                            files.reverse()

                        for file in files:
                            if file.endswith(".dem"):
                                if limitAmount > 0 and amount > limitAmount:
                                    break

                                filePath = os.path.join(fullPath, file)

                                amount += 1
                                filesRead += 1
                                os.system(f"title {progress_bar(length=60, progress=filesRead/fileAmount)}")

                                temp = dumpData.get(file, {})
                                data = list(map(lambda x: str(x).lower(), list(temp.keys()) + list(temp.values())))
                                matchesFound = [
                                    target for target in targets
                                    if any(target in item for item in data)
                                ]

                                if matchesFound:
                                    matches += 1
                                    matchAmount += 1
                                    print(f"{Fore.GREEN}[MATCH] {Fore.RESET}{filePath} | "+ ", ".join(f"{Fore.BLUE}{val}{Fore.RESET}" for val in matchesFound))

                if matchAmount > 0:
                    print("")
                print(f"{Fore.GREEN}{matchAmount/demAmount*100:.2f}{Fore.RESET}% matches ({Fore.GREEN}{matchAmount}{Fore.RESET})")

                time.sleep(.5)
                if os.path.exists(targetExe):
                    try: os.remove(targetExe)
                    except PermissionError:
                        print("")
                        print("Could not delete exe (still in use?)")

    if needsUpdate:
        with open(configFullpath, "wt") as file_:
            if file_.writable():
                file_.write(json.dumps(config, indent=4))

    return matches

def wait_for_input(valid_keys: Iterable):
    while True:
        c = ord(Pause())
        if c in valid_keys: # 27 esc, 32 space
            return c

if __name__ == "__main__":
    while True:
        print('Type "--help" for more info.')
        in_ = input("Enter player name or id to search for: ").strip()
        targets = List(parseInput(in_))

        for i, target in enumerate(targets):
            if re.fullmatch(r"7656[0-9]{13}", target):
                targets[i] = str(steamId64To32(int(target)))

        if targets.find(key=lambda x: x == "--help"):
            print()

        if targets.find(key=lambda x: x == "--f"):
            forceUpdate = True
            targets = list(filter(lambda x: x != "--f", targets))

        if not targets:
            print("Input something you goober.")

        else:
            print("")
            print(f"{', '.join(targets)}")

            results = find_name_in_demos(targets)
            
            print("")
            if not results:
                print("No matches found.")
            else:
                print(f"{Fore.RED}{results}{Fore.RESET} match{'' if results == 1 else 'es'} found.")

        print("")
        print("Press [ESC] to exit.\nPress [Space] to continue...")
        c = wait_for_input((27, 32))
        if c == 27:
            break
        cls()