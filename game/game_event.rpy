init python:
    class GameEvent:
        def __init__(self, state, event_data, page):
            self.state = state
            self.event_data = event_data
            self.page = page
            self.list_index = 0
            self.new_map_id = None
            self.choices_to_hide = []

        def common(self):
            return self.event_data.has_key('switchId')

        def parallel(self):
            return self.page['trigger'] == 4

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

        def replace_names(self, text):
            # Replace statements from actor numbers, e.g. \N[2] with their actor name
            text = re.sub(r'\\N\[(\d+)\]', lambda m: self.state.actors.by_index(int(m.group(1)))['name'], text, flags=re.IGNORECASE)
            # Replace statements from literal strings, e.g. \n<Doug> with that string followed by a colon
            text = re.sub(r'\\n\<(.*?)\>', lambda m: ("%s: " % m.group(1)), text)
            # Remove statements with image replacements, e.g. \I[314]
            text = re.sub(r'\\I\[(\d+)\]', '', text, flags=re.IGNORECASE)
            # Remove font size increase statements, e.g. \{
            text = re.sub(r'\\{', '', text)
            return text

        def hide_choice(self, choice_id):
            if not hasattr(self, 'choices_to_hide'):
                self.choices_to_hide = []
            self.choices_to_hide.append(choice_id)

        def eval_script(self, command):
            script_string = command['parameters'][0]

            if len(command['parameters']) != 1:
                renpy.say(None, "More than one parameter in script eval starting with '%s'" % script_string)
                return

            hide_choice_command = re.match("hide_choice\((\d+), \"\$gameSwitches.value\((\d+)\) === (\w+)\"\)", script_string)
            if len(command['parameters']) == 1 and 'ImageManager' in script_string:
                pass
            elif hide_choice_command:
                groups = hide_choice_command.groups()
                choice_id, switch_id, switch_value = (int(groups[0]), int(groups[1]), groups[2] == 'true')
                if self.state.switches.value(switch_id) == switch_value:
                    self.hide_choice(choice_id)
            elif script_string == 'SceneManager.push(Scene_Menu);':
                self.state.show_inventory()
            else:
                renpy.say(None, "Code 355 not implemented to eval '%s'" % script_string)

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
                        text = self.replace_names(command['parameters'][0])
                        accumulated_text.append(text)

                    renpy.say(None, "\n".join(accumulated_text))

                # Show choices
                elif command['code'] == 102:
                    choice_texts = command['parameters'][0]
                    cancel_type = command['parameters'][1]
                    if cancel_type >= len(choice_texts):
                        cancel_type = -2

                    if not hasattr(self, 'choices_to_hide'):
                        self.choices_to_hide = []

                    result = renpy.display_menu([(self.replace_names(text), index) for index, text in enumerate(choice_texts) if index not in self.choices_to_hide])
                    self.state.branch[command['indent']] = result
                    self.choices_to_hide = []

                # Choose item
                elif command['code'] == 104:
                    variable_id = command['parameters'][0]
                    item_type = command['parameters'][1] or 2
                    choices = self.state.party.item_choices(item_type)
                    result = None
                    if len(choices) > 0:
                        result = renpy.display_menu([(text, index) for text, index in choices])
                    else:
                        renpy.say(None, "No items to choose...")
                    self.state.variables.set_value(variable_id, result)

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
                    self.list_index += 1
                    return GameEvent(self.state, common_event, common_event)

                # Repeat Above
                elif command['code'] == 413:
                    if self.parallel():
                        # This might be an endlessly looping animation in a parallel
                        # event. Bail out of the event.
                        self.list_index = len(self.page['list']) - 1
                        return

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
                        value = self.state.variables.value(command['parameters'][4])
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
                    if self.parallel() and command['parameters'][1]['wait']:
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

                    if not hasattr(game_state, 'picture_since_last_pause'):
                        # Backfill the boolean for savegames from before this bit was introduced
                        game_state.picture_since_last_pause = True

                    if game_state.picture_since_last_pause and not self.parallel():
                        game_state.picture_since_last_pause = False
                        renpy.pause()

                # Show picture
                elif command['code'] == 231:
                    game_state.picture_since_last_pause = True
                    picture_id, picture_name = command['parameters'][0:2]
                    renpy.show(picture_name, tag = "picture%s" % picture_id)

                # Move picture - TODO - like the first scene in the cafe in ics2
                elif command['code'] == 232:
                    pass

                # Tint picture - TODO ?
                elif command['code'] == 234:
                    pass

                # Erase picture
                elif command['code'] == 235:
                    picture_id = command['parameters'][0]
                    renpy.hide("picture%s" % picture_id)

                # Weather Effect
                elif command['code'] == 236:
                    pass

                # Audio
                elif command['code'] in [241, 242, 243, 244, 245, 246, 249, 250, 251]:
                    pass

                # Play Movie
                elif command['code'] == 261:
                    renpy.show(command['parameters'][0], tag = "movie")
                    renpy.pause()
                    renpy.hide("movie")

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

                # Change actor name
                elif command['code'] == 320:
                    actor_index, actor_name = command['parameters'][0:2]
                    self.state.actors.set_property(actor_index, 'name', actor_name)

                # Change actor image
                elif command['code'] == 322:
                    pass

                # 'Script'
                elif command['code'] == 355:
                    self.eval_script(command)
                    while self.page['list'][self.list_index + 1]['code'] in [655]:
                        self.list_index += 1
                        self.eval_script(self.page['list'][self.list_index])

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

                # 'Plugin'
                elif command['code'] == 356:
                    if command['parameters'][0] == 'OpenSynthesis':
                        self.list_index += 1
                        self.state.show_synthesis_ui()

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
