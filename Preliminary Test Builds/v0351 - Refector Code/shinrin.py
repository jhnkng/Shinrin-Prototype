from markupsafe import Markup
import datetime as dt
import markdown as md
from itertools import zip_longest
import json
from random import randint


# ----------------- # Functions # ----------------- #
def get_data(user_key, data_type):
    """
    Loads saved data, returns the datatype requested
    :param user_key: user's access key. If new user key should be 'new_user'
    :param data_type: lists or cards
    :return: processed requested data
    """
    filename = f"{user_key}.json"
    print(filename)
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
    with open('db.json', mode='w') as data_file:
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
    stored_list_data = get_data("lists")
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
    stored_card_content = get_data("cards")

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
