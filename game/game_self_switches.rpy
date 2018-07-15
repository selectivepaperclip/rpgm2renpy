init python:
    class GameSelfSwitches:
        def __init__(self):
            self.switch_values = {}

        def value(self, key):
            return self.switch_values.get(key, None)

        def set_value(self, key, value):
            if value:
                self.switch_values[key] = value
            else:
                del self.switch_values[key]

        def print_values(self):
            for key, value in sorted(self.switch_values.iteritems()):
                print "%s: %s" % (key ,value)
