
class Board:
    def __init__(self):
        self.user_key = 'new_user'
        self.current_board_index = {}
        self.current_list_objects = []
        self.current_list_obj_index = {}
        self.current_card_objects = []
        self.current_card_obj_index = {}
        self.current_card_id = str
        self.current_list_id = str
        self.current_list_name = str

    def create_list_objects(self, saved_list_data):
        list_objects = []
        for each_list in saved_list_data:
            new_list_obj = List()
            new_list_obj.list_id = each_list['list_id']
            new_list_obj.list_name = each_list['list_name']
            new_list_obj.cards = each_list['cards']
            list_objects.append(new_list_obj)
        self.current_list_objects = list_objects
        return self.current_list_objects

    def create_card_objects(self, saved_card_data):
        card_objects = []
        for each_card in saved_card_data:
            new_card_obj = Card()
            new_card_obj.card_id = each_card['card_id']
            new_card_obj.card_body = each_card['card_body']
            new_card_obj.card_children = each_card['card_children']
            card_objects.append(new_card_obj)
        self.current_card_objects = card_objects
        return self.current_card_objects

    def create_list_objects_index(self):
        self.current_list_obj_index = {each.list_id: self.current_list_objects.index(each)
                                       for each in self.current_list_objects}
        print(f"List Obj Index {self.current_list_obj_index}")

    def create_card_objects_index(self):
        self.current_card_obj_index = {each.card_id: self.current_card_objects.index(each)
                                       for each in self.current_card_objects}
        print(f"Card Obj Index {self.current_card_obj_index}")


class List:
    def __init__(self):
        self.list_id = str
        self.list_name = str
        self.cards = []


class Card:
    def __init__(self):
        self.card_id = str
        self.card_body = str
        self.card_children = []
