# TODOS:

# read and show map names out of MapInfos.json
# show tiles on the map
# show characters on the map
# combine lines better ('needed her the most')
# Phone: YEP_ButtonCommonEvents
# HUD: OrangeHudVariablePicture and OrangeHudLine in plugins.js
# hide_choice for phone
# is sewer grate entry allowed?
# sprite positioning is off

define debug_events = False
define tile_images = {}
define character_images = {}
define character_image_sizes = {}
define mapdest = None
define keyed_common_event = None
define draw_impassible_tiles = False
define show_inventory = None

init python:
    import json
    import math

    for filename in renpy.list_files():
        if filename.startswith("unpacked/www/img/pictures/"):
            image_name = os.path.splitext(filename.replace("unpacked/www/img/pictures/", ""))[0]
            if renpy.has_image(image_name, exact=True):
                continue

            renpy.image(image_name, filename)

        if filename.startswith("unpacked/www/movies/"):
            image_name = os.path.splitext(filename.replace("unpacked/www/movies/", ""))[0]
            if renpy.has_image(image_name, exact=True):
                continue

            renpy.image(image_name, Movie(play=filename))

        if filename.startswith("unpacked/www/img/tilesets/"):
            image_name = os.path.splitext(filename.replace("unpacked/www/img/tilesets/", ""))[0].replace(".", "_")
            if renpy.has_image(image_name, exact=True):
                continue

            tile_images[image_name] = filename
            renpy.image(image_name, filename)

        if filename.startswith("unpacked/www/img/characters/"):
            image_name = os.path.splitext(filename.replace("unpacked/www/img/characters/", ""))[0].replace(".", "_")
            if renpy.has_image(image_name, exact=True):
                continue

            character_images[image_name] = filename
            renpy.image(image_name, filename)

    class SelectivelyPickle:
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

    class GameItems(SelectivelyPickle):
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

    class GameParty(SelectivelyPickle):
        MAX_GOLD = 99999999
        MAX_ITEMS = 99

        def __init__(self):
            # TODO: doesn't account for weapons and armor items
            self.members = [1]
            self.items = {}
            self.gold = 0

        def __setstate__(self, d):
            self.__dict__.update(d)
            if not hasattr(self, 'gold'):
                self.gold = 0

        def num_items(self, item):
            return self.items.get(item['id'], 0)

        def has_item(self, item):
            return self.num_items(item) > 0

        def gain_gold(self, amount):
            self.gold = max(0, min(self.gold + amount, GameParty.MAX_GOLD))

        def lose_gold(self, amount):
            self.gold = max(0, min(self.gold - amount, GameParty.MAX_GOLD))

        def gain_item(self, item, amount):
            existing_value = self.items.get(item['id'], 0)
            self.items[item['id']] = max(0, min(existing_value + amount, GameParty.MAX_ITEMS))
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
                if len(self.state.events) > 0:
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
                value = params[1]
                gold_operation = params[2]
                if gold_operation == 0: # Greater than or equal to
                    return self.state.party.gold >= value
                elif gold_operation == 1: # Less than or equal to
                    return self.state.party.gold <= value
                elif gold_operation == 2: # Less than
                    return self.state.party.gold < value
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
                command = self.page['list'][self.list_index]

                # Do nothing
                if command['code'] == 0:
                    pass

                # Show text
                elif command['code'] == 101:
                    accumulated_text = []
                    while len(self.page['list']) > self.list_index + 1 and self.page['list'][self.list_index + 1]['code'] == 401:
                        self.list_index += 1
                        command = self.page['list'][self.list_index]
                        text = command['parameters'][0]
                        text = text.replace("\\N[1]", self.state.actors.by_index(1)['name'])
                        accumulated_text.append(text)

                    renpy.say(None, "\n".join(accumulated_text))

                # Show choices
                elif command['code'] == 102:
                    choice_texts = command['parameters'][0]
                    cancel_type = command['parameters'][1]
                    if cancel_type >= len(choice_texts):
                        cancel_type = -2
                    result = renpy.display_menu([(text, index) for index, text in enumerate(choice_texts)])
                    self.state.branch[command['indent']] = result

                # Comment
                elif command['code'] == 108:
                    pass

                # Conditional branch
                elif command['code'] == 111:
                    branch_result = self.conditional_branch_result(command['parameters'])
                    self.state.branch[command['indent']] = branch_result
                    if not branch_result:
                        self.skip_branch(command['indent'])

                # Loop -- TODO: this is not good enough
                elif command['code'] == 112:
                    pass

                # Common Event
                elif command['code'] == 117:
                    common_event = self.state.common_events_data()[command['parameters'][0]]
                    return GameEvent(self, common_event, common_event)

                # Repeat Above
                elif command['code'] == 413:
                    while self.list_index > 0:
                        self.list_index -= 1
                        if self.page['list'][self.list_index]['indent'] == command['indent']:
                            break

                # Break Loop
                elif command['code'] == 113:
                    while self.list_index < len(self.page['list']) - 1:
                        self.list_index += 1
                        command = self.page['list'][self.list_index]
                        if command['code'] == 413 and command['indent'] < command['indent']:
                            break

                # Label
                elif command['code'] == 118:
                    pass

                # Jump to Label
                elif command['code'] == 119:
                    label_name = command['parameters'][0]
                    for index, other_command in enumerate(self.page['list']):
                        if other_command['code'] == 118 and other_command['parameters'][0] == label_name:
                            self.jump_to(index, current_indent = command['indent'])

                # Control Switches
                elif command['code'] == 121:
                    start, end, value = command['parameters'][0:3]
                    for i in xrange(start, end + 1):
                        self.state.switches.set_value(i, value == 0)

                # Control Variables
                elif command['code'] == 122:
                    start, end, operation_type, operand = command['parameters'][0:4]
                    value = 0
                    if operand == 0:
                        value = command['parameters'][4]
                    elif operand == 1:
                        value = this.state.variables.value(command['parameters'][4])
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
                elif command['code'] == 123:
                    switch_id, value = command['parameters']
                    key = (self.state.map.map_id, self.state.events[-1].event_data['id'], switch_id)
                    self.state.self_switches.set_value(key, value == 0)

                # Change gold
                elif command['code'] == 125:
                    operation, operand_type, operand = command['parameters']
                    value = self.state.variables.operate_value(operation, operand_type, operand)
                    self.state.party.gain_gold(value);

                # Change items
                elif command['code'] == 126:
                    item_id, operation, operand_type, operand = command['parameters']
                    value = self.state.variables.operate_value(operation, operand_type, operand)
                    self.state.party.gain_item(self.state.items.by_id(item_id), value)

                # Change party members -- TODO
                elif command['code'] == 129:
                    actor_index = command['parameters'][0]
                    actor = self.state.actors.by_index(actor_index)
                    if actor:
                        if command['parameters'][1] == 0:
                            # Initialize actor - I don't think this is needed outside of combat, mostly
                            if command['parameters'][2]:
                                pass
                            self.state.party.add_actor(actor_index)
                        else:
                            self.state.party.remove_actor(actor_index)

                # Toggle menu access
                elif command['code'] == 135:
                    pass

                # Transfer maps
                elif command['code'] == 201:
                    method, self.new_map_id, self.new_x, self.new_y = command['parameters'][0:4]
                    if debug_events:
                        renpy.say(None, "Map %d" % self.new_map_id)
                    if method != 0:
                        renpy.say(None, "Method on transfer was nonzero (%d), plz implement!" % method)

                # Set event location - TODO
                elif command['code'] == 203:
                    pass

                # Scroll map
                elif command['code'] == 204:
                    pass

                # Set movement route
                elif command['code'] == 205:
                    # If a movement route is set on 'wait' mode, and this is
                    # a parallel (background) command, finish the current
                    # event so that nothing else afterward will run.

                    # This has the effect that the character stays at the spawn
                    # point, but ensures that if the movement is in an infinite loop
                    # Renpy doesn't loop forever.
                    if self.page['trigger'] == 4 and command['parameters'][1]['wait']:
                        self.list_index = len(self.page['list']) - 1

                # "Show baloon icon"
                elif command['code'] == 213:
                    pass

                # Fade in/out/shake/etc
                elif command['code'] in [221, 222, 223, 224, 225]:
                    pass

                # Pause
                elif command['code'] == 230:
                    # Skip to the final pause if there's a series of pauses and audio
                    fast_forwarded = False
                    while self.page['list'][self.list_index + 1]['code'] in [230, 250]:
                        fast_forwarded = True
                        self.list_index += 1
                    if fast_forwarded:
                        self.list_index -= 1
                    renpy.pause()

                # Show picture
                elif command['code'] == 231:
                    renpy.scene()
                    renpy.show(command['parameters'][1])

                # Move picture - TODO - like the first scene in the cafe in ics2
                elif command['code'] == 232:
                    pass

                # Tint picture - TODO ?
                elif command['code'] == 234:
                    pass

                # Erase picture
                elif command['code'] == 235:
                    renpy.scene()

                # Audio
                elif command['code'] in [241, 242, 243, 244, 245, 246, 249, 250, 251]:
                    pass

                # Play Movie
                elif command['code'] == 261:
                    renpy.show(command['parameters'][0])

                # Change Parallax
                elif command['code'] == 284:
                    pass

                # Battle
                elif command['code'] == 301:
                    result = renpy.display_menu([("A battle is happening!", None), ("You Win!", 0), ("You Escape!", 1), ("You Lose!", 2)])
                    self.state.branch[command['indent']] = result

                # Shop
                elif command['code'] == 302:
                    self.state.shop_params = {}
                    self.state.shop_params['goods'] = [command['parameters']]
                    self.state.shop_params['purchase_only'] = command['parameters'][4]
                    while self.page['list'][self.list_index + 1]['code'] in [605]:
                        self.list_index += 1
                        self.state.shop_params['goods'].append(self.page['list'][self.list_index]['parameters'])

                # Get actor name
                elif command['code'] == 303:
                    actor_index = command['parameters'][0]
                    actor_name = renpy.input("What name should actor %d have?" % actor_index)
                    self.state.actors.set_property(actor_index, 'name', actor_name)

                # Recover all
                elif command['code'] == 314:
                    pass

                # Change actor image
                elif command['code'] == 322:
                    pass

                # 'Script'
                elif command['code'] == 355:
                    if len(command['parameters']) == 1 and 'ImageManager' in command['parameters'][0]:
                        pass
                    else:
                        renpy.say(None, "Code 355 not implemented to eval '%s'" % command['parameters'][0])

                # On Battle Win
                elif command['code'] == 601:
                    if self.state.branch[command['indent']] != 0:
                        self.skip_branch(command['indent'])

                # On Battle Escape
                elif command['code'] == 602:
                    if self.state.branch[command['indent']] != 1:
                        self.skip_branch(command['indent'])

                # On Battle Lose
                elif command['code'] == 603:
                    if self.state.branch[command['indent']] != 2:
                        self.skip_branch(command['indent'])

                # Dunno, probably battle related?
                elif command['code'] == 604:
                    pass

                # Additional lines for script
                elif command['code'] == 655:
                    pass

                # 'Plugin'
                elif command['code'] == 356:
                    pass


                # When [**]
                elif command['code'] == 402:
                    if self.state.branch[command['indent']] != command['parameters'][0]:
                        self.skip_branch(command['indent'])

                # When Cancel
                elif command['code'] == 403:
                    if self.state.branch[command['indent']] >= 0:
                        self.skip_branch(command['indent'])

                # TODO: unknown
                elif command['code'] == 404:
                    pass

                # Some mouse hover thingie
                elif command['code'] == 408:
                    pass

                # Else
                elif command['code'] == 411:
                    if self.state.branch[command['indent']] != False:
                        self.skip_branch(command['indent'])

                # Seems unimplemented?
                elif command['code'] == 412:
                    pass

                # TODO: Unknown
                elif command['code'] == 505:
                    pass

                else:
                    renpy.say(None, "Code %d not implemented, plz fix." % command['code'])

                self.list_index += 1

        def done(self):
            return self.list_index == len(self.page['list'])

    class GameTile:
        def __init__(self, tile_id = None, sx = None, sy = None, dx = None, dy = None, w = None, h = None, set_number = None):
            self.tile_id = tile_id
            self.sx = sx
            self.sy = sy
            self.dx = dx
            self.dy = dy
            self.w = w
            self.h = h
            self.set_number = set_number

    class GameMapBackground(renpy.Displayable):
        def __init__(self, tiles, **kwargs):
            super(GameMapBackground, self).__init__(**kwargs)

            largest_x = 0
            largest_y = 0
            for tile in tiles:
                if tile.x > largest_x:
                    largest_x = tile.x
                if tile.y > largest_y:
                    largest_y = tile.y

            self.width = (largest_x + 1) * GameMap.TILE_WIDTH
            self.height = (largest_y + 1) * GameMap.TILE_HEIGHT
            self.r = renpy.Render(self.width, self.height)

            for tile in tiles:
                img = im.Crop(tile_images[tile.tileset_name.replace(".", "_")], (tile.sx, tile.sy, tile.w, tile.h))
                self.r.blit(img.render(tile.w, tile.h, 0, 0), (tile.dx + int(tile.x * GameMap.TILE_WIDTH), tile.dy + int(tile.y * GameMap.TILE_HEIGHT)))

        def render(self, width, height, st, at):
            return self.r

    class GameMap(SelectivelyPickle):
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

        FLOOR_AUTOTILE_TABLE = [
            [[2,4],[1,4],[2,3],[1,3]],[[2,0],[1,4],[2,3],[1,3]],
            [[2,4],[3,0],[2,3],[1,3]],[[2,0],[3,0],[2,3],[1,3]],
            [[2,4],[1,4],[2,3],[3,1]],[[2,0],[1,4],[2,3],[3,1]],
            [[2,4],[3,0],[2,3],[3,1]],[[2,0],[3,0],[2,3],[3,1]],
            [[2,4],[1,4],[2,1],[1,3]],[[2,0],[1,4],[2,1],[1,3]],
            [[2,4],[3,0],[2,1],[1,3]],[[2,0],[3,0],[2,1],[1,3]],
            [[2,4],[1,4],[2,1],[3,1]],[[2,0],[1,4],[2,1],[3,1]],
            [[2,4],[3,0],[2,1],[3,1]],[[2,0],[3,0],[2,1],[3,1]],
            [[0,4],[1,4],[0,3],[1,3]],[[0,4],[3,0],[0,3],[1,3]],
            [[0,4],[1,4],[0,3],[3,1]],[[0,4],[3,0],[0,3],[3,1]],
            [[2,2],[1,2],[2,3],[1,3]],[[2,2],[1,2],[2,3],[3,1]],
            [[2,2],[1,2],[2,1],[1,3]],[[2,2],[1,2],[2,1],[3,1]],
            [[2,4],[3,4],[2,3],[3,3]],[[2,4],[3,4],[2,1],[3,3]],
            [[2,0],[3,4],[2,3],[3,3]],[[2,0],[3,4],[2,1],[3,3]],
            [[2,4],[1,4],[2,5],[1,5]],[[2,0],[1,4],[2,5],[1,5]],
            [[2,4],[3,0],[2,5],[1,5]],[[2,0],[3,0],[2,5],[1,5]],
            [[0,4],[3,4],[0,3],[3,3]],[[2,2],[1,2],[2,5],[1,5]],
            [[0,2],[1,2],[0,3],[1,3]],[[0,2],[1,2],[0,3],[3,1]],
            [[2,2],[3,2],[2,3],[3,3]],[[2,2],[3,2],[2,1],[3,3]],
            [[2,4],[3,4],[2,5],[3,5]],[[2,0],[3,4],[2,5],[3,5]],
            [[0,4],[1,4],[0,5],[1,5]],[[0,4],[3,0],[0,5],[1,5]],
            [[0,2],[3,2],[0,3],[3,3]],[[0,2],[1,2],[0,5],[1,5]],
            [[0,4],[3,4],[0,5],[3,5]],[[2,2],[3,2],[2,5],[3,5]],
            [[0,2],[3,2],[0,5],[3,5]],[[0,0],[1,0],[0,1],[1,1]]
        ]

        WALL_AUTOTILE_TABLE = [
            [[2,2],[1,2],[2,1],[1,1]],[[0,2],[1,2],[0,1],[1,1]],
            [[2,0],[1,0],[2,1],[1,1]],[[0,0],[1,0],[0,1],[1,1]],
            [[2,2],[3,2],[2,1],[3,1]],[[0,2],[3,2],[0,1],[3,1]],
            [[2,0],[3,0],[2,1],[3,1]],[[0,0],[3,0],[0,1],[3,1]],
            [[2,2],[1,2],[2,3],[1,3]],[[0,2],[1,2],[0,3],[1,3]],
            [[2,0],[1,0],[2,3],[1,3]],[[0,0],[1,0],[0,3],[1,3]],
            [[2,2],[3,2],[2,3],[3,3]],[[0,2],[3,2],[0,3],[3,3]],
            [[2,0],[3,0],[2,3],[3,3]],[[0,0],[3,0],[0,3],[3,3]]
        ]

        WATERFALL_AUTOTILE_TABLE = [
            [[2,0],[1,0],[2,1],[1,1]],[[0,0],[1,0],[0,1],[1,1]],
            [[2,0],[3,0],[2,1],[3,1]],[[0,0],[3,0],[0,1],[3,1]]
        ]

        TILE_WIDTH = 48
        TILE_HEIGHT = 48

        def __init__(self, state, map_id, x, y):
            self.state = state
            self.map_id = map_id
            self.x = x
            self.y = y

        def data(self):
            if not hasattr(self, '_data'):
                with renpy.file("unpacked/www/data/Map%03d.json" % self.map_id) as f:
                    self._data = json.load(f)

            return self._data

        def background_image(self):
            if not hasattr(self, '_background_image'):
                self._background_image = self.generate_background_image()

            return self._background_image

        def generate_background_image(self):
            tiles = self.tiles()
            d = GameMapBackground(self.tiles())
            return d

        def is_tile_a1(self, tile_id):
            return tile_id >= GameMap.TILE_ID_A1 and tile_id < GameMap.TILE_ID_A2

        def is_tile_a2(self, tile_id):
            return tile_id >= GameMap.TILE_ID_A2 and tile_id < GameMap.TILE_ID_A3

        def is_tile_a3(self, tile_id):
            return tile_id >= GameMap.TILE_ID_A3 and tile_id < GameMap.TILE_ID_A4

        def is_tile_a4(self, tile_id):
            return tile_id >= GameMap.TILE_ID_A4 and tile_id < GameMap.TILE_ID_MAX

        def is_tile_a5(self, tile_id):
            return tile_id >= GameMap.TILE_ID_A5 and tile_id < GameMap.TILE_ID_A1

        def flags(self, tile_id):
            flag_data = self.state.tilesets()[self.data()['tilesetId']]['flags']
            if len(flag_data) > tile_id:
                return flag_data[tile_id]
            else:
                return 0

        def is_table_tile(self, tile_id):
            return self.is_tile_a2(tile_id) and (self.flags(tile_id) & 0x80)

        def normal_tile_data(self, tile_id):
            if self.is_tile_a5(tile_id):
                set_number = 4
            else:
                set_number = 5 + tile_id // 256

            sx = ((tile_id // 128) % 2 * 8 + tile_id % 8) * GameMap.TILE_WIDTH
            sy = ((tile_id % 256 // 8) % 16) * GameMap.TILE_HEIGHT

            return GameTile(tile_id = tile_id, sx = sx, sy = sy, dx = 0, dy = 0, w = GameMap.TILE_WIDTH, h = GameMap.TILE_HEIGHT, set_number = set_number)

        def auto_tile_data(self, tile_id):
            result = []
            autotile_table = GameMap.FLOOR_AUTOTILE_TABLE
            kind = (tile_id - GameMap.TILE_ID_A1) // 48
            shape = (tile_id - GameMap.TILE_ID_A1) % 48
            tx = kind % 8
            ty = kind // 8
            bx = 0
            by = 0
            set_number = 0
            is_table = False

            if self.is_tile_a1(tile_id):
                animation_frame = 0
                water_surface_index = [0, 1, 2, 1][animation_frame % 4];
                set_number = 0
                if kind == 0:
                    bx = water_surface_index * 2
                    by = 0;
                elif kind == 1:
                    bx = water_surface_index * 2
                    by = 3
                elif kind == 2:
                    bx = 6
                    by = 0
                elif kind == 3:
                    bx = 6
                    by = 3
                else:
                    bx = (tx // 4) * 8
                    by = ty * 6 + (tx // 2) % 2 * 3
                    if kind % 2 == 0:
                        bx += water_surface_index * 2
                    else:
                        bx += 6
                        autotile_table = Tilemap.WATERFALL_AUTOTILE_TABLE
                        by += animation_frame % 3
            elif self.is_tile_a2(tile_id):
                set_number = 1
                bx = tx * 2
                by = (ty - 2) * 3
                is_table = self.is_table_tile(tile_id)
            elif self.is_tile_a3(tile_id):
                set_number = 2
                bx = tx * 2
                by = (ty - 6) * 2
                autotile_table = GameMap.WALL_AUTOTILE_TABLE
            elif self.is_tile_a4(tile_id):
                set_number = 3
                bx = tx * 2
                by = int(math.floor((ty - 10) * 2.5 + (0.5 if ty % 2 == 1 else 0)))
                if ty % 2 == 1:
                    autotile_table = GameMap.WALL_AUTOTILE_TABLE

            table = autotile_table[shape]

            if table:
                w1 = GameMap.TILE_WIDTH // 2
                h1 = GameMap.TILE_HEIGHT // 2
                for i in xrange(0, 4):
                    qsx = table[i][0]
                    qsy = table[i][1]
                    sx1 = (bx * 2 + qsx) * w1
                    sy1 = (by * 2 + qsy) * h1
                    dx1 = (i % 2) * w1
                    dy1 = (i // 2) * h1
                    if is_table and (qsy == 1 or qsy == 5):
                        qsx2 = qsx
                        qsy2 = 3
                        if qsy == 1:
                            qsx2 = [0,3,2,1][qsx]
                        sx2 = (bx * 2 + qsx2) * w1
                        sy2 = (by * 2 + qsy2) * h1
                        result.append(GameTile(tile_id = tile_id, sx = sx2, sy = sy2, dx = dx1, dy = dy1, w = w1, h = h1, set_number = set_number))
                        dy1 += h1 // 2
                        result.append(GameTile(tile_id = tile_id, sx = sx1, sy = sy2, dx = dx1, dy = dy1, w = w1, h = h1/2, set_number = set_number))
                    else:
                        result.append(GameTile(tile_id = tile_id, sx = sx1, sy = sy1, dx = dx1, dy = dy1, w = w1, h = h1, set_number = set_number))

            return result

        def is_visible_tile(self, tile_id):
            return tile_id > 0 and tile_id < GameMap.TILE_ID_MAX

        def impassible_tiles(self):
            result = []
            direction_bits = [1, 2, 4, 8]
            width = self.data()['width']
            height = self.data()['height']
            for x in xrange(0, width):
                for y in xrange(0, height):
                    tile_ids = [self.data()['data'][(z * height + y) * width + x] for z in xrange(0, 4)]
                    for tile_id in tile_ids:
                        flag = self.flags(tile_id)
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
                    for z in xrange(0, 4):
                        tile_id = self.data()['data'][(z * height + y) * width + x]

                        if not self.is_visible_tile(tile_id):
                            continue

                        set_number = 0

                        all_tiles = []

                        # "autotiles"
                        if tile_id > GameMap.TILE_ID_A1:
                            all_tiles = self.auto_tile_data(tile_id)

                        # "normal tiles"
                        else:
                            all_tiles = [self.normal_tile_data(tile_id)]

                        for tile in all_tiles:
                            tile.x = x
                            tile.y = y
                            tileset_names = self.state.tilesets()[self.data()['tilesetId']]['tilesetNames']
                            if len(tileset_names) > tile.set_number:
                                tile.tileset_name = tileset_names[tile.set_number]

                                result.append(tile)
            return result

        def sprites(self):
            result = []
            for e in self.data()['events']:
                if e:
                    for page in reversed(e['pages']):
                        if self.meets_conditions(e, page['conditions']):
                            image_data = page['image']
                            if image_data['characterName'] != '':
                                if image_data['tileId'] > 0:
                                    renpy.say(None, 'tileId in image not supported!')

                                img_base_filename = image_data['characterName'].replace(".", "_")

                                if not img_base_filename in character_image_sizes:
                                    character_image_sizes[img_base_filename] = renpy.image_size(character_images[img_base_filename])
                                img_size = character_image_sizes[img_base_filename]

                                pw = img_size[0] / 12
                                ph = img_size[1] / 8
                                n = image_data['characterIndex']
                                sx = (n % 4 * 3 + 1) * pw
                                sy = ((n // 4) * 4) * ph

                                img = im.Crop(character_images[img_base_filename], (sx, sy, GameMap.TILE_WIDTH, GameMap.TILE_HEIGHT))

                                result.append((e['x'], e['y'], img))
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
            for command in page['list']:
                if command['code'] != 0:
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

    class GameMapRegistry:
        def __init__(self, state):
            self.state = state
            self.maps = {}

        def get_map(self, map_id, x, y):
            if not map_id in self.maps:
                self.maps[map_id] = GameMap(self.state, map_id, x, y)

            return self.maps[map_id]

    class GameState(SelectivelyPickle):
        def __init__(self):
            self.common_events_index = None
            self.parallel_events_index = None
            self.events = []
            self.starting_map_id = self.system_data()['startMapId']
            self.map_registry = GameMapRegistry(self)
            self.map = self.map_registry.get_map(self.starting_map_id, self.system_data()['startX'], self.system_data()['startY'])
            self.switches = GameSwitches(self.system_data()['switches'])
            self.self_switches = GameSelfSwitches()
            self.variables = GameVariables(self.system_data()['variables'])
            self.party = GameParty()
            self.actors = GameActors()
            self.items = GameItems()
            self.branch = {}

        def __setstate__(self, d):
            self.__dict__.update(d)
            if not hasattr(self, 'events'):
                self.events = [event for event in [self.event] if event]

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

        def plugins(self):
            if not hasattr(self, '_plugins'):
                with renpy.file('unpacked/www/js/plugins.js') as f:
                    # the plugins.js file starts with "var $plugins = ["
                    # the '[' should be on line 4
                    content = "".join(f.readlines()[3:-1])
                    print content
                    self._plugins = json.loads(content)

            return self._plugins

        def common_events_keymap(self):
            if self.system_data()['gameTitle'] == 'Incest Story 2 v1.0 Final':
                return [('p', 4)]
            else:
                return []

            plugins = self.plugins()
            yepp_common_events = next(plugin_data for plugin_data in plugins if plugin_data['name'] == 'YEP_ButtonCommonEvents')
            print yepp_common_events
            if not yepp_common_events:
                return []

            result = []
            for key_desc, event_str in yepp_common_events:
                if event_str != "" and event_str != "0":
                    print key_desc
                    result.append((key_desc, event_str))
            return result

        def queue_common_and_parallel_events(self):
            if len(self.common_events_data()) > 0:
                self.common_events_index = 1
            if len(self.map.data()['events']) > 0:
                self.parallel_events_index = 1

        def show_shop_ui(self):
            shop_params = self.shop_params
            self.shop_params = None
            shop_items = []
            for item_params in shop_params['goods']:
                type, item_id, where_is_price, price_override = item_params[0:4]
                if type != 0:
                    renpy.say(None, "Purchasing item type %s is not supported!")
                item = self.items.by_id(item_id)
                if item:
                    if where_is_price != 0:
                        item = item.copy()
                        item['price'] = price_override
                    shop_items.append(item)
            renpy.call_screen(
                "shopscreen",
                shop_items = shop_items,
                purchase_only = shop_params['purchase_only']
            )

        def do_next_thing(self, mapdest, keyed_common_event, show_inventory):
            if len(self.events) > 0:
                this_event = self.events[-1]
                new_event = this_event.do_next_thing()
                if new_event:
                    self.events.append(new_event)
                    return True
                if hasattr(self, 'shop_params') and self.shop_params:
                    self.show_shop_ui()
                    return True
                if this_event.done():
                    if this_event.new_map_id:
                        self.map = self.map_registry.get_map(this_event.new_map_id, this_event.new_x, this_event.new_y)
                        self.queue_common_and_parallel_events()
                    if self.common_events_index == None and self.parallel_events_index == None:
                        self.queue_common_and_parallel_events()
                    self.events.pop()
                return True

            if self.common_events_index != None and self.common_events_index < len(self.common_events_data()):
                for event in xrange(self.common_events_index, len(self.common_events_data())):
                    common_event = self.common_events_data()[self.common_events_index]
                    self.common_events_index += 1
                    if common_event['trigger'] > 0 and self.switches.value(common_event['switchId']) == True:
                        self.events.append(GameEvent(self, common_event, common_event))
                        return True
            self.common_events_index = None

            if self.parallel_events_index != None and self.parallel_events_index < len(self.map.data()['events']):
                for event in xrange(self.parallel_events_index, len(self.map.data()['events'])):
                    possible_parallel_event = self.map.parallel_event_at_index(self.parallel_events_index)
                    self.parallel_events_index += 1
                    if possible_parallel_event:
                        self.events.append(possible_parallel_event)
                        return True
            self.parallel_events_index = None

            self.events = [e for e in [self.map.find_auto_trigger_event()] if e]
            if len(self.events) > 0:
                return True

            if keyed_common_event:
                common_event = self.common_events_data()[int(keyed_common_event)]
                self.events.append(GameEvent(self, common_event, common_event))
                return True

            if mapdest:
                self.events.append(self.map.find_event_for_location(mapdest[0], mapdest[1]))
                if debug_events:
                    renpy.say(None, "%d,%d" % mapdest)
                return True

            if show_inventory:
                interesting_items = []
                for item_id in self.party.items.keys():
                    item = self.items.by_id(item_id)
                    if item['effects'] and len(item['effects']) > 0:
                        common_event_effects = [effect for effect in item['effects'] if effect['code'] == 44]
                        if len(common_event_effects) > 0:
                            if len(common_event_effects) > 1:
                                renpy.say(None, "Items with more than one common event effect not supported!")
                            interesting_items.append(item)

                if len(interesting_items) == 0:
                    return True

                result = renpy.display_menu([(item['name'], item) for item in interesting_items])
                common_event_effects = [effect for effect in result['effects'] if effect['code'] == 44]
                effect = common_event_effects[0]
                common_event = self.common_events_data()[int(effect['dataId'])]
                self.events.append(GameEvent(self, common_event, common_event))
                return True

            renpy.checkpoint()

            coordinates = self.map.map_options()

            background_image = self.map.background_image()

            map_width = background_image.width + 50
            map_height = background_image.height + 50

            width_ratio = config.screen_width / float(map_width)
            height_ratio = config.screen_height / float(map_height)

            x_offset = 0
            y_offset = 0
            mapfactor = 1

            if width_ratio > 1:
                x_offset = (config.screen_width - map_width) // 2
                if height_ratio > 1:
                    # Image smaller than screen, show in native size
                    mapfactor = 1
                else:
                    # Image too tall, shrink to fit
                    mapfactor = float(config.screen_height) / map_height
            else:
                if height_ratio > 1:
                    # Image too wide, shrink to fit
                    mapfactor = float(config.screen_width) / map_width
                else:
                    # Image overflowing in both dimensions
                    if width_ratio > height_ratio:
                        # Overflowing more on height
                        mapfactor = float(config.screen_height) / map_height
                    else:
                        # Overflowing more on width
                        mapfactor = float(config.screen_width) / map_width

            if draw_impassible_tiles:
                impassible_tiles=self.map.impassible_tiles()
            else:
                impassible_tiles = []

            renpy.call_screen(
                "mapscreen",
                mapfactor=mapfactor,
                coords=coordinates,
                sprites=self.map.sprites(),
                impassible_tiles=impassible_tiles,
                common_events_keymap=self.common_events_keymap(),
                background_image=background_image,
                width=float(self.map.data()['width']),
                height=float(self.map.data()['height']),
                x_offset=x_offset,
                y_offset=y_offset
            )

transform mapzoom(mapfactor):
    zoom mapfactor

screen shopscreen(shop_items = None, purchase_only = None):
    zorder 1
    frame:
        xalign 0.1
        yalign 0.23
        background Color("#f00", alpha = 0.75)

        vbox:
            textbutton "Leave":
                background "#f00"
                hover_background "#00f"
                action Hide("shopscreen"), Jump("game")
                xalign 1.0

            text "Money: %s" % game_state.party.gold

            null height 10

            grid 3 len(shop_items):
                for item in shop_items:
                    textbutton item['name']
                    textbutton "Own %s" % game_state.party.num_items(item)
                    textbutton ("Buy (%s)" % item['price']):
                        sensitive (game_state.party.gold >= item['price'])
                        action [
                            Function(game_state.party.gain_item, item, 1),
                            Function(game_state.party.lose_gold, item['price'])
                        ]

screen mapscreen(coords = None, mapfactor = None, sprites = None, impassible_tiles = None, common_events_keymap = None, background_image = None, width = None, height = None, x_offset = None, y_offset = None):
    #key "viewport_wheelup" action [
    #    SetVariable('mapfactor', mapfactor * 1.5),
    #    renpy.restart_interaction
    #]
    #key "viewport_wheeldown" action [
    #    SetVariable('mapfactor', mapfactor * 0.66),
    #    renpy.restart_interaction
    #]

    key 'i':
        action SetVariable("show_inventory", True), Jump("game")

    for key_str, event_id in common_events_keymap:
        key key_str:
            action SetVariable("keyed_common_event", event_id), Jump("game")

    viewport:
        child_size (width * GameMap.TILE_WIDTH, height * GameMap.TILE_HEIGHT)
        mousewheel True
        draggable True
        scrollbars True
        fixed at mapzoom(mapfactor):
            add background_image:
                xpos x_offset
                ypos y_offset

            for coord in impassible_tiles:
                button:
                    xpos x_offset + int(coord[0] * GameMap.TILE_WIDTH)
                    xsize GameMap.TILE_WIDTH
                    ypos y_offset + int(coord[1] * GameMap.TILE_HEIGHT)
                    ysize GameMap.TILE_HEIGHT
                    background "#0f0"

            for x, y, img in sprites:
                button:
                    xpos x_offset + int(x * GameMap.TILE_WIDTH)
                    xsize GameMap.TILE_WIDTH
                    ypos y_offset + int(y * GameMap.TILE_HEIGHT)
                    ysize GameMap.TILE_HEIGHT
                    add img

            for i, coord in enumerate(coords):
                button:
                    xpos x_offset + int(coord[0] * GameMap.TILE_WIDTH)
                    xsize GameMap.TILE_WIDTH
                    ypos y_offset + int(coord[1] * GameMap.TILE_HEIGHT)
                    ysize GameMap.TILE_HEIGHT
                    background Color("#f00", alpha = 0.75)
                    hover_background "#00f"
                    action SetVariable("mapdest", coord), Jump("game")


label start:
    python:
        game_state = GameState()

label game:
    $ end_game = False

    while end_game == False:
        $ game_state.do_next_thing(mapdest, keyed_common_event, show_inventory)
        $ mapdest = None
        $ keyed_common_event = None
        $ show_inventory = None

    return