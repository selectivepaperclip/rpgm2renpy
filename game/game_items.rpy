init python:
    class GameItems(SelectivelyPickle):
        def __init__(self):
            pass

        def data(self):
            return game_file_loader.json_file(rpgm_data_path("Items.json"))

        def by_id(self, id):
            for item in self.data():
                if item and item['id'] == id:
                    return item
            return None

        def by_name(self, name):
            # In cases where two items have the exact same name,
            # YEP_ItemSynthesis matches to the LAST item with the same name, not the first
            matching_item = None
            for item in self.data():
                if item and item['name'] == name:
                    matching_item = item
            return matching_item
