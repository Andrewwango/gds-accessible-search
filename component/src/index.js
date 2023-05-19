function searchButtonPressed() {

    let inputElement = document.getElementById("user-query")
    let outputElement = document.getElementById("search-result")
    outputElement.innerHTML = handleSearch(inputElement.value)
}

function handleSearch(query) {
    let documentText = scrapeCurrentPage()
    let prompt = constructPrompt(documentText, query)
    let response = callBackend(prompt) //may need to be asynchronous

    return response
}

function scrapeCurrentPage() {
    // Scrape
    // Parse
    return ""
}

function constructPrompt(context, query) {
    return query
}

function callBackend(prompt) {
    return "Your query was: " + prompt
}