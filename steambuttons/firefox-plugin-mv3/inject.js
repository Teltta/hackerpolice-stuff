window.postMessage({
    type: "STEAM_ID",
    steamID: window.g_rgProfileData?.steamid ?? null
}, "*");