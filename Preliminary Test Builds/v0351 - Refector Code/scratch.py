import shinrin as sr
from board import Board, List, Card
from markupsafe import Markup
import datetime as dt
import markdown as md


board = Board()

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
saved_list_data = sr.get_data('lists')
saved_card_data = sr.get_data('cards')
# Objectify
list_objects = board.create_list_objects(saved_list_data)
card_objects = board.create_card_objects(saved_card_data)

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
            # \n characters mess up templates, so they are stored escaped. Here we unescape it before it goes to the UI
            unescaped_text = sr.process_newlines(card['card_body'])
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
