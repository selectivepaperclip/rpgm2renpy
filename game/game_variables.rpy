init python:
    class GameVariables:
        def __init__(self, variable_names):
            self.variable_names = variable_names
            self.variable_values = [0] * len(variable_names)

        def value(self, variable_id):
            return self.variable_values[variable_id]

        def set_value(self, variable_id, value):
            if isinstance(value, float):
                value = int(value)
            self.variable_values[variable_id] = value

        def operate_variable(self, variable_id, operation_type, value):
            old_value = self.value(variable_id)
            if operation_type == 0:
                self.set_value(variable_id, value)
                return old_value != value
            elif operation_type == 1:
                self.set_value(variable_id, old_value + value)
            elif operation_type == 2:
                self.set_value(variable_id, old_value - value)
            elif operation_type == 3:
                self.set_value(variable_id, old_value * value)
            elif operation_type == 4:
                self.set_value(variable_id, old_value / value)
            elif operation_type == 5:
                self.set_value(variable_id, old_value % value)
            return True

        def operate_value(self, operation, operand_type, operand):
            value = None
            if operand_type == 0:
                value = operand
            else:
                value = self.value(operand)

            if operation == 0:
                return value
            else:
                return -1 * value

        def debug_values(self):
            result = []

            longest_string = len(max(self.variable_names, key=len))

            for i in xrange(0, len(self.variable_names)):
                result.append(("%3s: '%" + str(longest_string) + "s' = %s") % (i, self.variable_names[i], self.variable_values[i]))

            return result

        def print_values(self):
            print "\n".join(self.debug_values())