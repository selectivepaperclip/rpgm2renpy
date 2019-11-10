init python:
    class GalvEventSpawnTimers(RpgmPlugin):
        DO_TIMER_REGEXP = 'this\.doTimer\("(\w+)",(true|false)\)'

        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('GALV_EventSpawnTimers')

        @classmethod
        def process_script(cls, event, line, script_string):
            if not cls.plugin_active():
                return False

            gre = Re()
            if gre.match('this\.setSpawn\(0,0,(\d+)\)', script_string):
                cls.initialize_timer_storage(event)
                event.state.map.galv_event_spawn_timers[event.event_data['id']] = {
                    'wait': int(gre.last_match.groups()[0])
                }
                return True
            else:
                return False

        @classmethod
        def process_move_route(cls, event, script_string):
            if not cls.plugin_active():
                return False

            gre = Re()
            if gre.match(GalvEventSpawnTimers.DO_TIMER_REGEXP, script_string):
                cls.initialize_timer_storage(event)
                timer_data = event.state.map.galv_event_spawn_timers[event.event_data['id']]

                if not 'self_switches' in timer_data:
                    timer_data['self_switches'] = {}
                self_switch_name = gre.last_match.groups()[0]
                self_switch_on = gre.last_match.groups()[1] == 'true'
                timer_data['self_switches'][self_switch_name] = self_switch_on
                return True
            else:
                return False

        @classmethod
        def has_timer(cls, command):
            if not cls.plugin_active():
                return False

            return re.match(GalvEventSpawnTimers.DO_TIMER_REGEXP, command['parameters'][0])

        @classmethod
        def event_timers(cls, map):
            if not cls.plugin_active():
                return []
            if not hasattr(map, 'galv_event_spawn_timers'):
                return []
            return map.galv_event_spawn_timers.keys()

        @classmethod
        def run_timer_actions(cls, map):
            if not cls.plugin_active():
                return
            if not hasattr(map, 'galv_event_spawn_timers'):
                return
            for event_id, timer_data in map.galv_event_spawn_timers.iteritems():
                if 'self_switches' in timer_data:
                    for self_switch_name, self_switch_on in timer_data['self_switches'].iteritems():
                        map.state.self_switches.set_value((map.map_id, event_id, self_switch_name), self_switch_on)

        @classmethod
        def initialize_timer_storage(cls, event):
            if not hasattr(event.state.map, 'galv_event_spawn_timers'):
                event.state.map.galv_event_spawn_timers = {}