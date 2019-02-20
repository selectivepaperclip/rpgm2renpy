init python:
    class GameSelfSwitches:
        def __init__(self):
            self.switch_values = {}

        def value(self, key):
            return self.switch_values.get(key, None)

        def set_value(self, key, value):
            changed = False
            if value:
                changed = (key not in self.switch_values or self.switch_values[key] != value)
                self.switch_values[key] = value
            elif key in self.switch_values:
                changed = True
                del self.switch_values[key]
            return changed

        def print_values(self):
            for key, value in sorted(self.switch_values.iteritems()):
                print "%s: %s" % (key ,value)
