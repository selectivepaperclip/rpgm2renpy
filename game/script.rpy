﻿# TODOS:

# read and show map names out of MapInfos.json
# try to draw impassible areas to get some idea of map shape
# show characters on the map
# probably CommonEvents isn't really working. this controls the time system
# can't return from far-left screen

define debug_events = False

init python:
    import json

    for filename in renpy.list_files():
        if filename.startswith("unpacked/www/img/pictures/"):
            image_name = filename.replace("unpacked/www/img/pictures/", "").split(".")[0]
            if renpy.has_image(image_name, exact=True):
                continue

            renpy.image(image_name, filename)

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
            # TODO: doesn't account for weapons and armor items
            self.members = []
            self.items = {}

        def has_item(self, item):
            return self.items.get(item['id'], 0) > 0

        def gain_item(self, item, amount):
            existing_value = self.items.get(item['id'], 0)
            self.items[item['id']] = max(0, min(existing_value + amount, 99))
            if self.items[item['id']] == 0:
                del self.items[item['id']]

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

        def conditional_branch_result(self, params):
            operation = params[0]
            # Switches
            if operation == 0:
                return self.state.switches.value(params[1]) == (params[2] == 0)
            # Variable
            elif operation == 1:
                value1 = self.state.variables.value(params[1]);
                value2 = None
                if params[2] == 0:
                    value2 = params[3];
                else:
                    value2 = self.state.variables.value(params[3]);

                if params[4] == 0:
                    return value1 == value2
                elif params[4] == 1:
                    return value1 >= value2
                elif params[4] == 2:
                    return value1 <= value2
                elif params[4] == 3:
                    return value1 > value2
                elif params[4] == 4:
                    return value1 < value2
                elif params[4] == 5:
                    return value1 != value2

            # Self Switches
            elif operation == 2:
                if this.state.event:
                    key = (self.state.map.map_id, event_data['id'], params[1])
                    return self.state.self_switches.value(key) == (params[2] == 0)
            # Timer
            elif operation == 3:
                renpy.say(None, "Conditional statements for Timer not implemented")
                return False
                #if ($gameTimer.isWorking()) {
                #    if (this._params[2] === 0) {
                #        result = ($gameTimer.seconds() >= this._params[1]);
                #    } else {
                #        result = ($gameTimer.seconds() <= this._params[1]);
                #    }
                #}
            # Actor
            elif operation == 4:
                renpy.say(None, "Conditional statements for Actor not implemented")
                return False
                #var actor = $gameActors.actor(this._params[1]);
                #if (actor) {
                #    var n = this._params[3];
                #    switch (this._params[2]) {
                #    case 0:  // In the Party
                #        result = $gameParty.members().contains(actor);
                #        break;
                #    case 1:  // Name
                #        result = (actor.name() === n);
                #        break;
                #    case 2:  // Class
                #        result = actor.isClass($dataClasses[n]);
                #        break;
                #    case 3:  // Skill
                #        result = actor.isLearnedSkill(n);
                #        break;
                #    case 4:  // Weapon
                #        result = actor.hasWeapon($dataWeapons[n]);
                #        break;
                #    case 5:  // Armor
                #        result = actor.hasArmor($dataArmors[n]);
                #        break;
                #    case 6:  // State
                #        result = actor.isStateAffected(n);
                #        break;
                #    }
                #}
            # Enemy
            elif operation == 5:
                renpy.say(None, "Conditional statements for Enemy not implemented")
                return False
                #var enemy = $gameTroop.members()[this._params[1]];
                #if (enemy) {
                #    switch (this._params[2]) {
                #    case 0:  // Appeared
                #        result = enemy.isAlive();
                #        break;
                #    case 1:  // State
                #        result = enemy.isStateAffected(this._params[3]);
                #        break;
                #    }
                #}
            # Character
            elif operation == 6:
                renpy.say(None, "Conditional statements for Character not implemented")
                return False
                #var character = this.character(this._params[1]);
                #if (character) {
                #    result = (character.direction() === this._params[2]);
                #}
            # Gold
            elif operation == 7:
                renpy.say(None, "Conditional statements for Gold not implemented")
                return False
                #switch (this._params[2]) {
                #case 0:  // Greater than or equal to
                #    result = ($gameParty.gold() >= this._params[1]);
                #    break;
                #case 1:  // Less than or equal to
                #    result = ($gameParty.gold() <= this._params[1]);
                #    break;
                #case 2:  // Less than
                #    result = ($gameParty.gold() < this._params[1]);
                #    break;
                #}
            # Item
            elif operation == 8:
                return self.state.party.has_item(self.state.items.by_id(params[1]))
            # Weapon
            elif operation == 9:
                renpy.say(None, "Conditional statements for Weapon not implemented")
                return False
                #result = $gameParty.hasItem($dataWeapons[this._params[1]], this._params[2]);
            # Armor
            elif operation == 10:
                renpy.say(None, "Conditional statements for Armor not implemented")
                return False
                #result = $gameParty.hasItem($dataArmors[this._params[1]], this._params[2]);
            # Button
            elif operation == 11:
                renpy.say(None, "Conditional statements for Button not implemented")
                return False
                #result = Input.isPressed(this._params[1]);
            # Script
            elif operation == 12:
                renpy.say(None, "Conditional statements for Script not implemented")
                return False
                #result = !!eval(this._params[1]);
            # Vehicle
            elif operation == 13:
                renpy.say(None, "Conditional statements for Vehicle not implemented")
                return False
                #result = ($gamePlayer.vehicle() === $gameMap.vehicle(this._params[1]));
            else:
                renpy.say(None, "Unknown operation %s" % operation)
                return False

        def skip_branch(self, current_indent):
            while self.page['list'][self.list_index + 1]['indent'] > current_indent:
                self.list_index += 1

        def jump_to(self, index, current_indent):
            current_index = self.list_index
            start_index = min(index, current_index)
            end_index = max(index, current_index)
            indent = current_indent
            for i in xrange(start_index, end_index + 1):
                new_indent = self.page['list'][i]['indent'];
                if new_indent != indent:
                    self.state.branch[indent] = None
                    indent = new_indent
            self.list_index = index


        def do_next_thing(self):
            if not self.done():
                list_item = self.page['list'][self.list_index]

                # Do nothing
                if list_item['code'] == 0:
                    pass

                # Show text
                elif list_item['code'] == 101:
                    accumulated_text = []
                    while len(self.page['list']) > self.list_index + 1 and self.page['list'][self.list_index + 1]['code'] == 401:
                        self.list_index += 1
                        list_item = self.page['list'][self.list_index]
                        text = list_item['parameters'][0]
                        text = text.replace("\\N[1]", self.state.actors.by_index(1)['name'])
                        accumulated_text.append(text)

                    renpy.say(None, "\n".join(accumulated_text))

                # Show choices
                elif list_item['code'] == 102:
                    choice_texts = list_item['parameters'][0]
                    cancel_type = list_item['parameters'][1]
                    if cancel_type >= len(choice_texts):
                        cancel_type = -2
                    result = renpy.display_menu([(text, index) for index, text in enumerate(choice_texts)])
                    self.state.branch[list_item['indent']] = result

                # Comment
                elif list_item['code'] == 108:
                    pass

                # Conditional branch
                elif list_item['code'] == 111:
                    branch_result = self.conditional_branch_result(list_item['parameters'])
                    self.state.branch[list_item['indent']] = branch_result
                    if not branch_result:
                        self.skip_branch(list_item['indent'])

                # Label
                elif list_item['code'] == 118:
                    pass

                # Jump to Label
                elif list_item['code'] == 119:
                    label_name = list_item['parameters'][0]
                    for index, other_list_item in enumerate(self.page['list']):
                        if other_list_item['code'] == 118 and other_list_item['parameters'][0] == label_name:
                            self.jump_to(index, current_indent = list_item['indent']);

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
                        value = this.state.variables.value(list_item['parameters'][4])
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

                # Change items
                elif list_item['code'] == 126:
                    item_id, operation, operand_type, operand = list_item['parameters']
                    value = self.state.variables.operate_value(operation, operand_type, operand)
                    self.state.party.gain_item(self.state.items.by_id(item_id), value)

                # Toggle menu access
                elif list_item['code'] == 135:
                    pass

                # Transfer maps
                elif list_item['code'] == 201:
                    method, self.new_map_id, self.new_x, self.new_y = list_item['parameters'][0:4]
                    if debug_events:
                        renpy.say(None, "Map %d" % self.new_map_id)
                    if method != 0:
                        renpy.say(None, "Method on transfer was nonzero (%d), plz implement!" % method)

                # Set movement route
                elif list_item['code'] == 205:
                    pass

                # Fade in/out/shake/etc
                elif list_item['code'] in [221, 222, 223, 224, 225]:
                    pass

                # Pause
                elif list_item['code'] == 230:
                    renpy.pause()

                # Show picture
                elif list_item['code'] == 231:
                    renpy.scene()
                    renpy.show(list_item['parameters'][1])

                # Erase picture
                elif list_item['code'] == 235:
                    renpy.scene()

                # Audio
                elif list_item['code'] in [241, 242, 243, 244, 245, 246, 249, 250, 251]:
                    pass

                # Get actor name
                elif list_item['code'] == 303:
                    actor_index = list_item['parameters'][0]
                    actor = self.state.actors.by_index(actor_index)
                    actor['name'] = renpy.input("What name should actor %d have?" % actor_index)

                # Change actor image
                elif list_item['code'] == 322:
                    pass

                # 'Script'
                elif list_item['code'] == 355:
                    if len(list_item['parameters']) == 1 and 'ImageManager' in list_item['parameters'][0]:
                        pass
                    else:
                        renpy.say(None, "Code 355 not implemented to eval '%s'" % list_item['parameters'][0])
                # Additional lines for script
                elif list_item['code'] == 655:
                    pass

                # 'Plugin'
                elif list_item['code'] == 356:
                    pass


                # When [**]
                elif list_item['code'] == 402:
                    if self.state.branch[list_item['indent']] != list_item['parameters'][0]:
                        self.skip_branch(list_item['indent'])

                # When Cancel
                elif list_item['code'] == 403:
                    if self.state.branch[list_item['indent']] >= 0:
                        self.skip_branch(list_item['indent'])

                # TODO: unknown
                elif list_item['code'] == 404:
                    pass

                # Some mouse hover thingie
                elif list_item['code'] == 408:
                    pass

                # Seems unimplemented?
                elif list_item['code'] == 412:
                    pass

                # TODO: Unknown
                elif list_item['code'] == 505:
                    pass

                else:
                    renpy.say(None, "Code %d not implemented, plz fix." % list_item['code'])

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

        def impassible_tiles(self):
            result = []
            direction_bits = [1, 2, 4, 8]
            width = self.data['width']
            height = self.data['height']
            for x in xrange(0, width):
                for y in xrange(0, height):
                    tile_ids = [self.data['data'][(z * height + y) * width + x] for z in xrange(0, 4)]
                    for tile_id in tile_ids:
                        flag = self.state.tilesets[self.data['tilesetId']]['flags'][tile_id]
                        if any([(flag & direction_bit) == direction_bit for direction_bit in direction_bits]):
                            result.append((x, y))
                            break

            return result

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
                actor = self.state.actors.by_index(conditions['actorId'])
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

            with renpy.file('unpacked/www/data/Tilesets.json') as f:
                self.tilesets = json.load(f)

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
            self.branch = {}

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
            renpy.call_screen(
                "mapscreen",
                coords=coordinates,
                impassible_tiles=self.map.impassible_tiles(),
                width=float(self.map.data['width']),
                height=float(self.map.data['height']),
                tile_width_px=int(config.screen_width / float(self.map.data['width'])),
                tile_height_px=int(config.screen_height / float(self.map.data['height']))
            )

define mapdest = None

screen mapscreen:
    for coord in impassible_tiles:
        button:
            xpos (coord[0] / width)
            xsize tile_width_px
            ypos (coord[1] / height)
            ysize tile_height_px
            background "#0f0"

    for i, coord in enumerate(coords):
        button:
            xpos (coord[0] / width)
            xsize tile_width_px
            ypos (coord[1] / height)
            ysize tile_height_px
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