init python:
    class GalvMapProjectiles:
        @classmethod
        def plugin_active(cls):
            plugin = game_file_loader.plugin_data_exact('GALV_MapProjectiles')
            if not plugin:
                return False
            return plugin['status']

        @classmethod
        def process_script(cls, event, script_string):
            if not cls.plugin_active():
                return False

            gre = Re()
            if gre.match('Galv\.PROJ\.(dir|atTarget)', script_string):
                return True
            else:
                return False

        @classmethod
        def is_projectile_page(cls, page):
            if not cls.plugin_active():
                return False

            for command in page['list']:
                if command['code'] == 108 and command['parameters'][0] == '<projEffect>':
                    return True

            return False
