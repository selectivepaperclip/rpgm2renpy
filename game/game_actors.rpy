init python:
    class GameActors(SelectivelyPickle):
        def __init__(self):
            self.overrides = {
                1: {
                    "name": "MCName"
                }
            }

        def __setstate__(self, d):
            self.__dict__.update(d)
            if not hasattr(self, 'overrides'):
                self.overrides = {}

        def data(self):
            if not hasattr(self, '_data'):
                with rpgm_file('www/data/Actors.json') as f:
                    self._data = json.load(f)

            return self._data

        def set_property(self, index, property_name, property_value):
            if not self.overrides.has_key(index):
                self.overrides[index] = {}
            self.overrides[index][property_name] = property_value

        def by_index(self, index):
            actor_data = self.data()[index]
            actor_data.update(self.overrides.get(index, {}))
            return actor_data
