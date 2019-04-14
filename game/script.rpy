﻿define debug_events = False
define debug_sound = False
define noisy_events = False
define debug_pickling = False
define debug_reachability_grid = False
define profile_timings = False
define tile_images = {}
define normal_images = {}
define character_images = {}
define parallax_images = {}
define face_images = {}
define mapdest = None
define keyed_common_event = None
define keyed_function_call = None
define draw_impassible_tiles = False
define hide_unreachable_events = False
define show_noop_events = False
define viewport_xadjustment = ui.adjustment()
define viewport_yadjustment = ui.adjustment()
define animation_fps = 60.0

init -10 python:
    # The game file loader caches all the parsed JSON files for the game:
    # it's deliberately created before the game starts so that RenPy
    # doesn't keep big expensive copies of all that data in the rollback log.
    game_file_loader = GameFileLoader()

    # Similarly load the reachability grid cache outside of the game flow
    # so great big pathfinding grids don't get pickled
    rpgm_reachability_grid_cache = ReachabilityGridCacheV2()

    image_size_cache = ImageSizeCache()
    rpgm_colors = RpgmColors()

    import glob
    build.classify('rpgmdata', 'all')
    build.classify('rpgmcache/**', None)

    class Re(object):
        def __init__(self):
            self.last_match = None

        def match(self,pattern,text):
            self.last_match = re.match(pattern,text)
            return self.last_match

        def search(self,pattern,text):
            self.last_match = re.search(pattern,text)
            return self.last_match

    rpgm_dir = 'rpgmdata'
    if not os.path.exists(os.path.join(renpy.config.basedir, rpgm_dir)):
        rpgm_dir = os.path.join('game', 'unpacked').replace('\\', '/')

    def rpgm_path(filename):
        return rpgm_dir + '/' + filename

    def rpgm_file(filename):
        return renpy.file(rpgm_path(filename))

    def rpgm_data_path(filename):
        if rpgm_metadata.is_pre_mv_version:
            return rpgm_path('JsonData/' + filename)
        else:
            return rpgm_path('www/data/' + filename)

    def rpgm_data_file(filename):
        return renpy.file(rpgm_data_path(filename))

    def supported_image(ext):
        return ext.lower() in [ ".jpg", ".jpeg", ".png", ".webp" ]

    renpy.music.register_channel('background_sound', mixer = 'music')

    map_cache_directory = os.path.join('rpgmcache', 'maps', 'v1').replace('\\', '/')
    if not os.path.exists(os.path.join(renpy.config.basedir, map_cache_directory)):
        os.makedirs(os.path.join(renpy.config.basedir, map_cache_directory))

    class RpgmMetadata():
        def __init__(self):
            self.is_pre_mv_version = os.path.exists(os.path.join(renpy.config.basedir, rpgm_path('JsonData')))
            self.has_large_choices_plugin = False
            if self.is_pre_mv_version:
                self.pictures_path = rpgm_path("Graphics/Pictures/")
                self.movies_path = rpgm_path("Movies/")
                self.background_music_path = rpgm_path("Audio/BGM/")
                self.background_sound_path = rpgm_path("Audio/BGS/")
                self.sound_effects_path = rpgm_path("Audio/SE/")
                self.tilesets_path = rpgm_path("Graphics/Tilesets/")
                self.characters_path = rpgm_path("Graphics/Characters/")
                self.parallaxes_path = rpgm_path("Graphics/Parallaxes/")
                self.faces_path = rpgm_path("Graphics/Faces/")
                self.window_png_path = rpgm_path("Graphics/System/Window.png")
                self.tile_width = 32
                self.tile_height = 32
                possible_choice_plugin_filenames = ['Choces_More.rb', 'LargeChoices.rb', 'More_Choices.rb']
                if any(os.path.exists(os.path.join(config.basedir, rpgm_path('Scripts/%s' % filename))) for filename in possible_choice_plugin_filenames):
                    self.has_large_choices_plugin = True
            else:
                self.pictures_path = rpgm_path("www/img/pictures/")
                self.movies_path = rpgm_path("www/movies/")
                self.background_music_path = rpgm_path("www/audio/bgm/")
                self.background_sound_path = rpgm_path("www/audio/bgs/")
                self.sound_effects_path = rpgm_path("Audio/se/")
                self.tilesets_path = rpgm_path("www/img/tilesets/")
                self.characters_path = rpgm_path("www/img/characters/")
                self.parallaxes_path = rpgm_path("www/img/parallaxes/")
                self.faces_path = rpgm_path("www/img/faces/")
                self.window_png_path = rpgm_path("www/img/system/Window.png")
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
                    basename = os.path.basename(filename)
                    base, ext = os.path.splitext(basename)
                    if supported_image(ext):
                        return os.path.join(titles_path, basename).replace("\\", "/")

    rpgm_metadata = RpgmMetadata()

init python:
    import re
    import random
    import json
    import math

    config.layers = [ 'master', 'maplayer', 'transient', 'screens', 'overlay' ]

    def scale_image(path):
        return im.Scale(path, config.screen_width, config.screen_height, bilinear=True)

    def scale_movie(path):
        return Movie(play=path, size=(config.screen_width, config.screen_height))

    def rpgm_picture_name(base):
        return 'rpgmpicture-' + base.lower().replace('.', '_')

    def rpgm_movie_name(base):
        return 'rpgmmovie-' + base.lower()

    def rpgm_parallax_name(base):
        return 'rpgmparallax-' + base.lower()

    def rpgm_face_name(base):
        return 'rpgmface-' + base.lower()

    def mog_title_layer_image():
        mog_title_layers = game_file_loader.plugin_data_exact('MOG_TitleLayers')
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

    if game_file_loader.plugin_data_exact('GALV_MapProjectiles'):
        renpy.image('crosshair-small-red', im.MatrixColor('custom_gui/crosshair-small.png', im.matrix.colorize("#f00", "#000")))
        renpy.image('crosshair-small-blue', im.MatrixColor('custom_gui/crosshair-small.png', im.matrix.colorize("#00f", "#000")))

    system_data = game_file_loader.json_file(rpgm_data_path("System.json"))
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
        character_images[image_name.lower()] = rpgm_metadata.characters_path + filename

    if os.path.exists(os.path.join(config.basedir, rpgm_metadata.parallaxes_path)):
        for filename in os.listdir(os.path.join(config.basedir, rpgm_metadata.parallaxes_path)):
            base, ext = os.path.splitext(os.path.basename(filename))
            if not supported_image(ext):
                continue
            image_name = rpgm_parallax_name(base)
            parallax_images[image_name] = rpgm_metadata.parallaxes_path + filename

    if os.path.exists(os.path.join(config.basedir, rpgm_metadata.faces_path)):
        for filename in os.listdir(os.path.join(config.basedir, rpgm_metadata.faces_path)):
            base, ext = os.path.splitext(os.path.basename(filename))
            if not supported_image(ext):
                continue
            image_name = rpgm_face_name(base)
            face_images[image_name] = rpgm_metadata.faces_path + filename

label start:
    python:
        game_state = GameState()
        game_state.set_game_start_events()
        if GameIdentifier().is_ics1():
            game_state.party.gold = 30000
            hide_unreachable_events = True
        elif GameIdentifier().is_ics2():
            GameSkips().ics2_skip_unpacking()
        elif GameIdentifier().is_taboo_request():
            hide_unreachable_events = True
        elif GameIdentifier().is_my_summer():
            hide_unreachable_events = True
        elif GameIdentifier().is_visiting_sara():
            hide_unreachable_events = True
        elif GameIdentifier().is_milfs_control():
            hide_unreachable_events = True
        elif GameIdentifier().is_milfs_villa():
            hide_unreachable_events = True
        elif rpgm_game_data.get('hide_unreachable_events', False) == True:
            hide_unreachable_events = True

label game:
    $ end_game = False

    while end_game == False:
        $ in_interaction = game_state.do_next_thing(mapdest, keyed_common_event)
        if not in_interaction:
          $ game_state.show_map(in_interaction)
          $ renpy.checkpoint()
          $ renpy.block_rollback()
          $ renpy.ui.interact(mouse="screen", type="screen")
        $ mapdest = None
        $ keyed_function_call = None
        $ keyed_common_event = None
        $ show_synthesis = None

    return

label after_load:
    python:
        displayed_map_screen = renpy.get_widget("mapscreen", "map_bg_viewport", layer = "maplayer")
        if displayed_map_screen:
            viewport_xadjustment = displayed_map_screen.xadjustment
            viewport_yadjustment = displayed_map_screen.yadjustment
            bg_image = renpy.get_widget("mapscreen", "map_bg_image", layer = "maplayer")
            if bg_image:
                bg_image.children[0].filename = game_state.map.background_image_cache_file()

        # Ensure the map's background has been (re-)generated before any cached displayables get shown
        game_state.map.background_image()
