
class Board:
    def __init__(self):
        # self.new_id = shinrin.get_data('id')
        self.user_key = 'new_user'
        self.current_board_index = dict
        self.current_list_objects = list
        self.current_list_obj_index = dict
        self.current_card_objects = list
        self.current_card_obj_index = dict
        self.current_card_id = int
        # self.current_card_content = str
        self.current_list_id = int
        self.current_list_name = str
        # self.current_notebook_id = int
        # self.current_notebook_name = str

    def create_list_objects(self, saved_list_data):
        list_objects = []
        for each_list in saved_list_data:
            new_list_obj = List()
            new_list_obj.list_id = each_list['list_id']
            new_list_obj.list_name = each_list['list_name']
            new_list_obj.is_notebook = each_list['is_notebook']
            new_list_obj.cards = each_list['cards']
            list_objects.append(new_list_obj)
        self.current_list_objects = list_objects
        return self.current_list_objects

    def create_card_objects(self, saved_card_data):
        card_objects = []
        for each_card in saved_card_data:
            new_card_obj = Card()
            new_card_obj.card_id = each_card['card_id']
            # new_card_obj.card_title = each_card['card_title']
            new_card_obj.card_body = each_card['card_body']
            card_objects.append(new_card_obj)
        self.current_card_objects = card_objects
        return self.current_card_objects


class List:
    def __init__(self):
        self.list_id = int
        self.list_name = str
        self.is_notebook = False
        self.cards = []


class Card:
    def __init__(self):
        self.card_id = int
        # self.card_title = str
        self.card_body = str
        # self.tags = str

