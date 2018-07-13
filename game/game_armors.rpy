init python:
    class GameArmors(SelectivelyPickle):
        def __init__(self):
            pass

        def data(self):
            if not hasattr(self, '_data'):
                with rpgm_file('www/data/Armors.json') as f:
                    self._data = json.load(f)

            return self._data

        def by_id(self, id):
            for armor in self.data():
                if armor and armor['id'] == id:
                    return armor
            return None
