init python:
    class YepXExtMesPack1:
        @classmethod
        def plugin_active(cls):
            plugin = game_file_loader.plugin_data_exact('YEP_MainMenuManager')
            if not plugin:
                return False
            return plugin['status']

        @classmethod
        def valid_command(cls, plugin_command):
            if not cls.plugin_active:
                return False
            if plugin_command in ['ChoiceRowMax']:
                return True
