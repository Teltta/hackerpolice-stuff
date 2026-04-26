import re, json, os

kills:  dict[str, dict[str, int]] = {}
deaths: dict[str, int] = {}

playerLastDeath: dict[str, int] = {}
playerIsSpyDict: dict[str, bool] = {}

lastKiller:dict[str, list[str, str]] = {}

killsPerPlayer: dict[str, dict[str, dict[str ,int]]] = {}

maxTicksBetweenDeaths = 666 # 10 seconds / prevents dead ringer deaths from showing up

def inputConfirm(text: str = "Confirm [y\\N] ", default_value: str = "n") -> bool:
    return ((input(text).strip().lower() or default_value) in ["y","1","true","yes"])

inFile = input("Input file: ")
accountDeadRinger = inputConfirm("Account for dead ringer deaths? [Y\\n]", "y")

if os.path.isabs(inFile):
    path = inFile
else:
    path = os.path.join(os.getcwd(), inFile)

def ticksSinceLastDeath(tick, player):
    last = playerLastDeath.get(player)
    if last is None:
        return None
    return abs(tick - last)

def removeRecentDeath(player):
    t = lastKiller.get(player)
    if t is None:
        return

    prev_killer, prev_weapon = t

    if kills.get(prev_killer, {}).get(prev_weapon) is not None:
        kills[prev_killer][prev_weapon] = max(kills[prev_killer][prev_weapon]-1, 0)
        deaths[player] = max(deaths[player]-1, 0)
        killsPerPlayer[prev_killer][player][prev_weapon] = max(killsPerPlayer[prev_killer][player][prev_weapon]-1, 0)

def playerIsSpy(player):
    return playerIsSpyDict[player] in [True, None]

def calculateDeadRinger(tick, killed, killer, weapon):
    tick = int(tick)

    lastDeathKilled = ticksSinceLastDeath(tick, killed)
    lastDeathKiller = ticksSinceLastDeath(tick, killer)

    if lastDeathKilled is not None and lastDeathKilled < maxTicksBetweenDeaths:
        if playerIsSpy(killed):
            removeRecentDeath(killed)

    if lastDeathKiller is not None and lastDeathKiller < maxTicksBetweenDeaths:
        if playerIsSpy(killer):
            removeRecentDeath(killer)

ENCODING = "utf-8"
with open(path, "rt", encoding=ENCODING) as file:
    lines = file.readlines()

spyWeapons = [
    "knife",
    "eternal_reward",
    "kunai",
    "big_earner",
    "spy_cicle",

    "revolver",
    "ambassador",
    "big_kill",
    "letranger",
    "enforcer",
    "diamondback"
]

for line in lines:
    match = re.search(r"\"([\d\D]+)\" was killed by \"([\d\D]+)\" using", line)
    if match:
        killed, killer = match.groups()
        playerIsSpyDict[killer] = None
        playerIsSpyDict[killed] = None

weaponMapping = {
    "player": "fall_damage?"
}

for line in lines:
    match = re.match(r"([0-9]+): \"([\d\D]+)\" was killed by \"([\d\D]+)\" using ([a-z \_\(\)\-]+)", line) # differentiates crit kills
    # match = re.match(r"([0-9]+): \"([\d\D]+)\" was killed by \"([\d\D]+)\" using ([a-z\_]+)", line)
    if match:
        tick, killed, killer, weapon = match.groups()
        tick = int(tick)

        if killer == "world" and weapon in ("worldspawn","world"):
            killer = killed
            weapon = "suicide"

        weapon = weaponMapping.get(weapon, weapon)

        wp = weapon.rsplit(" ",1)
        isSpy = playerIsSpyDict.get(killer, None)
        hasSpyWep = wp[0] in spyWeapons
        if isSpy is None and not hasSpyWep:
            playerIsSpyDict[killer] = False
        elif hasSpyWep:
            playerIsSpyDict[killer] = True

        deaths.setdefault(killed, 0)

        killsPerPlayer.setdefault(killer, {})
        killsPerPlayer[killer].setdefault(killed, {})
        killsPerPlayer[killer][killed].setdefault(weapon, 0)

        if accountDeadRinger:
            calculateDeadRinger(*match.groups())
        
        playerLastDeath[killed] = tick

        deaths[killed] += 1
        killsPerPlayer[killer][killed][weapon] += 1
        if weapon != "suicide":

            kills.setdefault(killer, {})
            kills[killer].setdefault(weapon, 0)
            kills[killer][weapon] += 1

        lastKiller[killed] = [killer, weapon]

output = {
    "kills": kills,
    "deaths": deaths,
    "perPlayer": killsPerPlayer
}
with open("parseKillsOutput.json", "wt", encoding=ENCODING) as file2:
    json.dump(output, file2, indent=4, ensure_ascii=False)
print("Done...")
# input("Press [Enter] to exit...")