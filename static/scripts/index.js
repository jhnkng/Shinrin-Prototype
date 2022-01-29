// ---------------------- // Communicate with Backend // ---------------------- //

// Make a get request
function getFromBackend (endPoint, functionToRun) {
    fetch(endPoint)
        .then(response => response.json())
        .then(data => {functionToRun(data)})
}

// Send data to backend
function sendToBackend(endPoint, method, dataToSend) {
    const request = new Request(endPoint, {
        method: method,
        body: JSON.stringify(dataToSend),
        headers: new Headers({
            'Content-Type': 'application/json'
        })
    })

    fetch(request)
        .then(res => res.json())
        // .then(res => console.log(res));
};


// ---------------------- // App Logic // ---------------------- //

// Enable Sortables for Cards
var sortables = document.querySelectorAll(".list_content");
for (var i = 0; i < sortables.length; i++) {
    var sortable = sortables[i];
    new Sortable(sortable, {
    handle: '.card_sort_handle',
    group: 'shared',
    animation: 50,
    ghostClass: 'blue-background-class',
    onEnd: function(evt) {
        console.log(evt);
        // sendToBackend('/receive', 'POST', getCurrentListLocation());
    }
    });
};

// activate drag and drop for lists
var listRow = document.getElementById("list_row")
new Sortable(listRow, {
    handle: '.list_sort_handle',
    animation: 50,
    ghostClass: 'blue-background-class'
});



// Event Listeners
function enableListeners() {
    // Listens for clicks to edit list headers
    $("h2.list_header").on('click', function() {
        editContent(this, '/app/l/rename', 'list name');
    });

    // Listens for clicks to edit card content
    $(".card_content").on('click', function() {
        editContent(this, '/app/c/edit', 'card content');
    });
};


// Turns on contentEditable, makes API call to save changed data
function editContent(editObj, endPoint, objType) {
    // Stops listening to clicks when editing
    if ($(editObj).attr('contentEditable') == 'false') {
        // create the array to be sent to the backend
        const changedData = [objType, $(editObj).closest('.id').attr('id')];
        // Changes to contentEditable mode
        $(editObj).attr('contentEditable', 'true');
        // Listens for enter key, if pressed exits edit mode
        $(editObj).keydown(function(e) {
            if (e.key == "Enter") {
                $(editObj).attr('contentEditable', 'false');
                // adds new text content to changedData array
                changedData.push($(this).prop('innerText'));
                // sends to the backend
                sendToBackend(endPoint, 'POST', changedData);
            }
        })
    }
};



// ---------------------- // Start // ---------------------- //
// Gets data from backend, sends it to renderPage to render on screen
// getFromBackend('/app', renderPage);

// Because everything is loaded programically we need to set a delay otherwise this runs before there is anything on screen
setTimeout(function(){
    enableListeners();
}, 1000)
