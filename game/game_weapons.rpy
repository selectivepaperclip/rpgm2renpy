init python:
    class GameWeapons(SelectivelyPickle):
        def __init__(self):
            pass

        def data(self):
            if not hasattr(self, '_data'):
                with rpgm_data_file('Weapons.json') as f:
                    self._data = json.load(f)

            return self._data

        def by_id(self, id):
            for weapon in self.data():
                if weapon and weapon['id'] == id:
                    return weapon
            return None
