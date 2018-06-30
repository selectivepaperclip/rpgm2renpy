define debug_events = False
define noisy_events = False
define debug_pickling = False
define tile_images = {}
define normal_images = {}
define character_images = {}
define character_image_sizes = {}
define image_sizes = {}
define mapdest = None
define keyed_common_event = None
define draw_impassible_tiles = False
define show_synthesis = None

init python:
    import re
    import random
    import json
    import math

    def scale_image(path):
        return im.Scale(path, config.screen_width, config.screen_height, bilinear=True)

    def scale_movie(path):
        return Movie(play=filename, size=(config.screen_width, config.screen_height))

    with renpy.file('unpacked/www/data/System.json') as f:
        system_data = json.load(f)
        title_screen_file_path = 'unpacked/www/img/titles1/' + system_data['title1Name'] + '.png'
        if renpy.exists(title_screen_file_path):
            gui.main_menu_background = scale_image(title_screen_file_path)

    for filename in renpy.list_files():
        if filename.startswith("unpacked/www/img/pictures/"):
            image_name = os.path.splitext(filename.replace("unpacked/www/img/pictures/", ""))[0]
            if renpy.has_image(image_name, exact=True):
                continue
            normal_images[image_name] = filename

            renpy.image(image_name, scale_image(filename))

        if filename.startswith("unpacked/www/movies/"):
            image_name = os.path.splitext(filename.replace("unpacked/www/movies/", ""))[0]
            if renpy.has_image(image_name, exact=True):
                continue

            renpy.image(image_name, scale_movie(filename))

        if filename.startswith("unpacked/www/img/tilesets/"):
            image_name = os.path.splitext(filename.replace("unpacked/www/img/tilesets/", ""))[0].replace(".", "_")
            if renpy.has_image(image_name, exact=True):
                continue

            tile_images[image_name] = filename
            renpy.image(image_name, filename)

        if filename.startswith("unpacked/www/img/characters/"):
            image_name = os.path.splitext(filename.replace("unpacked/www/img/characters/", ""))[0].replace(".", "_")
            if renpy.has_image(image_name, exact=True):
                continue

            character_images[image_name] = filename
            renpy.image(image_name, filename)

label start:
    python:
        game_state = GameState()
        game_state.set_game_start_events()

label game:
    $ end_game = False

    while end_game == False:
        $ game_state.do_next_thing(mapdest, keyed_common_event)
        $ mapdest = None
        $ keyed_common_event = None
        $ show_synthesis = None
        $ renpy.checkpoint()

    return