chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === "fetchJson") {
        fetch(msg.url).then(res => res.json())
        .then(data => {
            sendResponse({ success: true, data });
        })
        .catch(err => {
            sendResponse({ success: false, error: err.toString() });
        });

        return true;
    } else if (msg.type == "fetchHtml") {
        fetch(msg.url, {
            method: "GET",
            headers: {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Cache-Control": "no-cache"
            }
        }
        ).then(res => res.text())
        .then(data => {
            sendResponse({ success: true, data });
        })
        .catch(err => {
            sendResponse({ success: false, error: err.toString() });
        });
        return true;
    }
});