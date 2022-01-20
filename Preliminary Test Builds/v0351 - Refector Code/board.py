import shinrin


class Board:
    def __init__(self):
        # self.new_id = shinrin.get_data('id')
        self.user_key = '0'
        self.current_list_objects = list
        self.current_card_objects = list
        self.current_card_id = int
        self.current_card_content = str
        self.current_list_id = int
        self.current_list_name = str
        self.current_notebook_id = int
        self.current_notebook_name = str

    def create_list_objects(self, saved_list_data):
        list_objects = []
        for key in saved_list_data.keys():
            l = saved_list_data[key]
            new_list = List()
            new_list.list_id = l['list_id']
            new_list.list_name = l['list_name']
            new_list.is_notebook = l['is_notebook']
            new_list.cards = l['cards']
            list_objects.append(new_list)
        self.current_list_objects = list_objects
        return self.current_list_objects

    def create_card_objects(self, saved_card_data):
        card_objects = []
        for key in saved_card_data.keys():
            s = saved_card_data[key]
            new_card = Card()
            new_card.card_id = s['card_id']
            new_card.card_body = s['card_body']
            card_objects.append(new_card)
        self.current_card_objects = card_objects
        return self.current_card_objects


class List:
    def __init__(self):
        self.list_id = int
        self.list_name = str
        self.is_notebook = False
        self.cards = list


class Card:
    def __init__(self):
        self.card_id = int
        self.card_body = str
