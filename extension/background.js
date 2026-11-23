// The service worker only opens the analysis page. All analysis runs in the page and its Web Worker, so a service-
// worker shutdown cannot interrupt an analysis. Pre-download interception is NOT implemented (not demonstrated).
chrome.action.onClicked.addListener(() => chrome.tabs.create({ url: chrome.runtime.getURL('app.html') }));
