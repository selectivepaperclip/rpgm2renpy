init python:
    class GalvScreenZoom:
        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('Galv_ScreenZoom')

        @classmethod
        def process_script(cls, event, line, script_string):
            if not cls.plugin_active():
                return False

            gre = Re()
            if gre.match('Galv\.ZOOM', script_string):
                return True
            else:
                return False