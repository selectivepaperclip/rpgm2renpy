init python:
    class HIME_PreTitleEvents:
        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('HIME_PreTitleEvents')

        @classmethod
        def pre_title_map_id(cls):
            if not cls.plugin_active():
                return

            plugin_data = game_file_loader.plugin_data_exact('HIME_PreTitleEvents')
            return int(plugin_data['parameters']['Pre-Title Map ID'])
