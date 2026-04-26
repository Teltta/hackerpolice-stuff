import os, string, time, json, ctypes

from ctypes import wintypes
from sys import exit #pyinstaller dont like std exit
from colorama import init, Fore
init(True)

configPath = "\\removeDemos.cfg"

defaultCfg = {"explanations": [
              "NOTE: The script will always delete the oldest demos first",
              "For example; there are 36 demos and the file limit is 30, the script will delete the oldest 6 demos",
              "",
              "You can mark demos as \'important\' by putting a ! in front of its filename to make the script ignore it.",
              "You can delete these explanations if you want but dont complain when you dont know what each setting does.",
              "",
              "timeWindow [number]: If the file is older than x amount seconds it will be deleted, e.g 3600 -> 1hr",
              "maxFiles [number]:   Maximum amount of .dem files allowed.",
              "maxSize [number]:    The maximum file size of all .dem files combined in bytes.",
              "minSize [number]:    Minimum individual size per file in bytes, e.g 5000 -> files less than 5kb will be deleted.",
              "",
              "moveToTrashbin [true/false]:  Whether to move the files to the trashbin or straight up delete them. Setting this to false will cause the files to come unrecoverable.",
              "keepConsoleOpen [true/false]: Whether to keep the console open after it has deleted the files. Useful if you wanna look at its output.",
              "",
              "demoPath [path]: Path to the demo files relative to the root tf2 directory.",
              "gamePaths: [list {path} ]: Path(s) to tf2 root directory without the drive letter in front. e.g Program Files (x86)\\Steam\\steamapps\\..."],

              "timeWindow": 604_800,
              "maxFiles": 100,
              "maxSize": 2_000_000_000,
              "minSize": 3_000_000,
              "moveToTrashbin": True,
              "keepConsoleOpen": False,

              "demoPath": "\\tf\\demos",
              "gamePaths": ["\\Program Files (x86)\\Steam\\steamapps\\common\\Team Fortress 2",
                            "\\SteamLibrary\\Team Fortress 2",
                            "\\SteamLibrary\\steamapps\\common\\Team Fortress 2"]
              }

cwd = os.getcwd()
configFullpath = f"{cwd.strip("\\")}\\{configPath.strip("\\")}"
if not os.path.isfile(configFullpath):
    with open(configFullpath, "wt") as file:
        file.write(json.dumps(defaultCfg, indent=4))

    print(f"Created config at {configFullpath}.\nYou can change the values to your liking or keep them as default, and then re-run the program.\n\nPress enter to exit...")
    input()
    exit()

with open(configFullpath, "rt") as file_:
    config:dict[str, str] = json.loads((file_.read())) or defaultCfg

timeWindow = config.get("timeWindow", defaultCfg["timeWindow"])
maxFiles = config.get("maxFiles", defaultCfg["maxFiles"])
maxSize = config.get("maxSize", defaultCfg["maxSize"])
minSize = config.get("minSize", defaultCfg["minSize"])

moveToTrashbin = config.get("moveToTrashbin", defaultCfg["moveToTrashbin"])
keepConsoleOpen = config.get("keepConsoleOpen", defaultCfg["keepConsoleOpen"])

demoPath = config.get("demoPath", defaultCfg["demoPath"])
gamePaths = config.get("gamePaths", defaultCfg["gamePaths"])

FOF_ALLOWUNDO = 0x0040
FOF_NOCONFIRMATION = 0x0010
FOF_SILENT = 0x0004

class SHFILEOPSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("wFunc", wintypes.UINT),
        ("pFrom", wintypes.LPCWSTR),
        ("pTo", wintypes.LPCWSTR),
        ("fFlags", wintypes.UINT),
        ("fAnyOperationsAborted", wintypes.BOOL),
        ("hNameMappings", wintypes.LPVOID),
        ("lpszProgressTitle", wintypes.LPCWSTR),
    ]

SHFileOperation = ctypes.windll.shell32.SHFileOperationW
FO_DELETE = 0x0003

def send_to_recycle_bin(path):
    fileop = SHFILEOPSTRUCT()
    fileop.wFunc = FO_DELETE
    fileop.pFrom = path + "\0\0"
    fileop.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT
    SHFileOperation(ctypes.byref(fileop))

def get_drive_letters():
    return [
        f"{d}:"
        for d in string.ascii_uppercase
        if os.path.exists(f"{d}:\\")
    ]


for drive in get_drive_letters():
    for path in gamePaths:
        gamePath = f"{drive}\\{path.strip('\\')}"

        if os.path.exists(gamePath):
            fullPath = f"{gamePath}\\{demoPath.strip('\\')}"

            if os.path.exists(fullPath):
                print("Path: ", fullPath)
                print("")

                toDelete = []
                files = sorted(list(os.listdir(fullPath)), key=lambda x: os.path.getmtime(f"{fullPath}\\{x.strip('\\')}"), reverse=True)

                i = 0
                currentSize = 0
                for file in files:
                    if not file.endswith(".dem"):
                        continue

                    if file.startswith("!"): # ignore files marked as "important" by the user
                        continue

                    filePath = f"{fullPath}\\{file.strip('\\')}"
                    i += 1

                    if (i > maxFiles):
                        toDelete.append(filePath)
                        print(f"Max files reached, deleting {Fore.BLUE}{file}{Fore.RESET}. {i} > {maxFiles}")
                        continue
                    
                    fileSize = os.path.getsize(filePath)
                    if (fileSize < minSize):
                        toDelete.append(filePath)
                        print(f"Min file size exceeded, deleting {Fore.BLUE}{file}{Fore.RESET}. {fileSize:,} < {minSize:,}")
                        continue

                    currentSize += os.path.getsize(filePath)
                    if (currentSize > maxSize):
                        toDelete.append(filePath)
                        print(f"Max file size reached, deleting {Fore.BLUE}{file}{Fore.RESET}. {currentSize:,} > {maxSize:,}")
                        continue

                    modifiedTime = os.path.getmtime(filePath)
                    secondsSinceLastModify = time.time() - modifiedTime
                    if (secondsSinceLastModify > timeWindow):
                        toDelete.append(filePath)
                        print(f"File older than {timeWindow}, deleting {Fore.BLUE}{file}{Fore.RESET}. {int(secondsSinceLastModify):,} > {timeWindow:,}")
                        continue

                for item in toDelete:
                    if moveToTrashbin:
                        send_to_recycle_bin(item)
                    else:
                        os.remove(item)
                
                print("")
                print(f"Removed {len(toDelete)} files.")
                print("")

if keepConsoleOpen:
    print("Press enter to exit...")
    input()
