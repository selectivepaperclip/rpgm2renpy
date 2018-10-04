init python:
    class GameArmors(SelectivelyPickle):
        def __init__(self):
            pass

        def data(self):
            return game_file_loader.json_file(rpgm_data_path("Armors.json"))

        def by_id(self, id):
            for armor in self.data():
                if armor and armor['id'] == id:
                    return armor
            return None
