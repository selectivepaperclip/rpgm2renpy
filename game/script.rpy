define debug_events = False
define noisy_events = False
define debug_pickling = False
define profile_timings = False
define tile_images = {}
define normal_images = {}
define character_images = {}
define character_image_sizes = {}
define image_sizes = {}
define mapdest = None
define keyed_common_event = None
define draw_impassible_tiles = False
define show_synthesis = None
define viewport_xadjustment = ui.adjustment()
define viewport_yadjustment = ui.adjustment()

init -10 python:
    build.classify('rpgmdata', 'all')

    class PluginsLoader(SelectivelyPickle):
        def json(self):
            if not hasattr(self, '_json'):
                with rpgm_file('www/js/plugins.js') as f:
                    # the plugins.js file starts with "var $plugins = ["
                    # delete everything before the first [
                    content = f.read()
                    self._json = json.loads(content[content.find('['):].rstrip().rstrip(';'))

            return self._json

    rpgm_dir = os.path.join(renpy.config.basedir, 'rpgmdata').replace('\\', '/')
    if not os.path.exists(rpgm_dir):
        rpgm_dir = os.path.join(renpy.config.gamedir, 'unpacked').replace('\\', '/')

    def rpgm_path(filename):
        return rpgm_dir + '/' + filename

    def rpgm_file(filename):
        return renpy.file(rpgm_path(filename))

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

    def supported_image(ext):
        return ext.lower() in [ ".jpg", ".jpeg", ".png", ".webp" ]

    with rpgm_file('www/data/System.json') as f:
        system_data = json.load(f)
        title_screen_file_path = rpgm_path('www/img/titles1/' + system_data['title1Name'] + '.png')
        if os.path.exists(title_screen_file_path):
            gui.main_menu_background = scale_image(title_screen_file_path)

    pictures_path = rpgm_path("www/img/pictures/")
    for filename in os.listdir(pictures_path):
        base, ext = os.path.splitext(os.path.basename(filename))
        if not supported_image(ext):
            continue
        if renpy.has_image(base, exact=True):
            continue
        normal_images[base] = pictures_path + filename

        renpy.image(base, scale_image(pictures_path + filename))

    movies_path = rpgm_path("www/movies/")
    if os.path.exists(movies_path):
        for filename in os.listdir(movies_path):
            image_name = os.path.splitext(os.path.basename(filename))[0]
            if renpy.has_image(image_name, exact=True):
                continue

            renpy.image(image_name, scale_movie(movies_path + filename))

    tilesets_path = rpgm_path("www/img/tilesets/")
    for filename in os.listdir(tilesets_path):
        base, ext = os.path.splitext(os.path.basename(filename))
        if not supported_image(ext):
            continue
        image_name = base.replace(".", "_")
        tile_images[image_name] = tilesets_path + filename

    characters_path = rpgm_path("www/img/characters/")
    for filename in os.listdir(characters_path):
        base, ext = os.path.splitext(os.path.basename(filename))
        if not supported_image(ext):
            continue
        image_name = base.replace(".", "_")
        character_images[image_name] = characters_path + filename

label start:
    python:
        game_state = GameState()
        game_state.set_game_start_events()
        if GameIdentifier().is_ics2():
            GameSkips().ics2_skip_unpacking()

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