init python:
    class SkippableManager():
        def skippables(self, auto = False):
            skippables_for_map = rpgm_game_data.get("skippables", {}).get(str(game_state.map.map_id), [])
            if auto:
                skippables_for_map = [s for s in skippables_for_map if 'auto' in s and s['auto'] == True]
            else:
                skippables_for_map = [s for s in skippables_for_map if 'auto' not in s or s['auto'] == False]

            result = []
            for skippable in skippables_for_map:
                if any(self.eval_skippable_condition(condition) for condition in skippable['if_any']):
                    result.append(skippable)
            return result

        def eval_skippable_condition(self, condition):
            if condition[0] == 'self_switch_value':
                event_id, self_switch_name, on_or_off = condition[1:]
                self_switch_value = game_state.self_switches.value((game_state.map.map_id, event_id, self_switch_name))
                if on_or_off == True:
                    return self_switch_value == True
                else:
                    return self_switch_value == None
            elif condition[0] == 'switch_value':
                switch_id, on_or_off = condition[1:]
                return game_state.switches.value(switch_id) == on_or_off

        def skip_next_skippable_event(self):
            skippable = self.skippables()[0]
            if not skippable:
                return
            self.run_commands_for_skippable(skippable)

        def skip_auto_skippable_events(self):
            for skippable in self.skippables(auto = True):
                self.run_commands_for_skippable(skippable)

        def run_commands_for_skippable(self, skippable):
            for command in skippable['commands']:
                if command[0] == 'set_switch_value': # ["set_switch_value", 255, true]
                    game_state.switches.set_value(command[1], command[2])
                elif command[0] == 'set_self_switch_value': # ["set_self_switch_value", 13, "A", true]
                    game_state.self_switches.set_value((game_state.map.map_id, command[1], command[2]), command[3])
                elif command[0] == 'set_variable': # ["set_variable", 53, 3]
                    game_state.variables.set_value(command[1], command[2])
                elif command[0] == 'set_player_location': #  ["set_player_location", 20, 14]
                    game_state.player_x = command[1]
                    game_state.player_y = command[2]
                elif command[0] == 'set_event_location': # ["set_event_location", 5, 18, 21]
                    event = game_state.map.find_event_at_index(command[1])
                    game_state.map.override_event_location(event.event_data, (command[2], command[3]))
                elif command[0] == 'set_player_direction': # ["set_player_direction", 8]
                    game_state.player_direction = command[1]
                elif command[0] == 'set_event_direction': # ["set_event_direction", 5, 8]
                    event = game_state.map.find_event_at_index(command[1])
                    event.override_page(game_state.map, GameEvent.PROPERTY_DIRECTION, command[1])
                elif command[0] == 'set_inventory_item': # ["set_inventory_item", 64, 0]
                    game_state.party.items[command[1]] = command[2]
                elif command[0] == 'activate_event': # ["activate_event", 2]
                    event = game_state.map.find_event_at_index(command[1])
                    game_state.events.append(event)
