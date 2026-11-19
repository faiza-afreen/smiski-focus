
async function notifyDesktop() {
    try {
        await fetch("http://127.0.0.1:5000/distraction", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                website: "Instagram",
                timestamp: new Date().toISOString()
            }),
            signal: AbortSignal.timeout(2000)
        });
    } catch (error) {
        console.log("Desktop Smiski is not running.");
    }
}

chrome.runtime.onMessage.addListener((message, sender) => {

    if (message.type === "closeInstagram" &&
        sender.tab?.id != null) {

        const id = sender.tab.id;

        chrome.storage.local.get(
            { enabled: true },
            async ({ enabled }) => {

                if (!enabled) return;

                try {
                    const tab = await chrome.tabs.get(id);

                    const hostname = new URL(tab.url).hostname;

                    if (/(^|\.)instagram\.com$/.test(hostname)) {

                        await chrome.tabs.remove(id);

                        await notifyDesktop();
                    }

                } catch (error) {
                    console.log(error);
                }
            }
        );
    }
});
