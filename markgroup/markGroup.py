from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
from datetime import datetime

import asyncio, re, json

from colorama import init, Fore
init(True)

json_ = {
    "$schema": "https://raw.githubusercontent.com/PazerOP/tf2_bot_detector/master/schemas/v3/playerlist.schema.json",
	"file_info": {
		"authors": [
            "teltta"
		],
		"description": "None",
		"title": "None"
	},
    "players": []
}

def printTimestamp(text:str):
    print(f"{Fore.GREEN}{datetime.now().strftime('%H:%M:%S')}{Fore.RESET} | {text}")

steamID64Offset = 76561197960265728
def steamId64To32(id: int):
    return f"[U:1:{id-steamID64Offset}]"

def findFirst(__iterable: list|tuple, /, *, key):
    if isinstance(key, (type)):
        for item in __iterable:
            if isinstance(item, key):
                return item
    else:
        for item in __iterable:
            try:
                if key(item):
                    return item
            except:continue
    return None

ids = []
async def main():
    url = input("Group url: ")

    matches = re.match(r"https://steamcommunity\.com/groups/[a-zA-Z0-9-_]+", url)
    if not matches:
        return
    
    match = matches.group(0)
    urlPN = f"{match}/members/?p="
    pageNum = 1

    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument('--disable-gpu')

    printTimestamp("Initiating driver.\n")
    driver = webdriver.Firefox(options=options)

    while True:
        printTimestamp("Fetching url.\n")
        driver.get(f"{urlPN}{pageNum}")
        html = driver.page_source

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "grouppage_header_name")))
        await asyncio.sleep(1)

        printTimestamp("Parsing HTML.\n")
        soup = BeautifulSoup(html.encode("ascii", "replace"), "html.parser")

        groupname = soup.find("div", attrs={"class": "grouppage_header_name"}).get_text(strip=True)
        json_["file_info"]["description"] = f"Cheater/bot group - {groupname}"
        json_["file_info"]["title"] = f"Cheater/bot group - {groupname}"

        members = list(soup.find_all("div", attrs={"class": re.compile("^member_block")}))

        printTimestamp("Members:")
        for member in members:
            memberUrl = str(member.find_next("a", attrs={"class": "linkFriend"})["href"])
            memberID64 = "-"
            
            if not re.match(r"https://steamcommunity\.com/profiles/[0-9]{15,}", memberUrl):
                driver.get(memberUrl)

                await asyncio.sleep(1)
                html = driver.page_source

                pDataTemp = re.findall(r"g_rgProfileData = {[\d\D]+};", html)
                if not pDataTemp:
                    continue
                
                profileData = json.loads(str(pDataTemp[0]).replace("g_rgProfileData","").strip(" =").rstrip(";"))
                memberID64 = profileData.get("steamid", "-")
            else:
                memberID64 = memberUrl.rstrip("\\/").rsplit("/",1)[1]

            if memberID64 in ids:
                continue

            if not memberID64.isdigit():
                continue

            data = {
                "attributes": [
                    "suspicious"
                ],
                "proof": f"Part of cheater/bot group - {groupname}",
                "steamid": steamId64To32(int(memberID64))
            }

            json_["players"].append(data)

            ids.append(memberID64)
            print(memberID64)

        pagination = soup.find("div", attrs={"class": "pageLinks"})
        buttons = list(pagination.find_all(attrs={"class": "pagebtn"}))
        nextButton = findFirst(buttons, key=lambda x: x.get_text() == ">")
        if not nextButton:
            break
        if "disabled" in nextButton["class"]:
            break

        pageNum += 1
        print()

    temp = re.sub(r'\s+', '_', re.sub(r'[^a-zA-Z0-9 ]+', '', groupname))
    filename = f"playerlist.{temp}.json"

    print()
    printTimestamp(f"Writing to {filename}\n")

    with open(filename, "wt") as file:
        if file.writable():
            file.write(json.dumps(json_, indent=4))
        
    printTimestamp("Done.\n")
        

if __name__ == "__main__":
    asyncio.run(main())
    input("Press Enter to continue...")