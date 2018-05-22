# TODOS:

# read and show map names out of MapInfos.json
# show tiles on the map
# show characters on the map
# combine lines better ('needed her the most')
# reloading immediately after start is re-asking name ... some checkpointing problem seemingly
# implement the phone?!

define debug_events = False

init python:
    import json

    for filename in renpy.list_files():
        if filename.startswith("unpacked/www/img/pictures/"):
            image_name = filename.replace("unpacked/www/img/pictures/", "").split(".")[0]
            if renpy.has_image(image_name, exact=True):
                continue

            renpy.image(image_name, filename)

        if filename.startswith("unpacked/www/movies/"):
            image_name = filename.replace("unpacked/www/movies/", "").split(".")[0]
            if renpy.has_image(image_name, exact=True):
                continue

            renpy.image(image_name, Movie(play=filename))

        if filename.startswith("unpacked/www/img/tilesets/"):
            image_name = filename.replace("unpacked/www/img/tilesets/", "").split(".")[0]
            if renpy.has_image(image_name, exact=True):
                continue

            renpy.image(image_name, filename)

    class ObjectWithJson:
        def __getstate__(self):
            return dict((k, v) for k, v in self.__dict__.iteritems() if not k.startswith('_'))

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
            old_value = self.value(variable_id)
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

    class GameItems(ObjectWithJson):
        def __init__(self):
            pass

        def data(self):
            if not hasattr(self, '_data'):
                with renpy.file('unpacked/www/data/Items.json') as f:
                    self._data = json.load(f)

            return self._data

        def by_id(self, id):
            for item in self.data():
                if item and item['id'] == id:
                    return item
            return None

    class GameActors(ObjectWithJson):
        def __init__(self):
            self.overrides = {
                1: {
                    "name": "MCName"
                }
            }

        def __setstate__(self, d):
            self.__dict__.update(d)
            self.overrides = {}

        def data(self):
            if not hasattr(self, '_data'):
                with renpy.file('unpacked/www/data/Actors.json') as f:
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

    class GameParty(ObjectWithJson):
        def __init__(self):
            # TODO: doesn't account for weapons and armor items
            self.members = [1]
            self.items = {}

        def has_item(self, item):
            return self.items.get(item['id'], 0) > 0

        def gain_item(self, item, amount):
            existing_value = self.items.get(item['id'], 0)
            self.items[item['id']] = max(0, min(existing_value + amount, 99))
            if self.items[item['id']] == 0:
                del self.items[item['id']]

        def add_actor(self, actor_index):
            if actor_index not in self.members:
                self.members.append(actor_index)

        def remove_actor(self, actor_index):
            if actor_index in self.members:
                self.members.remove(actor_index)

        def has_actor(self, actor):
            return actor['id'] in self.members

    class GameEvent:
        def __init__(self, state, event_data, page):
            self.state = state
            self.event_data = event_data
            self.page = page
            self.list_index = 0
            self.new_map_id = None
            self.x = None
            self.y = None

        def common(self):
            return self.event_data.has_key('switchId')

        def conditional_branch_result(self, params):
            operation = params[0]
            # Switches
            if operation == 0:
                return self.state.switches.value(params[1]) == (params[2] == 0)
            # Variable
            elif operation == 1:
                value1 = self.state.variables.value(params[1])
                value2 = None
                if params[2] == 0:
                    value2 = params[3]
                else:
                    value2 = self.state.variables.value(params[3])

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
                new_indent = self.page['list'][i]['indent']
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

                # Loop -- TODO: this is not good enough
                elif list_item['code'] == 112:
                    pass

                # Repeat Above
                elif list_item['code'] == 413:
                    while self.list_index > 0:
                        self.list_index -= 1
                        if self.page['list'][self.list_index]['indent'] == list_item['indent']:
                            break

                # Break Loop
                elif list_item['code'] == 113:
                    while self.list_index < len(self.page['list']) - 1:
                        self.list_index += 1
                        command = self.page['list'][self.list_index]
                        if command['code'] == 413 and command['indent'] < list_item['indent']:
                            break

                # Label
                elif list_item['code'] == 118:
                    pass

                # Jump to Label
                elif list_item['code'] == 119:
                    label_name = list_item['parameters'][0]
                    for index, other_list_item in enumerate(self.page['list']):
                        if other_list_item['code'] == 118 and other_list_item['parameters'][0] == label_name:
                            self.jump_to(index, current_indent = list_item['indent'])

                # Control Switches
                elif list_item['code'] == 121:
                    start, end, value = list_item['parameters'][0:3]
                    for i in xrange(start, end + 1):
                        self.state.switches.set_value(i, value == 0)

                # Control Variables
                elif list_item['code'] == 122:
                    start, end, operation_type, operand = list_item['parameters'][0:4]
                    value = 0
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

                # Change party members -- TODO
                elif list_item['code'] == 129:
                    actor_index = list_item['parameters'][0]
                    actor = self.state.actors.by_index(actor_index)
                    if actor:
                        if list_item['parameters'][1] == 0:
                            # Initialize actor - I don't think this is needed outside of combat, mostly
                            if list_item['parameters'][2]:
                                pass
                            self.state.party.add_actor(actor_index)
                        else:
                            self.state.party.remove_actor(actor_index)

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

                # Set event location - TODO
                elif list_item['code'] == 203:
                    pass

                # Set movement route
                elif list_item['code'] == 205:
                    # If a movement route is set on 'wait' mode, and this is
                    # a parallel (background) command, finish the current
                    # event so that nothing else afterward will run.

                    # This has the effect that the character stays at the spawn
                    # point, but ensures that if the movement is in an infinite loop
                    # Renpy doesn't loop forever.
                    if self.page['trigger'] == 4 and list_item['parameters'][1]['wait']:
                        self.list_index = len(self.page['list']) - 1

                # "Show baloon icon"
                elif list_item['code'] == 213:
                    pass

                # Fade in/out/shake/etc
                elif list_item['code'] in [221, 222, 223, 224, 225]:
                    pass

                # Pause
                elif list_item['code'] == 230:
                    # Skip to the final pause if there's a series of pauses and audio
                    fast_forwarded = False
                    while self.page['list'][self.list_index + 1]['code'] in [230, 250]:
                        fast_forwarded = True
                        self.list_index += 1
                    if fast_forwarded:
                        self.list_index -= 1
                    renpy.pause()

                # Show picture
                elif list_item['code'] == 231:
                    renpy.scene()
                    renpy.show(list_item['parameters'][1])

                # Move picture - TODO - like the first scene in the cafe in ics2
                elif list_item['code'] == 232:
                    pass

                # Erase picture
                elif list_item['code'] == 235:
                    renpy.scene()

                # Audio
                elif list_item['code'] in [241, 242, 243, 244, 245, 246, 249, 250, 251]:
                    pass

                # Play Movie
                elif list_item['code'] == 261:
                    renpy.show(list_item['parameters'][0])

                # Get actor name
                elif list_item['code'] == 303:
                    actor_index = list_item['parameters'][0]
                    actor_name = renpy.input("What name should actor %d have?" % actor_index)
                    self.state.actors.set_property(actor_index, 'name', actor_name)

                # Recover all
                elif list_item['code'] == 314:
                    pass

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

                # Else
                elif list_item['code'] == 411:
                    if self.state.branch[list_item['indent']] != False:
                        self.skip_branch(list_item['indent'])

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

    class GameTile:
        def __init__(self, x, y, sx, sy, tileset_name):
            self.x = x
            self.y = y
            self.sx = sx
            self.sy = sy
            self.tileset_name = tileset_name

    class GameMap:
        TILE_ID_B      = 0
        TILE_ID_C      = 256
        TILE_ID_D      = 512
        TILE_ID_E      = 768
        TILE_ID_A5     = 1536
        TILE_ID_A1     = 2048
        TILE_ID_A2     = 2816
        TILE_ID_A3     = 4352
        TILE_ID_A4     = 5888
        TILE_ID_MAX    = 8192

        def __init__(self, state, map_id, x, y):
            self.state = state
            self.map_id = map_id
            self.x = x
            self.y = y

        def data(self):
            if not hasattr(self, '_data'):
                with renpy.file("unpacked/www/data/Map%03d.json" % self.map_id) as f:
                    self._data = json.load(f)

            return self._data;

        def is_tile_a5(self, tile_id):
            return tile_id >= GameMap.TILE_ID_A5 and tile_id < GameMap.TILE_ID_A1;

        def impassible_tiles(self):
            result = []
            direction_bits = [1, 2, 4, 8]
            width = self.data()['width']
            height = self.data()['height']
            for x in xrange(0, width):
                for y in xrange(0, height):
                    tile_ids = [self.data()['data'][(z * height + y) * width + x] for z in xrange(0, 4)]
                    for tile_id in tile_ids:
                        flag = self.state.tilesets()[self.data()['tilesetId']]['flags'][tile_id]
                        if any([(flag & direction_bit) == direction_bit for direction_bit in direction_bits]):
                            result.append((x, y))
                            break

            return result

        def tiles(self):
            result = []
            width = self.data()['width']
            height = self.data()['height']
            for x in xrange(0, width):
                for y in xrange(0, height):
                    tile_ids = [self.data()['data'][(z * height + y) * width + x] for z in xrange(0, 4)]
                    tile_id = tile_ids[0]
                    set_number = 0
                    if self.is_tile_a5(tile_id):
                        set_number = 4
                    else:
                        set_number = 5 + tile_id // 256

                    tile_width = 48;
                    tile_height = 48;
                    sx = ((tile_id // 128) % 2 * 8 + tile_id % 8) * tile_width;
                    sy = ((tile_id % 256 // 8) % 16) * tile_height;

                    # Need to implmenet _drawAutotile
                    if set_number > 4:
                        set_number = 4
                    tileset_name = self.state.tilesets()[self.data()['tilesetId']]['tilesetNames'][set_number]

                    result.append(GameTile(x, y, sx, sy, tileset_name))
            return result

        def find_event_for_location(self, x, y):
            for e in self.data()['events']:
                if e and e['x'] == x and e['y'] == y:
                    for index, page in enumerate(reversed(e['pages'])):
                        if self.meets_conditions(e, page['conditions']) and page['trigger'] != 3:
                            if debug_events:
                                renpy.say(None, "page -%s" % index)
                            return GameEvent(self.state, e, page)
            return None

        def find_auto_trigger_event(self):
            for e in self.data()['events']:
                if e:
                    for page in reversed(e['pages']):
                        if self.meets_conditions(e, page['conditions']):
                            if page['trigger'] == 3:
                                return GameEvent(self.state, e, page)
                            else:
                                break
            return None

        def parallel_event_at_index(self, event_index):
            e = self.data()['events'][event_index]
            if e:
                for page in reversed(e['pages']):
                    if self.meets_conditions(e, page['conditions']):
                        if page['trigger'] == 4:
                            return GameEvent(self.state, e, page)
                        else:
                            break
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
            for e in self.data()['events']:
                if e:
                    for page in reversed(e['pages']):
                        if page['trigger'] < 3 and self.meets_conditions(e, page['conditions']):
                            if self.has_commands(page):
                                coords.append((e['x'], e['y']))
                            break

            return coords

    class GameState(ObjectWithJson):
        def __init__(self):
            self.common_events_index = None
            self.parallel_events_index = None
            self.event = None
            self.starting_map_id = self.system_data()['startMapId']
            self.map = GameMap(self, self.starting_map_id, self.system_data()['startX'], self.system_data()['startY'])
            self.switches = GameSwitches(self.system_data()['switches'])
            self.self_switches = GameSelfSwitches()
            self.variables = GameVariables(self.system_data()['variables'])
            self.party = GameParty()
            self.actors = GameActors()
            self.items = GameItems()
            self.branch = {}

        def system_data(self):
            if not hasattr(self, '_system_data'):
                with renpy.file('unpacked/www/data/System.json') as f:
                    self._system_data = json.load(f)

            return self._system_data

        def common_events_data(self):
            if not hasattr(self, '_common_events_data'):
                with renpy.file('unpacked/www/data/CommonEvents.json') as f:
                    self._common_events_data = json.load(f)

            return self._common_events_data

        def tilesets(self):
            if not hasattr(self, '_tilesets'):
                with renpy.file('unpacked/www/data/Tilesets.json') as f:
                    self._tilesets = json.load(f)

            return self._tilesets

        def queue_common_and_parallel_events(self):
            if len(self.common_events_data()) > 0:
                self.common_events_index = 1
            if len(self.map.data()['events']) > 0:
                self.parallel_events_index = 1

        def do_next_thing(self, mapdest):
            if self.event:
                self.event.do_next_thing()
                if self.event.done():
                    if self.event.new_map_id:
                        self.map = GameMap(self, self.event.new_map_id, self.event.new_x, self.event.new_y)
                        self.queue_common_and_parallel_events()
                    if self.common_events_index == None and self.parallel_events_index == None:
                        self.queue_common_and_parallel_events()
                    self.event = None
                return True

            if self.common_events_index != None and self.common_events_index < len(self.common_events_data()):
                for event in xrange(self.common_events_index, len(self.common_events_data())):
                    common_event = self.common_events_data()[self.common_events_index]
                    self.common_events_index += 1
                    if common_event['trigger'] > 0 and self.switches.value(common_event['switchId']) == True:
                        self.event = GameEvent(self, common_event, common_event)
                        return True
            self.common_events_index = None

            if self.parallel_events_index != None and self.parallel_events_index < len(self.map.data()['events']):
                for event in xrange(self.parallel_events_index, len(self.map.data()['events'])):
                    possible_parallel_event = self.map.parallel_event_at_index(self.parallel_events_index)
                    self.parallel_events_index += 1
                    if possible_parallel_event:
                        self.event = possible_parallel_event
                        return True
            self.parallel_events_index = None

            self.event = self.map.find_auto_trigger_event()
            if self.event:
                return True

            if mapdest:
                self.event = self.map.find_event_for_location(mapdest[0], mapdest[1])
                if debug_events:
                    renpy.say(None, "%d,%d" % mapdest)
                return True

            renpy.checkpoint()

            coordinates = self.map.map_options()
            tile_pixel_options = [
                config.screen_width / float(self.map.data()['width']),
                (config.screen_height - 20) / float(self.map.data()['height'])
            ]
            tile_pixels = int(min(tile_pixel_options))

            renpy.call_screen(
                "mapscreen",
                coords=coordinates,
                tiles=self.map.tiles(),
                width=float(self.map.data()['width']),
                height=float(self.map.data()['height']),
                x_offset=int((config.screen_width - tile_pixels * self.map.data()['width']) / 2.0),
                y_offset=int((config.screen_height - tile_pixels * self.map.data()['height']) / 2.0),
                tile_pixels=tile_pixels
            )

define mapdest = None

screen mapscreen:
    for tile in tiles:
        button:
            image tile.tileset_name:
                crop (tile.sx, tile.sy, 48, 48)
            xpos x_offset + int(tile.x * tile_pixels)
            xsize tile_pixels
            ypos y_offset + int(tile.y * tile_pixels)
            ysize tile_pixels

    for i, coord in enumerate(coords):
        button:
            xpos x_offset + int(coord[0] * tile_pixels)
            xsize tile_pixels
            ypos y_offset + int(coord[1] * tile_pixels)
            ysize tile_pixels
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