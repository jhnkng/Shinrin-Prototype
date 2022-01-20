# Shinrin, Prototype v0351
# This continues from v0301

from flask import Flask, render_template, request, make_response
from board import Board
from markupsafe import Markup
import datetime as dt
import markdown as md
import json
from random import randint
from itertools import zip_longest


app = Flask(__name__)
bd = Board()


# ----------------- # Functions # ----------------- #
def get_data(user_key, data_type):
    """
    Loads saved data, returns the datatype requested
    :param user_key: user's access key. If new user key should be 'new_user'
    :param data_type: lists or cards
    :return: processed requested data
    """
    filename = f"{user_key}.json"
    try:
        with open(filename, mode='r') as data_file:
            data = json.load(data_file)
    except FileNotFoundError:
        with open('new_user.json', mode='r') as data_file:
            data = json.load(data_file)
    # Converting list/card IDs back to ints because JSON requires them to be stored as strings.
    cleaned = {int(key): value for key, value in data[data_type].items()}
    return cleaned


def write_data(list_pos, content):
    """
    Create the structure to save back to JSON to disk
    :param list_pos: The positions of lists and cards as passed back by the UI
    :param content: the card content that was in the UI
    :return: none
    """
    # Create the structure to save in JSON
    save_data = {
        'board': {},
        'lists': list_pos,
        'cards': content
    }
    filename = f"{bd.user_key}.json"
    with open(filename, mode='w') as data_file:
        json.dump(save_data, data_file, indent=2)


def get_new_id():
    # Generates a new id for each element created.
    new_id = dt.datetime.now().strftime('%Y%m%d%H%M%S%f')
    return new_id


def get_new_user_key():
    return randint(10000, 99999)


def process_newlines(text):
    """
    Escapes \n or unescapes \\n as required.
    :param text: string to be processed
    :return: string
    """
    if text.find('\\n'):
        return text.replace('\\n', '\n')
    elif text.find('\n'):
        return text.replace('\n', '\\n')
    else:
        return text


def change_order(new_pos, list_names, card_content):
    # ----------- # Wrangle Lists # ----------- #
    # 1. Get the data passed back from the UI
    ui_returned_content_order = list(new_pos)

    # 2. Create an index of each list with all the cards in the list as a dictionary
    #   a. get the index for each List ID in data
    new_list_order_index = [ui_returned_content_order.index(item) for item in ui_returned_content_order if
                            'list_id' in item]

    #   b. Sorts data
    sorted_list_card_positions = [ui_returned_content_order[a:b] for a, b in
                                  zip_longest([0] + new_list_order_index, new_list_order_index)][1:]

    #   c. Create the index as a dictionary
    new_list_index = {}
    for each_list in sorted_list_card_positions:
        new_entry = {
            int(each_list[0].split(' ')[1]): [int(card.split(' ')[1]) for card in each_list[1:]]
        }
        new_list_index.update(new_entry)
    #   returns: {6: [1, 2], 7: [3, 4], 11: [5]}

    #   d. Make a list of all the existing notebooks
    notebooks_list = []
    for each_list in sorted_list_card_positions:
        list_id = int(each_list[0].split(' ')[1])
        if 'note' in each_list[0].split(' ')[-1]:
            notebooks_list.append(list_id)
    # Returns a list of IDs that are notebooks. Later we check against this list to set is_notebook:True

    # 3. Sort lists
    #   a. List ids are keys in the New Board Index, so get those and return a list of ints
    new_list_order = [item for item in list(new_list_index.keys())]
    #   returns [7, 6, 11] list IDs in the new order

    #   b. Make a dict that matches List IDs with their Titles (from list_names)
    new_list_names = {new_list_order[i]: list_names[i] for i in range(len(new_list_order))}
    #   returns {38: 'List name', 35: 'list name'}
    # print(f"list_names:{list_names}")
    # new_list_names = {}
    # for i in range(len(new_list_order)):
    #     print(f"i:{i}, len:{len(new_list_order)}, new_list_order:{new_list_order[i]}, list_names:{list_names[i]}")
    #     new_list_order[i]: list_names[i]

    # 4. Iterate through the new list order (which holds the ListIDs) and use that to pull the corresponding
    #   index in order to access the list/card data to rebuild the entries in the new order
    #   But first, get a fresh copy of current saved list data
    stored_list_data = get_data(bd.user_key, "lists")
    new_list_pos_data_to_save = {}
    for num in new_list_order:
        # If the listID currently exists
        if num in list(stored_list_data.keys()):
            # Writes in the location of each card in their lists.
            stored_list_data[num]['cards'] = new_list_index[num]
            # Write in the list name
            stored_list_data[num]['list_name'] = new_list_names[num]
            # Write in notebook status
            if num in notebooks_list:
                stored_list_data[num]['is_notebook'] = True
            else:
                stored_list_data[num]['is_notebook'] = False
            # saves to new data to save
            new_list_pos_data_to_save[num] = stored_list_data[num]
        else:
            # make new structure to save
            new_list_pos_data_to_save[num] = {
                "list_id": num,
                "list_name": new_list_names[num],
                "is_notebook": False,
                "cards": new_list_index[num]
            }
            if num in notebooks_list:
                new_list_pos_data_to_save[num]['is_notebook'] = True

    # ----------- # Wrangle Card Content # ----------- #
    # 5. Wrangle and save card content
    #   a. Get a fresh copy of current saved list data
    stored_card_content = get_data(bd.user_key, "cards")

    #   b. Get card content data passed back from UI
    ui_returned_card_content = card_content  # Returns a list of the card body text.

    #   c. Make a list of the card IDs from the new order data
    ui_returned_card_ids = [int(item.split(' ')[1]) for item in ui_returned_content_order if 'card_id' in item]

    #   d. zip the card ids and card content together
    ui_returned_cards = zip(ui_returned_card_ids, ui_returned_card_content)

    #   e. Update stored card content with UI returned card content
    for card in ui_returned_cards:
        c_id = card[0]
        body = card[1]      # Todo: could run newline escape here
        if c_id in list(stored_card_content.keys()):
            # if the card id exists, update the card body content
            stored_card_content[c_id]['card_body'] = body
        else:
            # if not, make a new entry
            stored_card_content[c_id] = {
                "card_id": c_id,
                "card_body": body
            }

    # 5. Write to disk
    write_data(new_list_pos_data_to_save, stored_card_content)


# ----------------- # Start Here # ----------------- #
@app.route('/')
def login():
    resp = make_response(render_template('login.html'))
    return resp


@app.route('/board', methods=['GET', 'POST'])
def board():
    if request.method == 'POST':
        requested = request.form
        print(requested)
        user_key = requested.get('user')
        if user_key:
            bd.user_key = user_key
        else:
            bd.user_key = get_new_user_key()

    # ---------------- # 1. Get Data # ---------------- #
    # First we get the saved data and wrangle it to send to the template.
    # The template is expecting a list of dictionaries:
    # [{
    #     'list_id': int,
    #     'list_name': str,
    #     'is_notebook': bool,
    #     'cards': [{ 'card_id': int, 'card_body': str }, { 'card_id': int, 'card_body': str }]
    # }]
    # ...so let's build it.
    # Get saved data
    saved_list_data = get_data(bd.user_key, 'lists')
    saved_card_data = get_data(bd.user_key, 'cards')
    # Objectify
    list_objects = bd.create_list_objects(saved_list_data)
    card_objects = bd.create_card_objects(saved_card_data)

    # Because the template is expecting a single list of dictionaries (with dictionary == 1 list) we
    # have to combine the list and card data by:
    #   1. taking the list of Card IDs in list['cards']
    #   2. finding the matching card from the Card ID
    #   3. inserting the entire card dictionary as a value in list['cards']
    user_lists = [vars(list_obj) for list_obj in list_objects]
    user_cards = {card_obj.card_id: vars(card_obj) for card_obj in card_objects}
    for item in user_lists:
        card_locations = item['cards']
        cards_to_merge = []
        for card_id_num in card_locations:
            if card_id_num in user_cards.keys():
                card = user_cards[card_id_num]
                # \n characters mess up templates, so they are stored escaped.
                # Here we unescape it before it goes to the UI
                unescaped_text = process_newlines(card['card_body'])
                # Raw text is sent through markdown to convert to HTML, then HTML characters unescaped using Markup
                card['card_body_html'] = Markup(md.markdown(unescaped_text))
                cards_to_merge.append(card)
            else:
                make_card = {
                    'card_id': card_id_num,
                    'card_body': f"Sorry, we couldn't find the data for {card_id_num}."
                }
                cards_to_merge.append(make_card)
        item['cards'] = cards_to_merge

    resp = make_response(render_template('index.html', lists=user_lists, user_key=bd.user_key))
    return resp


@app.route('/board/fullscreen')
def show_fullscreen():
    resp = make_response(render_template('snippets/full_screen.html'))
    return resp


@app.route('/board/archive')
def show_archive():
    card_data = get_data(bd.user_key, 'cards')
    list_id = 1
    list_name = 'Archive'
    cards = []
    for key in card_data.keys():
        card = card_data[key]
        unescaped_text = process_newlines(card['card_body'])
        card['card_body_html'] = Markup(md.markdown(unescaped_text))
        cards.append(card)
    print(cards)
    resp = make_response(
        render_template('snippets/archive.html', list_id=list_id, list_name=list_name, cards=cards)
    )
    return resp


# ----------------- # Change Things # ----------------- #


@app.route('/board/change', methods=['POST'])
def change_list_card_order():
    if request.method == 'POST':
        requested = request.form
        id_list = requested.getlist('id')
        list_names = requested.getlist('list_name')
        card_content = requested.getlist('card_body')

        # Send to sort and save
        change_order(id_list, list_names, card_content)
    return '', 204


@app.route('/board/list/edit', methods=['POST', 'PUT'])
def change_list_name():
    if request.method == 'POST':
        req = request.form
        current_list_id = req.get('current_list').split(':')[0]
        current_list_name = req.get('current_list').split(':')[1]
        resp = make_response(
            render_template('snippets/list_name_change_before.html', current_list_name=bd.current_list_name)
        )
        return resp

    if request.method == 'PUT':
        requested = request.form
        new_list_name = ''.join(requested.getlist('new_list_name'))
        resp = make_response(
            render_template(
                'snippets/list_name_change_after.html', new_list_name=new_list_name, list_id=bd.current_list_id
            )
        )
        resp.headers['HX-Trigger'] = 'syncChange'

        bd.current_list_name = ''
        bd.current_list_id = 0

        return resp


@app.route('/board/notebook/edit', methods=['POST', 'PUT'])
def change_notebook_name():
    if request.method == 'POST':
        req = request.form
        bd.current_notebook_id = req.get('current_notebook').split(':')[0]
        bd.current_notebook_name = req.get('current_notebook').split(':')[1]
        resp = make_response(
            render_template('snippets/notebook_name_change_before.html', current_notebook_name=bd.current_notebook_name)
        )
        return resp

    if request.method == 'PUT':
        requested = request.form
        new_notebook_name = ''.join(requested.getlist('new_notebook_name'))
        resp = make_response(
            render_template(
                'snippets/notebook_name_change_after.html', new_notebook_name=new_notebook_name, notebook_id=bd.current_notebook_id
            )
        )
        resp.headers['HX-Trigger'] = 'syncChange'

        bd.current_notebook_name = ''
        bd.current_notebook_id = 0

        return resp


@app.route('/board/card/edit', methods=['POST', 'PUT'])
def change_card_content():
    if request.method == 'POST':
        req = request.form
        bd.current_card_id = req.get('current_card_content').split('::::')[0]
        bd.current_card_content = req.get('current_card_content').split('::::')[1]

        resp = make_response(
            render_template('snippets/card_change_before.html', current_card_content=bd.current_card_content)
        )
        return resp

    if request.method == 'PUT':
        requested = request.form
        new_card_content = ''.join(requested.getlist('new_card_content'))

        # Todo: clean up these variable names!!!
        escaped_newline_text = new_card_content
        # Get rid of newlines because it breaks things
        # todo: moved to board.py, test here
        if '\n' in new_card_content:
            escaped_newline_text = new_card_content.replace('\n', '\\n')

        html_text = Markup(md.markdown(new_card_content))

        hxvals_body_text = escaped_newline_text

        resp = make_response(render_template('snippets/card_change_after.html', card_id=bd.current_card_id, hxvals_body=hxvals_body_text, card_body=html_text))
        resp = make_response(resp)
        resp.headers['HX-Trigger'] = 'syncChange'

        bd.current_card_content = ''
        bd.current_card_id = 0

        return resp


# ----------------- # Add New Things # ----------------- #

# Adds a new card
@app.route('/board/card/new')
def new_card():
    # Get a new id for the new card
    new_card_id = get_new_id()
    # Update the current_card_id parameter so that when the new card content is passed to change_card_content() the
    # ID will follow.
    bd.current_card_id = new_card_id
    resp = make_response(render_template('snippets/card_new.html', new_card_id=new_card_id))
    resp.headers['HX-Trigger'] = 'syncChange'
    return resp


# Add new list
@app.route('/board/list/new')
def new_list():
    new_list_id = get_new_id()
    bd.current_list_id = new_list_id
    resp = make_response(render_template('snippets/list_new.html', new_list_id=new_list_id))
    resp.headers['HX-Trigger'] = 'syncChange'
    return resp


# Add new notebook
@app.route('/board/notebook/new')
def new_notebook():
    new_notebook_id = get_new_id()
    bd.current_notebook_id = new_notebook_id
    resp = make_response(render_template('snippets/notebook_new.html', new_notebook_id=new_notebook_id))
    resp.headers['HX-Trigger'] = 'syncChange'
    return resp


# ----------------- # Delete Things # ----------------- #

# To delete lists and cards I'm basically swapping the existing data for nothing using this function.
@app.route('/remove', methods=['DELETE'])
def remove():
    resp = make_response('')
    resp.headers['HX-Trigger'] = 'syncChange'
    return resp


if __name__ == '__main__':
    app.run(debug=True)
