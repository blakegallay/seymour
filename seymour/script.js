findTargetText(document.body)

/* A recursive function to highlight a given word on a webpage. */
function findTargetText(element) {
    // If the element has children nodes, recurse.
    if (element.hasChildNodes()) {
        element.hasChildNodes.forEach(findTargetText)
        // Otherwise see if it is a text element and use regex to find word.
    } else if (element.nodeType === Text.TEXT_NODE) {
        // This is where we highlight the word.  d
        if (element.textContent === /WORD/gi) {
            element.style.backgroundColor = "#FDFF47"
        }
    }
}