init python:
    class GameSwitches:
        def __init__(self, switch_names):
            self.switch_names = switch_names
            self.switch_values = [0] * len(switch_names)

        def value(self, switch_id):
            if switch_id >= len(self.switch_values):
                return False
            return self.switch_values[switch_id]

        def set_value(self, switch_id, value):
            self.switch_values[switch_id] = value

        def print_values(self):
            longest_string = len(max(self.switch_names, key=len))

            print "ACTIVE SWITCHES:"
            for i in xrange(0, len(self.switch_names)):
                if self.switch_values[i]:
                    print ("%3s: - '%s'") % (i, self.switch_names[i])

            print "INACTIVE SWITCHES:"
            for i in xrange(0, len(self.switch_names)):
                if not self.switch_values[i]:
                    print ("%3s: - '%s'") % (i, self.switch_names[i])
