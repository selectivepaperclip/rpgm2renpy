init python:
    import json

    for ix in range(0, 16 + 1):
        renpy.image("Intro %i" % ix, "unpacked/www/img/pictures/Intro %i.png" % ix)

    class GameSelfSwitches:
        def __init__(self):
            self.switch_values = {}

        def set_value(self, key, value):
            if value:
                self.switch_values[key] = value
            else:
                del self.switch_values[key]

    class GameSwitches:
        def __init__(self, switch_names):
            self.switch_names = switch_names
            self.switch_values = [0] * len(switch_names)

        def set_value(self, switch_id, value):
            self.switch_values[switch_id] = value

    class GameVariables:
        def __init__(self, variable_names):
            self.variable_names = variable_names
            self.variable_values = [0] * len(variable_names)

        def value(self, variable_id):
            return self.variable_values[variable_id]

        def set_value(self, variable_id, value):
            self.variable_values[variable_id] = value

        def operate_variable(self, variable_id, operation_type, value):
            old_value = self.value(variable_id);
            if operation_type == 0:
                self.set_value(variable_id, value)
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

    class GameEvent:
        def __init__(self, state, event_data):
            self.state = state
            self.event_data = event_data
            self.list_index = 0
            self.new_map_id = None
            self.x = None
            self.y = None

        def do_next_thing(self):
            if not self.done():
                list_item = self.event_data['pages'][0]['list'][self.list_index]

                # Show Text
                if list_item['code'] == 401 and len(list_item['parameters']) > 0 and list_item['parameters'][0][0] != "\\":
                    renpy.say(None, list_item['parameters'][0])
                # Transfer maps
                elif list_item['code'] == 201:
                    method, self.new_map_id, self.new_x, self.new_y = list_item['parameters'][0:4]
                    renpy.say(None, "Map %d" % self.new_map_id)
                    if method != 0:
                        renpy.say(None, "Method on transfer was nonzero (%d), plz implement!" % method)

                # Control Switches
                elif list_item['code'] == 121:
                    start, end, value = list_item['parameters'][0:3]
                    for i in xrange(start, end + 1):
                        self.state.switches.set_value(i, value == 0)

                # Control Variables
                elif list_item['code'] == 122:
                    start, end, operation_type, operand = list_item['parameters'][0:4]
                    value = 0;
                    if operand == 0:
                        value = list_item['parameters'][4]
                    elif operand == 1:
                        #    value = $gameVariables.value(this._params[4]);
                        renpy.say(None, "Variable control operand 1, plz implement")
                    elif operand == 2:
                        #    value = this._params[4] + Math.randomInt(this._params[5] - this._params[4] + 1);
                        renpy.say(None, "Variable control operand 2, plz implement")
                    elif operand == 3:
                        #    value = this.gameDataOperand(this._params[4], this._params[5], this._params[6]);
                        renpy.say(None, "Variable control operand 3, plz implement")
                    elif operand == 4:
                        #    value = eval(this._params[4]);
                        renpy.say(None, "Variable control operand 4, plz implement")

                    for i in xrange(start, end + 1):
                        self.state.variables.operate_variable(i, operation_type, value)

                # Control Self Switch
                elif list_item['code'] == 123:
                    switch_id, value = list_item['parameters']
                    key = (self.state.map.map_id, self.state.event.event_data['id'], switch_id)
                    self.state.self_switches.set_value(key, value == 0)

                # Show picture
                elif list_item['code'] == 231:
                    renpy.scene()
                    renpy.show(list_item['parameters'][1])
                    renpy.pause()

                self.list_index += 1

        def done(self):
            return self.list_index == len(self.event_data['pages'][0]['list'])

    class GameMap:
        def __init__(self, state, map_id, x, y):
            self.state = state
            self.map_id = map_id
            self.x = x
            self.y = y
            with renpy.file("unpacked/www/data/Map0%d.json" % map_id) as f:
                self.data = json.load(f)

        def find_event_for_location(self, x, y):
            for e in self.data['events']:
                if e and e['x'] == x and e['y'] == y:
                    return GameEvent(self.state, e)
            return None

        def find_auto_trigger_event(self):
            for e in self.data['events']:
                if e and e['pages'][0]['trigger'] == 3:
                    return GameEvent(self.state, e)
            return None

        def page_matches_conditions(self, conditions):
            if conditions['variableId'] == 1:
                return True

            return False

        def map_options(self):
            coords = []
            for e in self.data['events']:
                if e and self.page_matches_conditions(e['pages'][0]['conditions']):
                    if e['pages'][0]['trigger'] != 3:
                        coords.append((e['x'], e['y']))

            return coords

    class GameState:
        def __init__(self):
            with renpy.file('unpacked/www/data/System.json') as f:
                self.system_data = json.load(f)

            self.event = None
            self.starting_map_id = self.system_data['startMapId']
            self.ran_auto_trigger_events = False
            self.map = GameMap(self, self.starting_map_id, self.system_data['startX'], self.system_data['startY'])
            self.switches = GameSwitches(self.system_data['switches'])
            self.self_switches = GameSelfSwitches()
            self.variables = GameVariables(self.system_data['variables'])

        def do_next_thing(self, mapdest):
            if self.event:
                self.event.do_next_thing()
                if self.event.done():
                    if self.event.new_map_id:
                        self.map = GameMap(self, self.event.new_map_id, self.event.new_x, self.event.new_y)
                    self.event = None
                return True

            if not self.ran_auto_trigger_events:
                self.event = self.map.find_auto_trigger_event()
                self.ran_auto_trigger_events = True
                return True

            if mapdest:
                self.event = self.map.find_event_for_location(mapdest[0], mapdest[1])
                renpy.say(None, "%d,%d" % mapdest)
                return True

            coordinates = self.map.map_options()
            renpy.call_screen("mapscreen", coords=coordinates)

define mapdest = None

screen mapscreen:
    for i, coord in enumerate(coords):
        button:
            xpos (coord[0] / 80.0)
            xsize 10
            ypos (coord[1] / 64.0)
            ysize 10
            background "#f00"
            hover_background "#00f"
            action SetVariable("mapdest", coord), Jump("game")

label start:
    python:
        game_state = GameState()

label game:
    $ end_game = False

    while end_game == False:
        $ game_state.do_next_thing(mapdest)
        $ mapdest = None

    return