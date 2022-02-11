# Shinrin, Prototype v2

from flask import Flask, render_template, request, make_response, jsonify
from markupsafe import Markup
import datetime as dt
import markdown as md
import json
from random import choices
from board import Board, List, Card
from copy import deepcopy
# from itertools import zip_longest

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
    filename = f"user_data/{user_key}.json"
    # filename = 'user_data/test_data.json'
    try:
        with open(filename, mode='r') as data_file:
            data = json.load(data_file)
    except FileNotFoundError:
        with open('user_data/test_data.json', mode='r') as data_file:
            data = json.load(data_file)
    # Converting list/card IDs back to ints because JSON requires them to be stored as strings.
    # cleaned = {int(key): value for key, value in data[data_type].items()}
    cleaned = [value for value in data[data_type]]
    # print(f"loaded data: {data}")
    return cleaned


def write_data():
    list_pos = []
    for list_obj in bd.current_list_objects:
        if len(list_obj.cards) == 0:
            cards = []
        else:
            cards = [c for c in list_obj.cards]

        new_list = {
            "list_id": list_obj.list_id,
            "list_name": list_obj.list_name,
            "is_notebook": list_obj.is_notebook,
            "cards": cards
        }
        list_pos.append(new_list)

    content = []
    for card_obj in bd.current_card_objects:
        new_card = {
            "card_id": card_obj.card_id,
            "card_title": "",
            "card_body": card_obj.card_body,
            "tags": "",
            "card_children": [],
            "related_cards": ""
        }
        content.append(new_card)

    # Create the structure to save in JSON
    save_data = {
        'board': {},
        'lists': list_pos,
        'cards': content
    }
    filename = f"user_data/{bd.user_key}.json"
    with open(filename, mode='w') as data_file:
        json.dump(save_data, data_file, indent=4)


def get_new_id():
    # Generates a new id for each element created.
    new_id = dt.datetime.now().strftime('%Y%m%d%H%M%S')
    return new_id


def get_new_user_key():
    # alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
    # 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
    # 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

    alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                'U', 'V', 'W', 'X', 'Y', 'Z']
    new_key = ''.join(choices(alphabet, k=6))
    return new_key


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
    # if text.find('\\n'):
    #     return text.replace('\\n', '<br/>')
    # elif text.find('\n'):
    #     return text.replace('\n', '<br/>')
    # else:
    #     return text


# ----------------- # Start Here # ----------------- #
@app.route('/')
def login():
    resp = make_response(render_template('login.html'))
    return resp


@app.route('/app', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        requested = request.form
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
    bd.create_list_objects(saved_list_data)
    list_objects = deepcopy(bd.current_list_objects)
    # deepcopy() clones rather than points to list objects -- we need this because later we will merge list objects
    # and card objects into a single dictionary to send to the template, which also means current_list_objects will
    # contain all the card data rather than just the card ID.
    # print(f"list_objects: {list_objects}")
    # list_objects: [<board.List object at 0x000002C2049B4F10>, <board.List object at 0x000002C2049B4D30>]

    card_objects = bd.create_card_objects(saved_card_data)
    # bd.current_card_objects = card_objects
    # print(f"card_objects: {card_objects}")
    # card_objects: [<board.Card object at 0x00000196545D65E0>, <board.Card object at 0x00000196545D6040>,
    # <board.Card object at 0x00000196545D65B0>, <board.Card object at 0x00000196545D66A0>]

    # Creates {CardID:Index of Card Obj in Card Objects list} so we know which object to access to update content.
    bd.current_card_obj_index = {each.card_id: card_objects.index(each) for each in card_objects}
    # print(f"Card Obj Index: {bd.current_card_obj_index}")
    # Card Obj Index: {20220120115820735302: 0, 20220120120149112482: 1,
    # 20220120132630684721: 2, 20220120154744804753: 3}

    # Do the same for lists
    bd.current_list_obj_index = {each.list_id: list_objects.index(each) for each in list_objects}
    # print(bd.current_list_obj_index)

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
    # print(user_cards)
    # [print(obj.cards) for obj in bd.current_list_objects]
    resp = make_response(render_template('index.html', lists=user_lists, user_key=bd.user_key))
    return resp


# ----------------- # List Routes # ----------------- #
@app.route('/app/l/new', methods=['GET', 'POST'])
def list_new():
    if request.method == 'GET':
        # Get a new id for the new list
        return jsonify(get_new_id())

    if request.method == 'POST':
        new_list_data = request.get_json()
        # returns ['20220208210219163284', 'new list', 'This is the new name']

        # Create new card object and prepend to current list objects
        new_list_obj = List()
        new_list_obj.list_id = int(new_list_data[0])
        new_list_obj.list_name = process_newlines(new_list_data[-1])
        bd.current_list_objects.insert(0, new_list_obj)
        # Update list object index
        bd.current_list_obj_index = {each.list_id: bd.current_list_objects.index(each) for each in bd.current_list_objects}
        # Write to disk
        write_data()
        return jsonify('ok'), 204


@app.route('/app/l/minimise', methods=['POST'])
def card_add_to_minimise():
    if request.method == 'POST':
        print(request.get_json())
    return '', 204


@app.route('/app/l/trash', methods=['DELETE'])
def list_move_to_trash():
    if request.method == 'DELETE':
        x = int(request.get_json())
        x_index = bd.current_list_obj_index[x]
        del bd.current_list_objects[x_index]
        write_data()
        return '', 204


@app.route('/app/l/archive')
def list_add_to_archive():
    pass


@app.route('/app/l/update', methods=['POST'])
def list_order_update():
    if request.method == 'POST':
        # the data passed is an array with the old index to the new index
        # 1. get changed data
        changed_data = request.get_json()
        # 2. grab the current list of card objects, take the card object from old index and re-insert it at new index
        list_objects = bd.current_list_objects
        card_to_move = list_objects.pop(changed_data[0])
        list_objects.insert(changed_data[1], card_to_move)
        # 3. update the new card objects index, the new card objects, and write to disk
        bd.current_list_obj_index = {each.list_id: list_objects.index(each) for each in list_objects}
        bd.current_list_objects = list_objects
        write_data()
    return '', 204


@app.route('/app/l/rename', methods=['POST', 'PUT'])
def list_rename():
    if request.method == 'POST':
        print(request.get_json())
    return '', 204


# ----------------- # Card Routes # ----------------- #
# Show full-screen
@app.route('/app/c/<card_id>')
def card(card_id):
    print(type(card_id), card_id)
    print(bd.current_card_obj_index)
    card_index = bd.current_card_obj_index[int(card_id)]
    # card_index = bd.current_card_obj_index[card_id]

    card_content = Markup(md.markdown(process_newlines(bd.current_card_objects[card_index].card_body)))
    card_metadata = bd.current_card_objects[card_index].card_id
    # return render_template('fullscreen.html', content=card_content, metadata=card_metadata)
    resp = [card_content, card_metadata]
    return jsonify(resp)


# todo: update template
@app.route('/app/c/new', methods=['GET', 'POST'])
def card_new():
    if request.method == 'GET':
        # Get a new id for the new card
        return jsonify(get_new_id())

    if request.method == 'POST':
        # print(request.get_json())
        new_card_data = request.get_json()
        new_card_data[0] = int(new_card_data[0])
        # Returns ['new card id', 'new card', 'list id', 'card body']

        # Create new card object and append to current card objects
        new_card_obj = Card()
        new_card_obj.card_id = new_card_data[0]
        new_card_obj.card_body = process_newlines(new_card_data[-1])
        bd.current_card_objects.append(new_card_obj)

        # Update card object index
        card_objects = bd.current_card_objects
        bd.current_card_obj_index = {each.card_id: card_objects.index(each) for each in card_objects}

        # update list object with the new card id and position
        list_objects = bd.current_list_objects
        to_list_index = bd.current_list_obj_index[int(new_card_data[2])]
        to_list = list_objects[to_list_index].cards
        to_list.append(new_card_data[0])

        # Write to disk
        write_data()

        # Return markdown processed card body
        convert_to_markdown = Markup(md.markdown(new_card_data[-1]))
        return jsonify(convert_to_markdown)


@app.route('/app/c/update', methods=['POST'])
def card_order_update():
    if request.method == 'POST':
        # 1. get data
        changed_data = request.get_json()
        # returns ['20220120115816469292', 1, '20220120115816469292', 0]

        # 2. remove the card id from the first list id + index
        # get list objects
        list_objects = bd.current_list_objects
        # get the index of where the card to replace is
        from_list_index = bd.current_list_obj_index[int(changed_data[0])]
        from_list = list_objects[from_list_index].cards
        card_to_remove = from_list[changed_data[1]]
        card_to_remove_index = from_list.index(card_to_remove)
        # remove card
        removed_card = from_list.pop(card_to_remove_index)

        # so far I've removed the card id from the list it was at. Next:
        # 3. insert the card id to the new list id + index
        to_list_index = bd.current_list_obj_index[int(changed_data[2])]
        to_list = list_objects[to_list_index].cards
        to_list.insert(changed_data[3], removed_card)
        # print([obj.cards for obj in bd.current_list_objects])

        # 5. write to disk
        write_data()
    return '', 204


@app.route('/app/c/archive')
def card_add_to_archive():
    pass


@app.route('/app/c/trash', methods=['DELETE'])
def card_move_to_trash():
    pass


@app.route('/app/c/edit', methods=['POST', 'PUT'])
def card_edit_content():
    if request.method == 'POST':
        # accept the cardID, get the unwrapped content of that card and pass it through
        # 1. get the passed card id
        req_card_id = int(request.get_json())
        # print(f"req_card_id: {req_card_id}")

        # 2. look up the index of that card object
        if req_card_id in bd.current_card_obj_index:
            req_card_id_index = bd.current_card_obj_index[req_card_id]
            # 3. get the stored data unwrapped from the object
            req_data = process_newlines(bd.current_card_objects[req_card_id_index].card_body)
            # 4. return that data
            return jsonify(req_data)
        else:
            return '', 204

    if request.method == 'PUT':
        # 1. accept the changes
        changed_data = request.get_json()
        # print(f"changed data: {changed_data}")
        print(f"length current card objects before: {len(bd.current_card_objects)}")
        # 2. update card content
        # get card id
        changed_data_card_id = int(changed_data[0])
        # get the index of the matching card object
        changed_data_card_obj_index = bd.current_card_obj_index[changed_data_card_id]
        # update card object with new data
        bd.current_card_objects[changed_data_card_obj_index].card_body = changed_data[-1]
        # print(bd.current_card_objects[changed_data_card_obj_index].card_body)
        print(f"length current card objects: {len(bd.current_card_objects)}")

        # 3. write changes to disk
        write_data()

        # 4. wrap in markdown and return
        convert_to_markdown = Markup(md.markdown(changed_data[2]))
        return jsonify(convert_to_markdown)


# ----------------- # Delete Things # ----------------- #

# To delete lists and cards I'm basically swapping the existing data for nothing using this function.
@app.route('/remove', methods=['DELETE'])
def remove():
    if request.method == 'DELETE':
        x = int(request.get_json())
        x_index = bd.current_list_obj_index[x]
        del bd.current_list_objects[x_index]
        write_data()
        return '', 204


if __name__ == '__main__':
    app.run(debug=True)