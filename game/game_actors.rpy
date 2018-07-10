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
            self.populate_override(index)
            self.overrides[index][property_name] = property_value

        def add_state(self, index, state_to_change):
            self.populate_states(index)
            self.overrides[index]['affected_states'].add(state_to_change)

        def remove_state(self, index, state_to_change):
            self.populate_states(index)
            affected_states = self.overrides[index]['affected_states']
            if state_to_change in affected_states:
                affected_states.remove(state_to_change)

        def populate_override(self, index):
            if not self.overrides.has_key(index):
                self.overrides[index] = {}

        def populate_states(self, index):
            self.populate_override(index)
            overrides = self.overrides[index]
            if not hasattr(overrides, 'affected_states'):
                overrides['affected_states'] = Set()

        def by_index(self, index):
            actor_data = self.data()[index]
            actor_data.update(self.overrides.get(index, {}))
            return actor_data
