init python:
    class MogWeatherEx(RpgmPlugin):
        COMMANDS = [
            'weather',
            'clear_weather'
        ]

        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('MOG_Weather_EX')

        @classmethod
        def process_command(cls, command, command_args):
            if cls.plugin_active() and command in MogWeatherEx.COMMANDS:
                return True
            return False
