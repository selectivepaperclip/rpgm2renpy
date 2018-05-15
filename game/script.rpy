define debug_events = False

init python:
    import json

    for ix in range(0, 16 + 1):
        renpy.image("Intro %i" % ix, "unpacked/www/img/pictures/Intro %i.png" % ix)

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
            for key, value in self.switch_values.iteritems():
                print "%s: %s" % (key ,value)

    class GameSwitches:
        def __init__(self, switch_names):
            self.switch_names = switch_names
            self.switch_values = [0] * len(switch_names)

        def value(self, switch_id):
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

        def print_values(self):
            longest_string = len(max(self.variable_names, key=len))

            for i in xrange(0, len(self.variable_names)):
                print ("%3s: '%" + str(longest_string) + "s' = %s") % (i, self.variable_names[i], self.variable_values[i])

    class GameItems:
        def __init__(self):
            with renpy.file('unpacked/www/data/Items.json') as f:
                self.data = [item for item in json.load(f) if item]

        def by_id(self, id):
            for item in self.data:
                if item['id'] == id:
                    return item
            return None

    class GameActors:
        def __init__(self):
            with renpy.file('unpacked/www/data/Actors.json') as f:
                self.data = [actor for actor in json.load(f) if actor]

            self.data[1]['name'] = "MCName"

        def by_index(self, index):
            return self.data[index]

    class GameParty:
        def __init__(self):
            self.members = []

        def has_item(self, item):
            False

        def members(self):
            self.members

        def has_actor(self, actor):
            False

    class GameEvent:
        def __init__(self, state, event_data, page):
            self.state = state
            self.event_data = event_data
            self.page = page
            self.list_index = 0
            self.new_map_id = None
            self.x = None
            self.y = None

        def do_next_thing(self):
            if not self.done():
                list_item = self.page['list'][self.list_index]

                # Show text
                if list_item['code'] == 101:
                    accumulated_text = []
                    while len(self.page['list']) > self.list_index + 1 and self.page['list'][self.list_index + 1]['code'] == 401:
                        self.list_index += 1
                        list_item = self.page['list'][self.list_index]
                        text = list_item['parameters'][0]
                        text = text.replace("\\N[1]", self.state.actors.by_index(1)['name'])
                        accumulated_text.append(text)

                    renpy.say(None, "\n".join(accumulated_text))
                # Transfer maps
                elif list_item['code'] == 201:
                    method, self.new_map_id, self.new_x, self.new_y = list_item['parameters'][0:4]
                    if debug_events:
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
            return self.list_index == len(self.page['list'])

    class GameMap:
        def __init__(self, state, map_id, x, y):
            self.state = state
            self.map_id = map_id
            self.x = x
            self.y = y
            with renpy.file("unpacked/www/data/Map%03d.json" % map_id) as f:
                self.data = json.load(f)

        def find_event_for_location(self, x, y):
            for e in self.data['events']:
                if e and e['x'] == x and e['y'] == y:
                    for index, page in enumerate(reversed(e['pages'])):
                        if self.meets_conditions(e, page['conditions']) and page['trigger'] != 3:
                            if debug_events:
                                renpy.say(None, "page -%s" % index)
                            return GameEvent(self.state, e, page)
            return None

        def find_auto_trigger_event(self):
            for e in self.data['events']:
                if e:
                    for page in reversed(e['pages']):
                        if page['trigger'] == 3:
                            return GameEvent(self.state, e, page)
            return None

        def meets_conditions(self, event_data, conditions):
            if conditions['switch1Valid']:
                if not self.state.switches.value(conditions['switch1Id']):
                    return False

            if conditions['switch2Valid']:
                if not self.state.switches.value(conditions['switch2Id']):
                    return False

            if conditions['variableValid']:
                if self.state.variables.value(conditions['variableId']) < conditions['variableValue']:
                    return False

            if conditions['selfSwitchValid']:
                key = (self.state.map.map_id, event_data['id'], conditions['selfSwitchCh'])
                if self.state.self_switches.value(key) != True:
                    return False

            if conditions['itemValid']:
                item = self.state.items.by_id(conditions['itemId'])
                if not self.state.party.has_item(item):
                    return False

            if conditions['actorValid']:
                actor = self.state.actors.by_id(conditions['actorId'])
                if not self.state.party.has_actor(actor):
                    return False

            return True

        def has_commands(self, page):
            for list_item in page['list']:
                if list_item['code'] != 0:
                    return True
            return False

        def map_options(self):
            coords = []
            for e in self.data['events']:
                if e:
                    for page in reversed(e['pages']):
                        if page['trigger'] != 3 and self.meets_conditions(e, page['conditions']):
                            if self.has_commands(page):
                                coords.append((e['x'], e['y']))
                            break

            return coords

    class GameState:
        def __init__(self):
            with renpy.file('unpacked/www/data/System.json') as f:
                self.system_data = json.load(f)

            with renpy.file('unpacked/www/data/CommonEvents.json') as f:
                self.common_events_data = json.load(f)

            self.common_events_index = 1
            self.event = None
            self.starting_map_id = self.system_data['startMapId']
            self.ran_auto_trigger_events = False
            self.map = GameMap(self, self.starting_map_id, self.system_data['startX'], self.system_data['startY'])
            self.switches = GameSwitches(self.system_data['switches'])
            self.self_switches = GameSelfSwitches()
            self.variables = GameVariables(self.system_data['variables'])
            self.party = GameParty()
            self.actors = GameActors()
            self.items = GameItems()

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

            if self.common_events_index < len(self.common_events_data):
                for event in xrange(self.common_events_index, len(self.common_events_data)):
                    common_event = self.common_events_data[self.common_events_index]
                    self.common_events_index += 1
                    if common_event['trigger'] == 2:
                        self.event = GameEvent(self, common_event, common_event)
                        return True

            if mapdest:
                self.event = self.map.find_event_for_location(mapdest[0], mapdest[1])
                if debug_events:
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