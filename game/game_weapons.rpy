init python:
    class GameWeapons(SelectivelyPickle):
        def __init__(self):
            pass

        def data(self):
            return game_file_loader.json_file(rpgm_data_path("Weapons.json"))

        def by_id(self, id):
            for weapon in self.data():
                if weapon and weapon['id'] == id:
                    return weapon
            return None
