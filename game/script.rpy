define debug_events = False
define noisy_events = False
define debug_pickling = False
define debug_reachability_grid = False
define profile_timings = False
define tile_images = {}
define normal_images = {}
define character_images = {}
define character_image_sizes = {}
define parallax_images = {}
define image_sizes = {}
define picture_image_sizes = {}
define mapdest = None
define keyed_common_event = None
define draw_impassible_tiles = False
define hide_unreachable_events = False
define show_noop_events = False
define viewport_xadjustment = ui.adjustment()
define viewport_yadjustment = ui.adjustment()
define animation_fps = 60.0

init -10 python:
    import glob
    build.classify('rpgmdata', 'all')
    build.classify('rpgmcache/**', None)

    class PluginsLoader(SelectivelyPickle):
        def package_json(self):
            if rpgm_metadata.is_pre_mv_version:
                return None

            if not hasattr(self, '_package_json'):
                with rpgm_file('package.json') as f:
                    self._package_json = json.load(f)

            return self._package_json

        def json(self):
            if rpgm_metadata.is_pre_mv_version:
                return []

            if not hasattr(self, '_json'):
                with rpgm_file('www/js/plugins.js') as f:
                    # the plugins.js file starts with "var $plugins = ["
                    # delete everything before the first [
                    content = f.read()
                    self._json = json.loads(content[content.find('['):].rstrip().rstrip(';'))

            return self._json

    rpgm_dir = 'rpgmdata'
    if not os.path.exists(os.path.join(renpy.config.basedir, rpgm_dir)):
        rpgm_dir = os.path.join('game', 'unpacked').replace('\\', '/')

    def rpgm_path(filename):
        return rpgm_dir + '/' + filename

    def rpgm_file(filename):
        return renpy.file(rpgm_path(filename))

    def rpgm_data_file(filename):
        if rpgm_metadata.is_pre_mv_version:
            return rpgm_file('JsonData/' + filename)
        else:
            return rpgm_file('www/data/' + filename)

    def supported_image(ext):
        return ext.lower() in [ ".jpg", ".jpeg", ".png", ".webp" ]

    map_cache_directory = os.path.join(renpy.config.basedir, 'rpgmcache', 'maps', 'v1').replace('\\', '/')
    if not os.path.exists(map_cache_directory):
        os.makedirs(map_cache_directory)

    class RpgmMetadata():
        def __init__(self):
            self.is_pre_mv_version = os.path.exists(os.path.join(renpy.config.basedir, rpgm_path('JsonData')))
            if self.is_pre_mv_version:
                self.pictures_path = rpgm_path("Graphics/Pictures/")
                self.movies_path = rpgm_path("Movies/")
                self.tilesets_path = rpgm_path("Graphics/Tilesets/")
                self.characters_path = rpgm_path("Graphics/Characters/")
                self.parallaxes_path = rpgm_path("Graphics/Parallaxes/")
                self.tile_width = 32
                self.tile_height = 32
            else:
                self.pictures_path = rpgm_path("www/img/pictures/")
                self.movies_path = rpgm_path("www/movies/")
                self.tilesets_path = rpgm_path("www/img/tilesets/")
                self.characters_path = rpgm_path("www/img/characters/")
                self.parallaxes_path = rpgm_path("www/img/parallaxes/")
                self.tile_width = 48
                self.tile_height = 48

        def title_screen_file(self, base_file):
            titles_path = None
            if self.is_pre_mv_version:
                titles_path = rpgm_path('Graphics/Titles1/')
            else:
                titles_path = rpgm_path('www/img/titles1/')

            if os.path.exists(os.path.join(config.basedir, titles_path)):
                for filename in glob.glob(os.path.join(config.basedir, titles_path, '%s.*' % base_file)):
                    base, ext = os.path.splitext(os.path.basename(filename))
                    if supported_image(ext):
                        return filename.replace("\\", "/")

    rpgm_metadata = RpgmMetadata()

    rpgm_plugins_loader = PluginsLoader()

init python:
    import re
    import random
    import json
    import math

    config.layers = [ 'maplayer', 'master', 'transient', 'screens', 'overlay' ]

    def scale_image(path):
        return im.Scale(path, config.screen_width, config.screen_height, bilinear=True)

    def scale_movie(path):
        return Movie(play=path, size=(config.screen_width, config.screen_height))

    def rpgm_picture_name(base):
        return 'rpgmpicture-' + base.lower()

    def rpgm_movie_name(base):
        return 'rpgmmovie-' + base.lower()

    def rpgm_parallax_name(base):
        return 'rpgmparallax-' + base.lower()

    def mog_title_layer_image():
        plugins = PluginsLoader().json()
        mog_title_layers = next((plugin_data for plugin_data in plugins if plugin_data['name'] == 'MOG_TitleLayers'), None)
        if mog_title_layers:
            layer_data = {}
            layer_line_regexp = re.compile('^L(\d+) (.*)$')
            for key, value in mog_title_layers['parameters'].iteritems():
                match = re.match(layer_line_regexp, key)
                if match:
                    layer_id = int(match.groups()[0])
                    layer_key = match.groups()[1]
                    if not layer_id in layer_data:
                        layer_data[layer_id] = {}
                    layer_data[layer_id][layer_key] = value
            composite_args = [(config.screen_width, config.screen_height)]
            for layer_id in sorted(layer_data.iterkeys()):
                layer_values = layer_data[layer_id]
                if layer_values['Visible'] == 'true':
                    composite_args.append((0, 0))
                    # It probably wouldn't be that hard to animate this for situations where there are multiple frames,
                    # but doesn't seem like a high priority
                    layer_file = glob.glob(os.path.join(config.basedir, rpgm_path('www/img/titles1/' + layer_values['File Name'] + '*')))[0]
                    composite_args.append(rpgm_path('www/img/titles1/' + os.path.basename(layer_file)))
            return LiveComposite(*composite_args)
        return None

    with rpgm_data_file('System.json') as f:
        system_data = json.load(f)
        title_screen_file_path = rpgm_metadata.title_screen_file(system_data['title1Name'])
        if title_screen_file_path:
            gui.main_menu_background = scale_image(title_screen_file_path)
        else:
            title_layer_image = mog_title_layer_image()
            if title_layer_image:
                gui.main_menu_background = title_layer_image

    for filename in os.listdir(os.path.join(config.basedir, rpgm_metadata.pictures_path)):
        base, ext = os.path.splitext(os.path.basename(filename))
        if not supported_image(ext):
            continue
        pic_name = rpgm_picture_name(base)
        if renpy.has_image(pic_name, exact=True):
            continue
        normal_images[pic_name] = rpgm_metadata.pictures_path + filename
        renpy.image(pic_name, rpgm_metadata.pictures_path + filename)

    if os.path.exists(os.path.join(config.basedir, rpgm_metadata.movies_path)):
        for filename in os.listdir(os.path.join(config.basedir, rpgm_metadata.movies_path)):
            image_name = rpgm_movie_name(os.path.splitext(os.path.basename(filename))[0])
            if renpy.has_image(image_name, exact=True):
                continue

            renpy.image(image_name, scale_movie(rpgm_metadata.movies_path + filename))

    for filename in os.listdir(os.path.join(config.basedir, rpgm_metadata.tilesets_path)):
        base, ext = os.path.splitext(os.path.basename(filename))
        if not supported_image(ext):
            continue
        image_name = base.replace(".", "_")
        tile_images[image_name] = rpgm_metadata.tilesets_path + filename

    for filename in os.listdir(os.path.join(config.basedir, rpgm_metadata.characters_path)):
        base, ext = os.path.splitext(os.path.basename(filename))
        if not supported_image(ext):
            continue
        image_name = base.replace(".", "_")
        character_images[image_name] = rpgm_metadata.characters_path + filename

    if os.path.exists(os.path.join(config.basedir, rpgm_metadata.parallaxes_path)):
        for filename in os.listdir(os.path.join(config.basedir, rpgm_metadata.parallaxes_path)):
            base, ext = os.path.splitext(os.path.basename(filename))
            if not supported_image(ext):
                continue
            image_name = rpgm_parallax_name(base)
            parallax_images[image_name] = rpgm_metadata.parallaxes_path + filename

label start:
    python:
        game_state = GameState()
        game_state.set_game_start_events()
        if GameIdentifier().is_ics2():
            GameSkips().ics2_skip_unpacking()
        if GameIdentifier().is_taboo_request():
            hide_unreachable_events = True
        if GameIdentifier().is_my_summer():
            hide_unreachable_events = True
        if GameIdentifier().is_visiting_sara():
            hide_unreachable_events = True

label game:
    $ end_game = False

    while end_game == False:
        $ in_interaction = game_state.do_next_thing(mapdest, keyed_common_event)
        $ game_state.show_map(in_interaction)
        if not in_interaction:
          $ renpy.checkpoint()
          $ renpy.ui.interact(mouse="screen", type="screen")
        $ mapdest = None
        $ keyed_common_event = None
        $ show_synthesis = None

    return
