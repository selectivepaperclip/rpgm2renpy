init python:
    class MogWeatherEx:
        COMMANDS = [
            'weather',
            'clear_weather'
        ]

        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('MOG_Weather_EX')

        @classmethod
        def is_weather_command(cls, plugin_command):
            if cls.plugin_active() and plugin_command in MogWeatherEx.COMMANDS:
                return True
            return False
