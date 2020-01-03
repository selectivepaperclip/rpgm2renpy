init python:
    class OrangeTimeSystem(RpgmPlugin):
        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('OrangeTimeSystem')

        @classmethod
        def process_script(cls, event, line, script_string):
            if not cls.plugin_active():
                return False

            # .hour =
            # .minute =
            # .addHours(\d)
            # .refreshTimeSystem
            # .runInDays(\d, \d)
            # .runInHours(\d, \d)
            gre = Re()
            if not gre.match('OrangeTimeSystem\.(.*)', script_string):
                return False

            command = gre.last_match.groups()[0]
            if gre.match('addHours\((\d+)\)', command):
                cls.add_time(hours = int(gre.last_match.groups()[0]))
                return True
            elif gre.match('hour = (\d+);', command):
                old_data = cls.get_date_time()
                game_state.orange_time_system_data['hour'] += int(gre.last_match.groups()[0])
                return True
            elif gre.match('minute = (\d+);', command):
                old_data = cls.get_date_time()
                game_state.orange_time_system_data['minute'] += int(gre.last_match.groups()[0])
                return True
            elif command == 'refreshTimeSystem()':
                return True

            # TODO: all of this stuff
            return False

        @classmethod
        def get_date_time(cls):
            if not hasattr(game_state, 'orange_time_system_data'):
                plugin = game_file_loader.plugin_data_exact('OrangeTimeSystem')
                game_state.orange_time_system_data = {
                    "hour": plugin.get('initialHour', 0),
                    "minute": plugin.get('initialMinute', 0),
                    "seconds": plugin.get('initialSecond', 0),
                    "day": plugin.get('initialDay', 1),
                    "month": plugin.get('initialMonth', 1),
                    "year": plugin.get('initialYear', 1),
                    "day_period": "EARLY_MORNING",
                    "weekday": 0
                }

            return {
                "hour": game_state.orange_time_system_data['hour'],
                "minute": game_state.orange_time_system_data['minute'],
                "seconds": game_state.orange_time_system_data['seconds'],
                "day": game_state.orange_time_system_data['day'],
                "month": game_state.orange_time_system_data['month'],
                "year": game_state.orange_time_system_data['year'],
                "day_period": game_state.orange_time_system_data['day_period'],
                "weekday": game_state.orange_time_system_data['weekday']
            }

        @classmethod
        def add_time(cls, seconds = 0, minutes = 0, hours = 0, days = 0, months = 0 , years = 0):
            old_data = cls.get_date_time()

            game_state.orange_time_system_data['seconds'] += int(seconds or 0)
            game_state.orange_time_system_data['minute'] += int(minutes or 0)
            game_state.orange_time_system_data['hour'] += int(hours or 0)
            game_state.orange_time_system_data['day'] += int(days or 0)
            game_state.orange_time_system_data['month'] += int(months or 0)
            game_state.orange_time_system_data['year'] += int(years or 0)

            # run events