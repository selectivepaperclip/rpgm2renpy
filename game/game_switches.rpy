init python:
    class GameSwitches(SelectivelyPickle):
        def __init__(self, switch_names):
            self._switch_names = switch_names
            self.switch_values = [0] * len(switch_names)

        def reload_switch_names(self):
            self._switch_names = game_state.system_data()['switches']
            for i in xrange(len(self.switch_values), len(self._switch_names)):
                self.switch_values.append(0)

        def ensure_switch_names_loaded(self, switch_id):
            if not hasattr(self, '_switch_names'):
                self.reload_switch_names()

        def value(self, switch_id):
            self.ensure_switch_names_loaded(switch_id)
            if switch_id >= len(self.switch_values):
                return False
            return self.switch_values[switch_id]

        def set_value(self, switch_id, value):
            self.ensure_switch_names_loaded(switch_id)
            self.switch_values[switch_id] = value

        def debug_values(self):
            result = []

            self.reload_switch_names()
            longest_string = len(max(self._switch_names, key=len))

            for i in xrange(0, len(self._switch_names)):
                result.append(("%3s: - '%s' - %s") % (i, self._switch_names[i], self.switch_values[i]))

            return result

        def print_values(self):
            print "\n".join(self.debug_values())
