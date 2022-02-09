// ---------------------- // Communicate with Backend // ---------------------- //

// Make a get request
function getFromBackend (endPoint, funcToCall, elem) {
    // funcToCall: the function to call after the data has been fetched
    // elem: the target element. Right now this has been written for addCard which requires a target element to insert the new card into. 
    // This probably won't scale for everything.
    // But it needs to be here for now because if you don't call addCard after you get the data then it'll run BEFORE the data arrives.
    fetch(endPoint)
        .then(response => response.json())
        .then(data => {
            // console.log(data);
            funcToCall(elem, data)
        })
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
        // .then(res => res.json())
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
    animation: 150,
    easing: "cubic-bezier(1, 0, 0, 1)",
    ghostClass: 'blue-background-class',
    onEnd: function(evt) {
        // Get the list ID from where the card was dragged to where the card was dropped
        let from = evt.from.closest('.id').getAttribute('id');
        let to = evt.to.closest('.id').getAttribute('id');
        // Create array from the old index and the new index along with the lists it was dragged and dropped from
        let changeIndex = [from, evt.oldIndex, to, evt.newIndex];
        console.log(changeIndex);
        sendToBackend('/app/c/update', 'POST', changeIndex);
    }
    });
};

// activate drag and drop for lists
var listRow = document.getElementById("list_row")
new Sortable(listRow, {
    handle: '.list_sort_handle',
    animation: 150,
    easing: "cubic-bezier(1, 0, 0, 1)",
    ghostClass: 'blue-background-class',
    onEnd: function(evt) {
        // grabs the old index and the new index to pass to backend to make change persistent
        let changeIndex = [evt.oldIndex, evt.newIndex]
        sendToBackend('/app/l/update', 'POST', changeIndex);
    }
});

// Event Listeners
function enableListeners() {
    // Listens for clicks to edit list headers
    $("h2.list_header").on('click', function() {
        editContent(this, '/app/l/rename', 'POST', 'list name');
    });

    // Listens for clicks to edit card content
    $(".edit_handle").on('click', function() {
        // Goes up one level in the DOM tree and finds the card content container
        let cardContentContainer = $(this).parent().find('.card_content');
        // gets the card ID
        let cardId = cardContentContainer.closest('.id').attr('id');

        // fetches the un-markdown-ed text as stored
        const request = new Request('/app/c/edit', {
            method: 'POST',
            body: JSON.stringify(cardId),
            headers: new Headers({
                'Content-Type': 'application/json'
            })
        });
    
        fetch(request)
            .then(res => res.json())
            .then(res => {
                // save the current text in case we want to cancel
                let beforeEditContent = cardContentContainer.html();
                // replace newlines with line breaks. Without this text is jammed into the edit window with no line breaks at all.
                let result = res.replace(/\n/g, "<br>");
                // replace current text with markdown in edit window
                cardContentContainer.html(result);
                // Stops listening to clicks when editing
                if (cardContentContainer.attr('contentEditable') == 'false') {
                    // create the array to be sent to the backend
                    const changedData = [cardId, 'Card Content'];
                    // Changes to contentEditable mode
                    cardContentContainer.attr('contentEditable', 'true');
                    cardContentContainer.focus();
                    // Listens for enter key, if pressed exits edit mode
                    cardContentContainer.on('keydown', function(e) {
                        if (e.key == "Enter" && e.ctrlKey) {
                            cardContentContainer.attr('contentEditable', 'false');
                            // adds new text content to changedData array
                            changedData.push($(this).prop('innerText'));
                            // sends to the backend
                            const request = new Request('/app/c/edit', {
                                method: 'PUT',
                                body: JSON.stringify(changedData),
                                headers: new Headers({
                                    'Content-Type': 'application/json'
                                })
                            })
                        
                            fetch(request)
                                .then(res => res.json())
                                .then(res => {
                                    // replaces markdown code with processed markdown html
                                    cardContentContainer.html(res);
                                    // turns off listeners, otherwise multiple listeners are active at once
                                    cardContentContainer.off();
                                });
                        }
                    })
                    // Cancel function
                    cardContentContainer.on('keydown', function(e) {
                        if (e.key == "Escape") {
                            cardContentContainer.html(beforeEditContent);
                            cardContentContainer.attr('contentEditable', 'false');
                            // turns off listeners, otherwise multiple listeners are active at once
                            cardContentContainer.off();
                        }
                    })
                    
                }
            })
        
    });

    // Add new card
    $('.card_new').on('click', function() {
        let targetElem = $(this).closest('.id').find('.list_content');
        // fetches the new id. Passes in the name of the function to call, then the target element that function requires
        getFromBackend('/app/c/new', addNewCard, targetElem)
    });
    
    // Change List Width
    // Todo: add persistence 
    $(".list_width").on('click', function() {
        console.log(this);
        if ($(this).hasClass('rotate')) {
            $(this).closest('.list_wrapper').addClass('wide_wrapper');
            $(this).removeClass('rotate');
        } else {
            $(this).closest('.list_wrapper').removeClass('wide_wrapper');
            $(this).addClass('rotate');    
        }
    });

    // Delete (currently only removes from UI, does not delete from backend)
    $('.remove').on('click', function() {
        let objToDel = $(this).closest('.id');
        let objToDelID = objToDel.attr('id');
        alert(`Are you sure you want to delete the list ${objToDel.find('.list_header').text()}?`);
        sendToBackend('/remove', 'DELETE', objToDelID);
        objToDel.remove();    
    });
};


function removeListeners() {
    // removes all listeners so listeners can be re-enabled when something new is added to the DOM
    $(document).add('*').off()
}

// Turns on contentEditable, makes API call to save changed data
function editContent(editObj, endPoint, method, objType) {
    // Stops listening to clicks when editing
    if ($(editObj).attr('contentEditable') == 'false') {
        // create the array to be sent to the backend
        const changedData = [$(editObj).closest('.id').attr('id'), objType];
        // Changes to contentEditable mode
        $(editObj).attr('contentEditable', 'true');
        $(editObj).focus();
        // Listens for enter key, if pressed exits edit mode
        $(editObj).keydown(function(e) {
            if (e.key == "Enter" && e.ctrlKey) {
                $(editObj).attr('contentEditable', 'false');
                // adds new text content to changedData array
                changedData.push($(this).prop('innerText'));
                // sends to the backend
                sendToBackend(endPoint, method, changedData);
            }
        })
        $(editObj).keydown(function(e) {
            if (e.key == "Escape") {
                $(editObj).attr('contentEditable', 'false');
            }
        })
    }
};


// Make new card
function addNewCard(listObj, data) {
    let cardId = data;
    let newCard = `
    <div id="${cardId}" class="card id">
    <div class="card_sort_handle"><span class="material-icons">drag_handle</span></div>
    <div class="row">
        <div class="edit_handle">
            <span class="material-icons">edit</span>
        </div>
        <div contentEditable="false" class="card_content content_main col-9">
        </div>
        <div class="content_side col-3">
        <ul class="metadata">
            <li>${cardId}</li>
            <li>Show Parent</li>
            <li>Related Cards</li>
            <li>Share Link</li>
        </ul>
        </div>
    </div>  
    </div>
    `
    $(listObj).append(newCard);
    removeListeners();
    enableListeners();
    let newCardObj = $(`#${cardId}`).find('.card_content');
    let parentListId = newCardObj.closest('.list_wrapper').attr('id');
    console.log(newCardObj);
    console.log(parentListId);
    // editContent(newCardObj, '/app/c/new', 'POST', 'new card');
    
    // Stops listening to clicks when editing
    if (newCardObj.attr('contentEditable') == 'false') {
        // create the array to be sent to the backend
        const changedData = [newCardObj.closest('.id').attr('id'), 'new card', parentListId];
        // Changes to contentEditable mode
        newCardObj.attr('contentEditable', 'true');
        newCardObj.focus();
        // Listens for enter key, if pressed exits edit mode
        newCardObj.keydown(function(e) {
            if (e.key == "Enter" && e.ctrlKey) {
                newCardObj.attr('contentEditable', 'false');
                // adds new text content to changedData array
                changedData.push($(this).prop('innerText'));
                // sends to the backend
                // sendToBackend('/app/c/new', 'POST', changedData);

                const request = new Request('/app/c/new', {
                    method: 'POST',
                    body: JSON.stringify(changedData),
                    headers: new Headers({
                        'Content-Type': 'application/json'
                    })
                })
            
                fetch(request)
                    .then(res => res.json())
                    .then(res => {
                        // replaces markdown code with processed markdown html
                        newCardObj.html(res);
                    });
            }
        })
        newCardObj.keydown(function(e) {
            if (e.key == "Escape") {
                newCardObj.attr('contentEditable', 'false');
            }
        })
    }
};

function addNewList() {

    fetch('/app/c/new')
        .then(response => response.json())
        .then(newListID => {
            
            let newList = `
            <div id="${newListID}" class="list_wrapper smooth id align-self-start ms-2 p-0">
            <div class="list_sort_handle z-ind-0">  <!-- Sortables target handle -->
            <span class="material-icons drag_handle">drag_handle</span>
        
                <div class="list_header_wrapper smooth row justify-content-between z-ind-2">
                    <div class="col-10">
                        <h2 contentEditable="false" class="list_header"></h2>
                    </div>
                    <div class="col-2 z-ind-3 text-end">
                        <span class="material-icons mt-2 remove">close</span>
                    </div>
                </div>
                </div>  <!-- Sortables target handle end -->
            
            <!-- List content: contains individual cards -->
            <div class="list_content">
            </div> <!-- List content end -->
        
            <!--  List tool bar: appends the new card after the last child of the list content div-->
            <div class="list_tools row justify-content-between m-2 mt-1">
                <p class="col-2 material-icons card_new">add</p>
                <!-- <p class="col-2 material-icons text-center list_width">west</p> -->
            </div><!-- list tool bar end -->
        
            </div>
            <!-- individual list end -->
            `

            // Insert into page
            $('#list_row').prepend(newList);

            removeListeners();
            enableListeners();

            // Edit list name
            let newListObj = $(`#${newListID} h2.list_header`);
            editContent(newListObj, '/app/l/new', 'POST', 'new list');
        })


}




// ---------------------- // Start // ---------------------- //
// Because everything is loaded programically we need to set a delay otherwise this runs before there is anything on screen
setTimeout(function(){
    enableListeners();
}, 1000)
