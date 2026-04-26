// if (!document.href.url.test(/https:\/\/steamcommunity\.com/)) return;
console.info("[SteamButtons] Running steambuttons.")

function id64To32(id64) {
	return `[U:1:${id64 - 76561197960265728n}]`
}

let namesFetched = false;

function nameHistoryCB(steamID) {
    chrome.runtime.sendMessage({
        type: "fetchHtml",
        url: `https://steamhistory.net/history/0/${steamID}`
    }, (response) => {
        if (!response) {
            console.error("[SteamButtons] No response from steamhistory.");
            return;
        }

        if (response.success) {
            const shHTML = new DOMParser().parseFromString(response.data, "text/html");
            // this is for shadefall
            // let aliases = shHTML.querySelectorAll(".name-entry > .name")
            // let aliases = shHTML.querySelectorAll("script")
            
            // const names = document.querySelector("#NamePopupAliases")
            // if (names && aliases) {
            //     aliases.forEach(alias => {
            //         let p = document.createElement("p")
            //         p.textContent = alias.textContent;
            //         names.append(p)
            //     })
            //     namesFetched = true;
            // }
            let script = Array.from(shHTML.querySelectorAll("script")).find(x => x.textContent.includes("kit.start"))
            const match = script.textContent.match(/entries:\s*(\[[\s\S]*?\])\s*,/);
            const names = document.querySelector("#NamePopupAliases")

            if (match && names) {
                const fixed = match[1].replace(/([{,]\s*)(\w+)\s*:/g, '$1"$2":');
                const entries = Array.from(JSON.parse(fixed));

                if (entries) {
                    let i = 0
                    entries.forEach(entry => {
                        if (!Array.from(names.children).find(x => x.textContent == entry.Name)) {
                            let p = document.createElement("p")
                            p.textContent = entry.Name;
                            names.append(p)
                            i++
                        }
                    })
                    console.info(`[SteamButtons] Added ${i} names.`)
                    namesFetched = true;
                }
            }
        } else {
            console.error("[SteamButtons] ERROR:", response.error);
        }
    });
}

function getViaRGProfileData() {
    return new Promise((resolve) => {
        const script = document.createElement("script");
        script.textContent = `
            window.postMessage({
                type: "STEAM_ID",
                steamID: window.g_rgProfileData?.steamid ?? null
            }, "*");
        `;

        const handler = (event) => {
            if (event.source !== window) return;
            if (event.data?.type !== "STEAM_ID") return;

            window.removeEventListener("message", handler);
            resolve(event.data.steamID);
        };
        window.addEventListener("message", handler);

        document.documentElement.appendChild(script);
        script.remove();
    });
}

async function getSteamID()  {
    const input = document.querySelector('input[name="abuseID"]');
    let steamID = input && input.value;

    if (!steamID) {
        console.warn("[SteamButtons] Getting steam ID failed, trying 2nd method.")
        const login = document.querySelector('.global_action_link[href*="/login/"]:not([id])');
        const match = login?.href.match(/(7656\d{13})/);

        steamID = match ? match[1] : null;
    }

    if (!steamID) {
        console.warn("[SteamButtons] Getting steam ID failed, trying 3rd method.")
        steamID = await getViaRGProfileData();
    }

    return steamID
}

async function copyToClipboard(text) {
    const clipboardItem = new ClipboardItem({["text/plain"]: text});
    await navigator.clipboard.write([clipboardItem]);
}

function addCheaterMarks(rightcol, steamID32, url) {
    return new Promise((resolve, reject) => {
        chrome.runtime.sendMessage({
            type: "fetchJson",
            url: url
        }, (response) => {
            if (!response) {
                console.error(`[SteamButtons] No response from ${url}`);
                resolve();
                return;
            }

            if (response.success) {
                const players = response.data.players;

                const match = players.find(player => player.steamid.trim() === steamID32);
                if (match) {
                    const reportType = match.attributes.join(", ")
                    const proof = match.proof[0]
                    const proofHref = proof.includes("discord.com") ? `discord:${proof}` : proof

                    const siteName = url.includes("shadefall.net") ? "Shadefall" : "Hackerpolice"

                    const div = document.createElement("a")
                    Object.assign(div.style, {
                        borderRadius: "8px", background: "#45000099", border: "2px solid #cd4141",
                        width: "fit-content", padding: "6px", color: "#fff", display: "block", marginBottom: "10px"
                    });
                    div.textContent = `Player is marked as ${reportType}`;
                    div.href = proofHref;

                    rightcol.insertBefore(div, rightcol.children[0])

                    let timestamp = match?.last_seen.time
                    const div2 = document.createElement("div")
                    if (timestamp) {
                        let [num, ...text] = relativeTime(timestamp).split(" ")
                        div2.innerHTML = `${siteName}: <strong>${num}</strong> ${text.join(" ")}`
                    } else {
                        div2.innerHTML = siteName
                    }
                    rightcol.insertBefore(div2, rightcol.children[0])
                }
                resolve();
                
            } else {
                console.error("[SteamButtons] ERROR:", response.error);
                resolve();
            }
        });
    });
}

function relativeTime(unixTimestamp) {
    const now = Date.now() / 1000;
    const diff = now - unixTimestamp

    const units = [
        ["year", 31536000],
        ["month", 2592000],
        ["day", 86400],
        ["hour", 3600],
        ["minute", 60],
        ["second", 1]
    ];

    const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

    for (const [unit, seconds] of units) {
        const value = Math.floor(diff / seconds);
        if (value >= 1) {
            return rtf.format(-value, unit);
        }
    }

    return "just now";
}

async function main() {
    const pageUrl = window.location.href;
    let regex = new RegExp("steamcommunity\.com")

    if (regex.test(pageUrl)) {
        
        const steamID = await getSteamID()

        if (steamID) {
            const header = document.querySelector(".profile_header_actions");
            if (header) {
                let a = document.createElement("a")
                a.href = `https://steamhistory.net/id/${steamID}`
                a.classList.add("btn_profile_action", "btn_medium");

                let a2 = document.createElement("span")
                a2.textContent = "SteamHistory";
                a.appendChild(a2)


                let b = document.createElement("a")
                b.href = `https://shadefall.net/archive/${steamID}`
                b.classList.add("btn_profile_action", "btn_medium");

                let b2 = document.createElement("span")
                b2.textContent = "Shadefall";
                b.appendChild(b2)
                

                header.appendChild(a)
                header.appendChild(b)
            } else {
                console.warn("[SteamButtons] Couldnt find profile header. Cant add steamhistory/shadefall buttons.")
            }

            const nameHistory = document.querySelector(".namehistory_link");
            if (nameHistory) {
                nameHistory.addEventListener("click", _ => {
                    if (namesFetched) return;
                    console.info("[SteamButtons] Adding names")
                    setTimeout(() => nameHistoryCB(steamID), 300);
                },)
            } else {
                console.warn("[SteamButtons] Couldnt find namehistory element. Cant add past names.")
            }

            const userName = document.querySelector(".persona_name")
            if (userName) {
                let personaStyle = document.createElement("style")
                personaStyle.textContent = ".persona_id:hover {color: #d2d2d2 !important;}"
                document.head.appendChild(personaStyle)

                userName.style.overflow = "visible"

                let personaId = document.createElement("div")
                personaId.className = "persona_id"
                personaId.textContent = `(${steamID})`

                personaId.style.fontSize = "14px"
                personaId.style.color = "#8b8b8b"
                personaId.style.width = "fit-content"
                personaId.style.position = "relative"
                personaId.style.cursor = "pointer"
                personaId.setAttribute("clicked", false)


                let popupVisual = document.createElement("div")
                popupVisual.className = "popup_visual"
                popupVisual.textContent = "-"

                Object.assign(popupVisual.style, {
                    "fontSize" : "14px","opacity" : "0","transition" : "opacity 200ms ease-in-out","color" : "#e2e2e2",
                    "display" : "none","position" : "absolute","top" : "50%","left" : "50%","transform" : "translate(-50%, -50%)",
                    "background" : "#1e1e1e99","padding" : "0 10px 0 10px","border" : "2px solid #fff","borderRadius" : "8px"
                })

                function popupVisualRun(text) {
                    if (personaId.getAttribute("clicked") == "true") return

                    personaId.setAttribute("clicked", true)
                    popupVisual.textContent = text
                    popupVisual.style.display = "block"
                    popupVisual.style.opacity = "1"
                    
                    setTimeout(() => {
                        popupVisual.style.opacity = "0"
                        setTimeout(() => {
                            popupVisual.style.display = "none"
                            personaId.setAttribute("clicked", false)
                        }, 200);
                    }, 1000);
                }

                personaId.addEventListener("contextmenu", (event) => {
                    event.preventDefault()
                    copyToClipboard(`https://steamcommunity.com/profiles/${steamID}`)
                    popupVisual.textContent = "Copied Profile URL"
                    popupVisualRun("Copied Profile URL")
                })
                personaId.addEventListener("click", (event) => {
                    event.preventDefault()
                    copyToClipboard(`${steamID}`)
                    popupVisual.textContent = "Copied User ID"
                    popupVisualRun("Copied User ID")
                })


                personaId.appendChild(popupVisual)
                userName.appendChild(personaId)
            }

        
            const rightcol = document.querySelector(".profile_rightcol")
            if (rightcol) {
                const steamID32 = id64To32(BigInt(steamID)).toString().trim()
                await addCheaterMarks(rightcol, steamID32, "https://raw.githubusercontent.com/Nocrex/Tom/main/playerlist.vorobey-hackerpolice.json");
                await addCheaterMarks(rightcol, steamID32, "https://shadefall.net/api/lists/cheaters.json");
                
            } else {
                console.warn("[SteamButtons] Couldnt find profile right column. Cant check for cheater detection.")
            }
	    } else {
            console.error("[SteamButtons] Couldnt find user id.")
        }
    }
}

//if ( document.readyState === "loading" ) { // this gets triggered slower than the one below but achieves the same thing 
// (idk why (edit: i think document elements can be loaded but readyState will still be "loading" so it triggers the if clause even though we can already append to the document tree))
if ( !(document.head || document.body || document.documentElement) ) {
    window.addEventListener("DOMContentLoaded", main, { once:true })
} else {
    main()
}