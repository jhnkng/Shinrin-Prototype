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

function enableSortable() {
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
            sendToBackend('/app/l/update', 'PUT', changeIndex);
        }
    });
};


// ---------------------- // Event Listeners // ---------------------- //
 
function enableListeners() {

    // Listens for clicks to edit list headers
    $("h2.list_header").on('click', function() {
        
        if ($(this).attr('contentEditable') == 'false') {
            // Stops listening to clicks when editing
            $(this).off();
            // create the array to be sent to the backend
            const changedData = [$(this).closest('.id').attr('id'), 'rename list'];
            // Changes to contentEditable mode
            $(this).attr('contentEditable', 'true');
            $(this).focus();

            // Listens for paste event, replaces formatted text with plain text
            $(this).on("paste",function(event){
                event.preventDefault();
                // console.log(window.event.clipboardData);
                let clipboarddata =  window.event.clipboardData.getData('text/plain');    
                // console.log("paste value" + clipboarddata);
                $(this).text(clipboarddata);
            });

            // Listens for enter key, if pressed exits edit mode and saves data
            $(this).on('keydown', function(e) {
                if (e.key == "Enter") {
                    e.preventDefault();
                    $(this).attr('contentEditable', 'false');
                    // adds new text content to changedData array
                    changedData.push($(this).prop('innerText'));
                    // sends to the backend
                    const request = new Request('/app/l/rename', {
                        method: 'PUT',
                        body: JSON.stringify(changedData),
                        headers: new Headers({
                            'Content-Type': 'application/json'
                        })
                    })
                
                    fetch(request);

                    // Reenables the listeners
                    removeListeners();
                    enableListeners();
                }
            })
            $(this).on('keydown', function(e) {
                if (e.key == "Escape") {
                    $(this).attr('contentEditable', 'false');
                    // Reenables the listeners
                    removeListeners();
                    enableListeners();
                }
            })
        }
    });

    // Listens for clicks to edit card content
    $(".edit_handle").on('click', function() {
        console.log('clicked');
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
                        if (e.key == "s" && e.ctrlKey) {
                            e.preventDefault();
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
                                    // reset listeners
                                    removeListeners();
                                    enableListeners();
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
                            // reset listeners
                            removeListeners();
                            enableListeners();
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
    

    // Delete list
    $('.remove').on('click', function() {
        let listToDel = $(this).closest('.id');
        let listToDelID = listToDel.attr('id');
        alert(`Are you sure you want to delete the list ${listToDel.find('.list_header').text()}?`);
        sendToBackend('/app/l/trash', 'DELETE', listToDelID);
        listToDel.remove();    
    });

    // Minimise list
    $('.minimise').on('click', function() {
        let listToMinimise = $(this).closest('.id');
        let listToMinimiseID = listToMinimise.attr('id');
        let listToMinimiseText = listToMinimise.find('h2.list_header').text();
        sendToBackend('/app/l/minimise', 'PUT', listToMinimiseID);
        listToMinimise.remove();
        $('#minimised_lists').append(`<li class='ps-3 ${listToMinimiseID}' onclick='restoreMinimisedList("${listToMinimiseID}")'>${listToMinimiseText}</li>`);
    });

    // Change List Width
    // Todo: add persistence 
    // $(".list_width").on('click', function() {
    //     console.log(this);
    //     if ($(this).hasClass('rotate')) {
    //         $(this).closest('.list_wrapper').addClass('wide_wrapper');
    //         $(this).removeClass('rotate');
    //     } else {
    //         $(this).closest('.list_wrapper').removeClass('wide_wrapper');
    //         $(this).addClass('rotate');    
    //     }
    // });

    $('.card_content').on('click', function() {
        if ($(this).attr('contentEditable') == 'false') {
            id = $(this).closest('.id').attr('id');
            showFullscreen(id);    
        };
    });

    console.log('listeners enabled');
};


function removeListeners() {
    // removes all listeners so listeners can be re-enabled when something new is added to the DOM
    $(document).add('*').off()
    console.log('listeners removed');
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

        // Listens for paste event, replaces formatted text with plain text
        $(editObj).on("paste",function(event){
            event.preventDefault();
            let clipboarddata =  window.event.clipboardData.getData('text/plain');    
            $(editObj).text(clipboarddata);
        });

        // Listens for enter key, if pressed exits edit mode
        $(editObj).on('keydown', function(e) {
            if (e.key == "Enter") {
                $(editObj).attr('contentEditable', 'false');
                // adds new text content to changedData array
                changedData.push($(this).prop('innerText'));
                // sends to the backend
                sendToBackend(endPoint, method, changedData);
            }
        })
        $(editObj).on('keydown', function(e) {
            if (e.key == "Escape") {
                $(editObj).attr('contentEditable', 'false');
            }
        })
    }
};


// Make new card
function addNewCard(listObj, cardId) {
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
    
    // Insert card
    $(listObj).append(newCard);

    // edit card content
    let newCardObj = $(`#${cardId}`).find('.card_content');
    let parentListId = newCardObj.closest('.list_wrapper').attr('id');
    
    // Stops listening to clicks when editing
    if (newCardObj.attr('contentEditable') == 'false') {
        // create the array to be sent to the backend
        const changedData = [newCardObj.closest('.id').attr('id'), 'new card', parentListId];
        // Changes to contentEditable mode
        newCardObj.attr('contentEditable', 'true');
        newCardObj.focus();

        // Listens for paste event, replaces formatted text with plain text
        newCardObj.on("paste",function(event){
            event.preventDefault();
            // console.log(window.event.clipboardData);
            let clipboarddata =  window.event.clipboardData.getData('text/plain');    
            // console.log("paste value" + clipboarddata);
            newCardObj.text(clipboarddata);
        });

        // Listens for enter key, if pressed exits edit mode
        newCardObj.on('keydown', function(e) {
            if (e.key == "s" && e.ctrlKey) {
                e.preventDefault();
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
                        newCardObj.off();
                        // reset listeners
                        removeListeners();
                        enableListeners();

                    });
            }
        })
        newCardObj.on('keydown', function(e) {
            if (e.key == "Escape") {
                // newCardObj.attr('contentEditable', 'false');
                $(`#${cardId}`).remove();
                newCardObj.off();
                // reset listeners
                removeListeners();
                enableListeners();
            }
        })
    }
};

// add new list
function addNewList() {

    fetch('/app/l/new')
        .then(response => response.json())
        .then(newListID => {
            
            let newList = `
            <div id="${newListID}" class="list_wrapper smooth id align-self-start ms-2 p-0">
            <div class="list_sort_handle z-ind-0">
            <span class="material-icons drag_handle">drag_handle</span>
        
                <div class="list_header_wrapper smooth row justify-content-between z-ind-2">
                    <div class="col-9">
                        <h2 contentEditable="false" class="list_header"></h2>
                    </div>
                    <div class="col-3 z-ind-3 text-end">
                    <span class="material-icons minimise" style="position: relative; top: -2px; left: 4px;">minimize</span>
                    <span class="material-icons mt-2 remove">close</span>    
                    </div>
                </div>
                </div>
            
            <div class="list_content"><!-- Cards go here --></div>
        
            <div class="list_tools row justify-content-between m-2 mt-1">
                <p class="col-2 material-icons card_new">add</p>
                <!-- <p class="col-2 material-icons text-center list_width">west</p> -->
            </div>        
            </div>
            `

            // Insert into page
            $('#list_row').prepend(newList);

            // reset listeners
            removeListeners();
            enableListeners();

            // Edit list name
            let newListObj = $(`#${newListID} h2.list_header`);            
            // Stops listening to clicks when editing
            if (newListObj.attr('contentEditable') == 'false') {
                // create the array to be sent to the backend
                const changedData = [newListID, 'new list'];
                // Changes to contentEditable mode
                newListObj.attr('contentEditable', 'true');
                newListObj.focus();

                // Listens for paste event, replaces formatted text with plain text
                newListObj.on("paste",function(event){
                    event.preventDefault();
                    // console.log(window.event.clipboardData);
                    let clipboarddata =  window.event.clipboardData.getData('text/plain');    
                    // console.log("paste value" + clipboarddata);
                    newListObj.text(clipboarddata);
                });

                // Listens for enter key, if pressed exits edit mode and saves data
                newListObj.on('keydown', function(e) {
                    if (e.key == "Enter") {
                        e.preventDefault();
                        newListObj.attr('contentEditable', 'false');
                        // adds new text content to changedData array
                        changedData.push($(this).prop('innerText'));
                        // sends to the backend
                        const request = new Request('/app/l/new', {
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
                                newListObj.html(res);
                                newListObj.off();
                            });
                    }
                })
                newListObj.on('keydown', function(e) {
                    if (e.key == "Escape") {
                        $(`#${newListID}`).remove();
                        newListObj.off();
                    }
                })
            }
        })
}

// restore minimised list
function restoreMinimisedList(listID) {
    let endPoint = '/app/l/minimise';
    let method = 'POST';
    let dataToSend = listID;
    console.log(`Unminimising List ${listID}`)

    const request = new Request(endPoint, {
        method: method,
        body: JSON.stringify(dataToSend),
        headers: new Headers({
            'Content-Type': 'application/json'
        })
    })

    fetch(request)
        .then(response => response.json())
        .then(data => {
            // console.log(data);
            let listID = data.list_id;
            // console.log(listID);
            let listName = data.list_name;
            // console.log(listName);
            let list = `
            <div id="${listID}" class="list_wrapper smooth id align-self-start ms-2 p-0">
            <div class="list_sort_handle z-ind-0">
            <span class="material-icons drag_handle">drag_handle</span>
        
                <div class="list_header_wrapper smooth row justify-content-between z-ind-2">
                    <div class="col-9">
                        <h2 contentEditable="false" class="list_header">${listName}</h2>
                    </div>
                    <div class="col-3 z-ind-3 text-end">
                    <span class="material-icons minimise" style="position: relative; top: -2px; left: 4px;">minimize</span>
                    <span class="material-icons mt-2 remove">close</span>    
                    </div>
                </div>
                </div>
            
            <div class="list_content"><!-- Cards go here --></div>
        
            <div class="list_tools row justify-content-between m-2 mt-1">
                <p class="col-2 material-icons card_new">add</p>
                <!-- <p class="col-2 material-icons text-center list_width">west</p> -->
            </div>        
            </div>
            `
            $('#list_row').prepend(list);

            for (let i = 0; i < data.cards.length; i++) {
                cardId = data.cards[i].card_id;
                card_body = data.cards[i].card_body;
                let newCard = `
                <div id="${cardId}" class="card id">
                <div class="card_sort_handle"><span class="material-icons">drag_handle</span></div>
                <div class="row">
                    <div class="edit_handle">
                        <span class="material-icons">edit</span>
                    </div>
                    <div contentEditable="false" class="card_content content_main col-9">
                    ${card_body}
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
                $(`#${listID} .list_content`).append(newCard);
            };

            // reset listeners
            removeListeners();
            enableListeners();

            // Re-enable sortable
            enableSortable();

            // Remove the link from minimised lists list
            $(`#minimised_lists .${listID}`).remove();
        })
};

// Show full screen card
function showFullscreen(cardID) {
    $('body').addClass('freeze_scroll');
    request = `/app/c/${cardID}`
    fetch(request)
        .then(response => response.json())
        .then(response => {
            let cardContent = response[0];
            let cardMetadata = response[1];
            let cardChildren = response[2];
            console.log(cardChildren);
            let fsContainer = `
            <div id="fullscreen" class="fs_wrapper container-fluid m-0 p-0">
                
            <ul class="row pt-1 pb-1" style="color: white; background-color: black; font-size: 0.85rem;">
            <li class="col-2" onclick="closeFS()">Back to lists</li>
            <li class="col-2" onclick="fsAddNewCard()">Add new sub card</li>
            <li class="col-2" onclick="fsAddNewList()">Add new sub list</li>
            </ul>

            <div id="fs_frame" class="fs_frame row flex-nowrap">
                <div class="fs_list_main content_main fs_list">
                    
                    <div id="${cardMetadata}" class="card id">
                        <div class="card_sort_handle"><span class="material-icons">drag_handle</span></div>
                        <div class="row">
                        <div class="edit_handle"><span class="material-icons">edit</span></div>
                        <div contentEditable="false" class="card_content content_main">
                        ${cardContent}
                        </div>
                        <div class="content_side">
                            <ul class="metadata">
                            <li>${cardMetadata}</li>
                            </ul>
                        </div>
                        </div>
                    </div>                        
                    
                </div>
                <div class="fs_list_sub content_main fs_list"></div>
            </div>
            </div>
            `
            // Insert into page
            $('#target').html(fsContainer);

            // Render sub cards
            for (let i = 0; i < cardChildren.length; i++) {
                let subCardID = cardChildren[i].subcard_id;
                let subCardBody = cardChildren[i].subcard_body;
                let newCard = `
                <div id="${subCardID}" class="card id">
                <div class="card_sort_handle"><span class="material-icons">drag_handle</span></div>
                <div class="row">
                <div class="edit_handle"><span class="material-icons">edit</span></div>
                <div contentEditable="false" class="card_content content_main">
                ${subCardBody}
                </div>
                <div class="content_side">
                    <ul class="metadata">
                    <li>${subCardID}</li>
                    </ul>
                </div>
                </div>
                </div>
                `
                $('.fs_list_sub').append(newCard);
            };

            // Sortables for Fullscreen
            var fs = document.querySelectorAll(".fs_list");
            for (var i = 0; i < fs.length; i++) {
                var sortable = fs[i];
                new Sortable(sortable, {
                    handle: '.card_sort_handle',
                    group: 'shared',
                    animation: 150,
                    easing: "cubic-bezier(1, 0, 0, 1)",
                    ghostClass: 'blue-background-class',
                });
            };

            // Listens for clicks to edit card content
            $(".edit_handle").on('click', function() {
                console.log("edit clicked");
                let endPoint = '/app/cards/subcard/edit';
                // Goes up one level in the DOM tree and finds the card content container
                let cardContentContainer = $(this).parent().find('.card_content');
                // gets the card ID
                let cardId = cardContentContainer.closest('.id').attr('id');
                let parentCardId = $('.fs_list_main').find('.id').attr('id');
                const dataRequest = [cardId, parentCardId]

                // fetches the un-markdown-ed text as stored
                const request = new Request(endPoint, {
                    method: 'POST',
                    body: JSON.stringify(dataRequest),
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
                            const changedData = [cardId, 'Sub Card Content', parentCardId];
                            // Changes to contentEditable mode
                            cardContentContainer.attr('contentEditable', 'true');
                            cardContentContainer.focus();
                            // Listens for enter key, if pressed exits edit mode
                            cardContentContainer.on('keydown', function(e) {
                                if (e.key == "s" && e.ctrlKey) {
                                    e.preventDefault();
                                    cardContentContainer.attr('contentEditable', 'false');
                                    // adds new text content to changedData array
                                    changedData.push($(this).prop('innerText'));
                                    // sends to the backend
                                    const request = new Request(endPoint, {
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
                                            // reset listeners
                                            removeListeners();
                                            enableListeners();
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
                                    // reset listeners
                                    removeListeners();
                                    enableListeners();
                                }
                            })
                        }
                    }) 
            });
        });
};


function fsAddNewCard() {
    let listObj = $('.fs_list_sub')
    let endPoint = "/app/cards/subcard/new"
    fetch(endPoint)
        .then(resp => resp.json())
        .then(cardId => {
            let newCard = `
            <div id="${cardId}" class="card id">
            <div class="card_sort_handle"><span class="material-icons">drag_handle</span></div>
            <div class="row">
            <div class="edit_handle"><span class="material-icons">edit</span></div>
            <div contentEditable="false" class="card_content content_main"></div>
            <div class="content_side">
                <ul class="metadata">
                <li>${cardId}</li>
                </ul>
            </div>
            </div>
            </div>
            `
            
            // Insert card
            $(listObj).append(newCard);

            // edit card content
            let newCardObj = $(`#${cardId}`).find('.card_content');
            let parentCardId = $('.fs_list_main').find('.id').attr('id');
            console.log(parentCardId);
            // Stops listening to clicks when editing
            if (newCardObj.attr('contentEditable') == 'false') {
                // create the array to be sent to the backend
                const changedData = [newCardObj.closest('.id').attr('id'), 'new subcard', parentCardId];
                // Changes to contentEditable mode
                newCardObj.attr('contentEditable', 'true');
                newCardObj.focus();

                // Listens for paste event, replaces formatted text with plain text
                newCardObj.on("paste",function(event){
                    event.preventDefault();
                    // console.log(window.event.clipboardData);
                    let clipboarddata =  window.event.clipboardData.getData('text/plain');    
                    // console.log("paste value" + clipboarddata);
                    newCardObj.text(clipboarddata);
                });

                // Listens for enter key, if pressed exits edit mode
                newCardObj.on('keydown', function(e) {
                    if (e.key == "s" && e.ctrlKey) {
                        e.preventDefault();
                        newCardObj.attr('contentEditable', 'false');
                        // adds new text content to changedData array
                        changedData.push($(this).prop('innerText'));
                        // sends to the backend
                        const request = new Request(endPoint, {
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
                                newCardObj.off();
                                // reset listeners
                                removeListeners();
                                enableListeners();

                            });
                    }
                })
                newCardObj.on('keydown', function(e) {
                    if (e.key == "Escape") {
                        // newCardObj.attr('contentEditable', 'false');
                        $(`#${cardId}`).remove();
                        newCardObj.off();
                        // reset listeners
                        removeListeners();
                        enableListeners();
                    }
                })
            }
        }) 
};

function fsAddNewList() {
    $('#fs_frame').append('<div class="fs_list_scratch content_main fs_list"></div>');

    // Sortables for Fullscreen
    var fs = document.querySelectorAll(".fs_list");
    for (var i = 0; i < fs.length; i++) {
        var sortable = fs[i];
        new Sortable(sortable, {
            handle: '.card_sort_handle',
            group: 'shared',
            animation: 150,
            easing: "cubic-bezier(1, 0, 0, 1)",
            ghostClass: 'blue-background-class',
        });
    };
};


function closeFS() {
    $("#fullscreen").remove();
    $('body').removeClass('freeze_scroll');
};

// ---------------------- // Start // ---------------------- //
// Because everything is loaded programically we need to set a delay otherwise this runs before there is anything on screen
$(document).ready(function(){
    enableListeners();
    enableSortable();
});