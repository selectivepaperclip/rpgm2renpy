init -99 python:
    class GameFileLoader(object):
        def __init__(self):
            self.exact_plugin_cache = {}
            self.loose_plugin_cache = {}

        def json_file(self, filename):
            if not hasattr(self, '_json_files'):
                self._json_files = {}
            if not filename in self._json_files:
                with renpy.file(filename) as f:
                    self._json_files[filename] = json.load(f)

            return self._json_files[filename]

        def package_json(self):
            if rpgm_metadata.is_pre_mv_version:
                return None

            if not hasattr(self, '_package_json'):
                with rpgm_file('package.json') as f:
                    self._package_json = json.load(f)

            return self._package_json

        def plugins_json(self):
            if rpgm_metadata.is_pre_mv_version:
                return []

            if not hasattr(self, '_plugins_json'):
                with rpgm_file('www/js/plugins.js') as f:
                    # the plugins.js file starts with "var $plugins = ["
                    # delete everything before the first [
                    content = f.read()
                    self._plugins_json = json.loads(content[content.find('['):].rstrip().rstrip(';'))

            return self._plugins_json

        def plugin_data_exact(self, plugin_name):
            if plugin_name in self.exact_plugin_cache:
                return self.exact_plugin_cache[plugin_name]

            self.exact_plugin_cache[plugin_name] = next((plugin_data for plugin_data in self.plugins_json() if plugin_data['name'] == plugin_name), None)
            return self.exact_plugin_cache[plugin_name]

        def plugin_data_startswith(self, plugin_name):
            if plugin_name in self.loose_plugin_cache:
                return self.loose_plugin_cache[plugin_name]

            self.loose_plugin_cache[plugin_name] = next((plugin_data for plugin_data in self.plugins_json() if plugin_data['name'].startswith(plugin_name)), None)
            return self.loose_plugin_cache[plugin_name]
