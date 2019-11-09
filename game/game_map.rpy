init python:
    import time
    import pygame
    import pygame_sdl2.image
    from Queue import PriorityQueue

    class MapClickable:
        def __init__(
            self,
            x,
            y,
            label = None,
            special = False,
            page_index = None,
            clicky = False,
            has_commands = True,
            walk_destination = False,
            projectile_target = False,
            through = False,
            solid = False,
            touch_trigger = False,
            action_trigger = False,
            parallel_trigger = False
        ):
            self.x = x
            self.y = y
            self.label = label
            self.special = special
            self.reachable = True
            self.clicky = clicky
            self.has_commands = has_commands
            self.walk_destination = walk_destination
            self.projectile_target = projectile_target
            self.page_index = page_index
            self.through = through
            self.solid = solid
            self.touch_trigger = touch_trigger
            self.action_trigger = action_trigger
            self.parallel_trigger = parallel_trigger

        def is_walk_destination(self):
            if hasattr(self, 'walk_destination') and self.walk_destination:
                return True
            return False

        def is_projectile_target(self):
            if hasattr(self, 'projectile_target') and self.projectile_target:
                return True
            return False

        def is_noop_event(self):
            if hasattr(self, 'special') and self.special:
                return False
            if self.is_projectile_target():
                return False
            if hasattr(self, 'has_commands') and not self.has_commands:
                return True
            if hasattr(self, 'through') and self.through and self.action_trigger:
                return True
            return False

        def reachable_or_clickable(self):
            return (self.reachable if hasattr(self, 'reachable') else True) or (self.clicky if hasattr(self, 'clicky') else False)

        def map_color(self):
            if self.is_walk_destination():
                if self.reachable_or_clickable():
                    return "#ff8000"
                else:
                    return '#ffc387'
            if self.is_projectile_target():
                return "#00aacc"
            if hasattr(self, 'has_commands') and not self.has_commands:
                return "#000"
            if self.reachable_or_clickable():
                return "#f00"
            else:
                return "#ee9090"

        def tooltip(self):
            parts = []
            if self.label:
                parts.append(self.label)
            if not self.reachable_or_clickable():
                parts.append("(possibly unreachable)")
            if self.special:
                parts.append("(weightSwitch)")
            if len(parts) > 0:
                return ' '.join(parts)
            return None

    class GameTile:
        def __init__(self, tile_id = None, sx = None, sy = None, dx = None, dy = None, w = None, h = None, set_number = None):
            self.tile_id = tile_id
            self.sx = sx
            self.sy = sy
            self.dx = dx
            self.dy = dy
            self.w = w
            self.h = h
            self.set_number = set_number

    # Original GameMapBackground class for compatibility with earlier saves
    class GameMapBackground(renpy.Displayable):
        pass

    class GameMapBackgroundGenerator():
        def __init__(self, map_id, tiles, doodads, cache_file):
            self.map_id = map_id
            self.cache_file = cache_file

            largest_x = 0
            largest_y = 0
            for tile in tiles:
                if tile.x > largest_x:
                    largest_x = tile.x
                if tile.y > largest_y:
                    largest_y = tile.y

            self.width = (largest_x + 1) * rpgm_metadata.tile_width
            self.height = (largest_y + 1) * rpgm_metadata.tile_height
            self.tiles = tiles
            self.doodads = doodads

        def __getstate__(self):
            map_pickle_values = [(k, v) for k, v in self.__dict__.iteritems() if not k.startswith('_')]
            if debug_pickling:
                print ("picklin %s" % self.__class__.__name__)
                print map_pickle_values
            return dict(map_pickle_values)

        def safe_filename_for_pygame_sdl2_save(self):
            # pygame_sdl2 seems to sometimes have problems saving to paths that are not pure-ASCII,
            # "e.g. /Users/José/my-favorite-rpgm-game"

            # internally, pygame_sdl2 uses 'sys.getfilesystemencoding()' to encode unicode
            # python strings into bytes before calling filesystem APIs. if you send a byte
            # string for the path instead, it does not do the encode within pygame_sdl2

            # it works well enough on my machine to interpret 'sys.getfilesystemencoding()' to
            # really mean 'utf-8' when it returns 'mbcs' on a windows machine, but no guarantee
            # that fixes the problem on all OSes, especially older windows that return 'mbcs'

            # see: https://docs.python.org/2/library/sys.html#sys.getfilesystemencoding
            # see: https://docs.python.org/3/library/sys.html#sys.getfilesystemencoding
            # see: https://github.com/renpy/pygame_sdl2/issues/56

            filesystem_encoding = sys.getfilesystemencoding()
            if filesystem_encoding == 'mbcs':
                return self.cache_file.encode('utf-8')

        def save(self):
            # Caching code borrowed from https://github.com/renpy/renpy/blob/f40e61dfdfbf723f9eac88bbfec7765b45599682/renpy/display/imagemap.py
            # because it's hard as hell to figure out what incantations to do without source-diving

            surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)

            tileset_images = {}

            for tile in self.tiles:
                renpy.not_infinite_loop(10)
                if len(tile.tileset_name) > 0:
                    img_path = tile_images[tile.tileset_name.replace(".", "_")]
                    img_size = image_size_cache.for_path(img_path)
                    if tile.sx + tile.w <= img_size[0] and tile.sy + tile.h <= img_size[1]:
                        if tile.tileset_name not in tileset_images:
                            if profile_map_generation:
                                start_time = time.time()
                            tileset_images[tile.tileset_name] = renpy.display.im.cache.get(Image(img_path))
                            if profile_map_generation:
                                print "[MAP %s BG]: Img get for tile (%s, %s) img %s took %s" % (self.map_id, tile.w, tile.h, tile.tileset_name, time.time() - start_time)
                        subsurface = tileset_images[tile.tileset_name].subsurface((tile.sx, tile.sy, tile.w, tile.h))
                        surf.blit(subsurface, (tile.dx + int(tile.x * rpgm_metadata.tile_width), tile.dy + int(tile.y * rpgm_metadata.tile_height)))
                    else:
                        print ("Image source out of bounds! '%s', imgWidth: %s, imgHeight: %s, sourceX: %s, sourceY: %s, sourceWidth: %s, sourceHeight: %s" % (tile.tileset_name, img_size[0], img_size[1], tile.sx, tile.sy, tile.w, tile.h))

            if len(self.doodads) > 0:
                doodad_images = {}

                glob_special_characters_re = re.compile('([*?[])')
                for doodad in sorted(self.doodads, key = lambda d: d['z']):
                    renpy.not_infinite_loop(10)
                    if 'switchOn' in doodad and len(doodad['switchOn']) > 0 and not all(game_state.switches.value(switch_id) for switch_id in doodad['switchOn']):
                        continue
                    if 'switchOff' in doodad and len(doodad['switchOff']) > 0 and any(game_state.switches.value(switch_id) for switch_id in doodad['switchOff']):
                        continue
                    doodad_search = glob_special_characters_re.sub(r'[\1]', rpgm_path("www/img/doodads/" + doodad['folder'] + doodad['bitmap']))
                    doodad_image_path = glob.glob(os.path.join(config.basedir, doodad_search + '.*'))[0].replace("\\", "/")
                    doodad_x_repeat = 1
                    doodad_y_repeat = 1
                    if '[' in doodad_image_path:
                        match = re.search("\[(\d+)x(\d+)]", doodad_image_path)
                        doodad_x_repeat = int(match.groups()[0])
                        doodad_y_repeat = int(match.groups()[1])

                    if doodad_image_path not in doodad_images:
                        doodad_images[doodad_image_path] = renpy.display.im.cache.get(Image(doodad_image_path))
                    doodad_surface = doodad_images[doodad_image_path]
                    doodad_image_size = doodad_surface.get_size()
                    if doodad_x_repeat != 1 or doodad_y_repeat != 1:
                        doodad_image_size = (doodad_image_size[0] / doodad_x_repeat, doodad_image_size[1] / doodad_y_repeat)
                        doodad_surface = doodad_surface.subsurface((0, 0, doodad_image_size[0], doodad_image_size[1]))

                    rendered_size = doodad_image_size
                    if doodad['scaleX'] != 100 or doodad['scaleY'] != 100:
                        x_scale_factor = doodad['scaleX'] / 100.0
                        y_scale_factor = doodad['scaleY'] / 100.0
                        if x_scale_factor > 0 and y_scale_factor > 0:
                            rendered_size = (int(doodad_image_size[0] * x_scale_factor), int(doodad_image_size[1] * y_scale_factor))
                            doodad_surface = renpy.display.pgrender.transform_scale(doodad_surface, rendered_size)
                        else:
                            # TODO - negative factors should mean the sprite is mirrored
                            print("Failed to render mirrored doodad: %s" % doodad_image_path)
                    surf.blit(
                        doodad_surface,
                        (
                            doodad['x'] - int(rendered_size[0] * doodad['anchorX']),
                            doodad['y'] - int(rendered_size[1] * doodad['anchorY'])
                        )
                    )

            try:
                if profile_map_generation:
                    print "[MAP %s BG]: Saving generated image" % self.map_id
                    start_time = time.time()
                pygame_sdl2.image.save(surf, self.cache_file)
                if profile_map_generation:
                    print "[MAP %s BG]: Finished saving generated image - took %s" % (self.map_id, time.time() - start_time)
            except pygame_sdl2.error as e:
                if e.args[0].startswith("Couldn't open"):
                    pygame_sdl2.image.save(surf, self.safe_filename_for_pygame_sdl2_save())
                else:
                    raise

    class GameMap(SelectivelyPickle):
        TILE_ID_B      = 0
        TILE_ID_C      = 256
        TILE_ID_D      = 512
        TILE_ID_E      = 768
        TILE_ID_A5     = 1536
        TILE_ID_A1     = 2048
        TILE_ID_A2     = 2816
        TILE_ID_A3     = 4352
        TILE_ID_A4     = 5888
        TILE_ID_MAX    = 8192

        FLOOR_AUTOTILE_TABLE = [
            [[2,4],[1,4],[2,3],[1,3]],[[2,0],[1,4],[2,3],[1,3]],
            [[2,4],[3,0],[2,3],[1,3]],[[2,0],[3,0],[2,3],[1,3]],
            [[2,4],[1,4],[2,3],[3,1]],[[2,0],[1,4],[2,3],[3,1]],
            [[2,4],[3,0],[2,3],[3,1]],[[2,0],[3,0],[2,3],[3,1]],
            [[2,4],[1,4],[2,1],[1,3]],[[2,0],[1,4],[2,1],[1,3]],
            [[2,4],[3,0],[2,1],[1,3]],[[2,0],[3,0],[2,1],[1,3]],
            [[2,4],[1,4],[2,1],[3,1]],[[2,0],[1,4],[2,1],[3,1]],
            [[2,4],[3,0],[2,1],[3,1]],[[2,0],[3,0],[2,1],[3,1]],
            [[0,4],[1,4],[0,3],[1,3]],[[0,4],[3,0],[0,3],[1,3]],
            [[0,4],[1,4],[0,3],[3,1]],[[0,4],[3,0],[0,3],[3,1]],
            [[2,2],[1,2],[2,3],[1,3]],[[2,2],[1,2],[2,3],[3,1]],
            [[2,2],[1,2],[2,1],[1,3]],[[2,2],[1,2],[2,1],[3,1]],
            [[2,4],[3,4],[2,3],[3,3]],[[2,4],[3,4],[2,1],[3,3]],
            [[2,0],[3,4],[2,3],[3,3]],[[2,0],[3,4],[2,1],[3,3]],
            [[2,4],[1,4],[2,5],[1,5]],[[2,0],[1,4],[2,5],[1,5]],
            [[2,4],[3,0],[2,5],[1,5]],[[2,0],[3,0],[2,5],[1,5]],
            [[0,4],[3,4],[0,3],[3,3]],[[2,2],[1,2],[2,5],[1,5]],
            [[0,2],[1,2],[0,3],[1,3]],[[0,2],[1,2],[0,3],[3,1]],
            [[2,2],[3,2],[2,3],[3,3]],[[2,2],[3,2],[2,1],[3,3]],
            [[2,4],[3,4],[2,5],[3,5]],[[2,0],[3,4],[2,5],[3,5]],
            [[0,4],[1,4],[0,5],[1,5]],[[0,4],[3,0],[0,5],[1,5]],
            [[0,2],[3,2],[0,3],[3,3]],[[0,2],[1,2],[0,5],[1,5]],
            [[0,4],[3,4],[0,5],[3,5]],[[2,2],[3,2],[2,5],[3,5]],
            [[0,2],[3,2],[0,5],[3,5]],[[0,0],[1,0],[0,1],[1,1]]
        ]

        WALL_AUTOTILE_TABLE = [
            [[2,2],[1,2],[2,1],[1,1]],[[0,2],[1,2],[0,1],[1,1]],
            [[2,0],[1,0],[2,1],[1,1]],[[0,0],[1,0],[0,1],[1,1]],
            [[2,2],[3,2],[2,1],[3,1]],[[0,2],[3,2],[0,1],[3,1]],
            [[2,0],[3,0],[2,1],[3,1]],[[0,0],[3,0],[0,1],[3,1]],
            [[2,2],[1,2],[2,3],[1,3]],[[0,2],[1,2],[0,3],[1,3]],
            [[2,0],[1,0],[2,3],[1,3]],[[0,0],[1,0],[0,3],[1,3]],
            [[2,2],[3,2],[2,3],[3,3]],[[0,2],[3,2],[0,3],[3,3]],
            [[2,0],[3,0],[2,3],[3,3]],[[0,0],[3,0],[0,3],[3,3]]
        ]

        WATERFALL_AUTOTILE_TABLE = [
            [[2,0],[1,0],[2,1],[1,1]],[[0,0],[1,0],[0,1],[1,1]],
            [[2,0],[3,0],[2,1],[3,1]],[[0,0],[3,0],[0,1],[3,1]]
        ]

        def __init__(self, state, map_id):
            self.state = state
            self.map_id = map_id
            self.event_location_overrides = {}
            self.event_page_overrides = {}

        def initialize_erased_events(self):
            self.erased_events = {}
            erased_events_from_metadata = rpgm_game_data.get('erased_events', None)
            if erased_events_from_metadata:
                for event_id in erased_events_from_metadata.get(str(self.map_id), []):
                    self.erased_events[event_id] = True

        def update_for_transfer(self):
            self.tileset_id_override = None
            self.event_location_overrides.clear()
            self.event_page_overrides.clear()
            self.initialize_erased_events()
            self.hide_unpleasant_moving_obstacles()
            map_data = self.data()
            if len(map_data['bgm']['name']) > 0:
                self.state.queue_background_music(map_data['bgm']['name'], map_data['bgm']['volume'])
            if len(map_data['bgs']['name']) > 0:
                self.state.queue_background_sound(map_data['bgs']['name'], map_data['bgs']['volume'])

        def hide_unpleasant_moving_obstacles(self):
            if GameIdentifier().is_ics1() or GameIdentifier().is_the_artifact_part_3():
                for e in self.active_events():
                    for page in reversed(e['pages']):
                        if self.meets_conditions(e, page['conditions']):
                            if page['trigger'] != 4:
                                continue

                            for command in page['list']:
                                if command['code'] != 205:
                                    continue

                                event_id = command['parameters'][0]
                                if event_id < 0:
                                    continue
                                elif event_id == 0:
                                    event_id = e['id']

                                event = self.state.map.find_event_at_index(event_id)
                                if event:
                                    event.hide_if_unpleasant_moving_obstacle()

        def data(self):
            return game_file_loader.json_file(rpgm_data_path("Map%03d.json" % self.map_id))

        def background_image(self):
            if not hasattr(self, '_background_image') or isinstance(self._background_image, GameMapBackground):
                if not os.path.exists(self.background_image_cache_file_absolute()):
                    if profile_map_generation:
                        print "[MAP %s BG]: Generating background image" % self.map_id
                        start_time = time.time()
                    self.generate_background_image()
                    if profile_map_generation:
                        print "[MAP %s BG]: Finished background image - took %s" % (self.map_id, time.time() - start_time)
                self._background_image = Image(self.background_image_cache_file())
            if not hasattr(self, 'image_width'):
                image_sizes = [renpy.image_size(self._background_image)]
                if self.overlay_image('ground'):
                    image_sizes.append(renpy.image_size(self.overlay_image('ground')))
                if self.overlay_image('parallax'):
                    image_sizes.append(renpy.image_size(self.overlay_image('parallax')))
                self.image_width = max(zip(*image_sizes)[0])
                self.image_height = max(zip(*image_sizes)[1])

            return self._background_image

        def background_image_cache_file(self):
            doodads = self.doodads()
            doodad_descriptions = []
            if len(doodads) > 0:
                switches_on = Set()
                switches_off = Set()
                for d in doodads:
                    if 'switchOn' in d and len(d['switchOn']) > 0:
                        for switch_id in d['switchOn']:
                            if self.state.switches.value(switch_id):
                                switches_on.add(switch_id)
                    if 'switchOff' in d and len(d['switchOff']) > 0:
                        for switch_id in d['switchOff']:
                            if not self.state.switches.value(switch_id):
                                switches_off.add(switch_id)
                if len(switches_on) > 0:
                    doodad_descriptions.append('-'.join(["switchOn%s" % switch_id for switch_id in list(switches_on)]))
                if len(switches_off) > 0:
                    doodad_descriptions.append('-'.join(["switchOff%s" % switch_id for switch_id in list(switches_off)]))

            if hasattr(self, 'tileset_id_override') and self.tileset_id_override:
                basename = ('Map%03d_tileset%s.png' % (self.map_id, self.tileset_id_override))
            elif len(doodad_descriptions) > 0:
                basename = ('Map%03d%s.png' % (self.map_id, '-'.join(doodad_descriptions)))
            else:
                basename = ('Map%03d.png' % self.map_id)

            return os.path.join(map_cache_directory, basename).replace("\\", "/")

        def background_image_cache_file_absolute(self):
            return os.path.join(config.basedir, self.background_image_cache_file()).replace("\\", "/")

        def generate_background_image(self):
            bg = GameMapBackgroundGenerator(self.map_id, self.tiles(), self.doodads(), self.background_image_cache_file_absolute())
            bg.save()

        def parallax_image(self):
            if not hasattr(self, '_parallax_image'):
                parallax_name = self.data()['parallaxName']
                if parallax_name and len(parallax_name) > 0:
                    self._parallax_image = parallax_images[rpgm_parallax_name(parallax_name)]
                else:
                    self._parallax_image = None

            return self._parallax_image

        def overlay_image(self, image_type):
            plugin = game_file_loader.plugin_data_exact('OrangeOverlay')
            if not plugin:
                return None

            if not hasattr(self, '_overlay_images'):
                self._overlay_images = {}

            if image_type not in self._overlay_images:
                has_overlay_of_type = re.search('<%s>' % image_type, self.data()['note'])
                if has_overlay_of_type:
                    self._overlay_images[image_type] = os.path.join(config.basedir, rpgm_path('www/img/overlays'), image_type + 's', "%s%s.png" % (image_type, self.map_id)).replace("\\", "/")
                else:
                    self._overlay_images[image_type] = None

            return self._overlay_images[image_type]

        def clicky_command(self, command):
           return (command['code'] == 108) and (command['parameters'][0] == 'click_activate!')

        def clicky_event(self, event, page):
            if event['note'] == 'click_activate!':
                return True

            first_event_command = event['pages'][0]['list'][0]
            if first_event_command and self.clicky_command(first_event_command):
                return True

            first_page_command = page['list'][0]
            return first_page_command and self.clicky_command(first_page_command)

        def forced_clicky(self):
            if GameIdentifier().is_milfs_villa():
                # Bench keys at beach
                if self.state.variables.value(53) == 1 or self.state.variables.value(54) == 1:
                    return True
                # Bottom box in tool shed
                elif self.map_id == 12 and self.state.variables.value(41) == 1:
                    return True
            return False

        def ignored_clicky_page(self, page):
            # ZONE OF HACKS
            if GameIdentifier().is_milfs_villa():
                if len(page['list']) > 2 and page['list'][2]['parameters'][0] == "<Mini Label: Pool>":
                    return True
            return False

        def active_events(self):
            if not hasattr(self, 'erased_events'):
                self.initialize_erased_events()
            return (e for e in self.data()['events'] if e and e['id'] not in self.erased_events)

        def is_clicky(self, player_x, player_y):
            if self.forced_clicky():
                return True

            has_events = False
            some_event_is_clicky = False
            all_events_are_clicky = True
            for e in self.active_events():
                for page in reversed(e['pages']):
                    if self.meets_conditions(e, page['conditions']):
                        has_events = True
                        if self.clicky_event(e, page) and not self.ignored_clicky_page(page):
                            some_event_is_clicky = True
                        else:
                            all_events_are_clicky = False

            if not has_events:
                return False

            return all_events_are_clicky or (some_event_is_clicky and not self.can_move(player_x, player_y))

        def is_tile_a1(self, tile_id):
            return tile_id >= GameMap.TILE_ID_A1 and tile_id < GameMap.TILE_ID_A2

        def is_tile_a2(self, tile_id):
            return tile_id >= GameMap.TILE_ID_A2 and tile_id < GameMap.TILE_ID_A3

        def is_tile_a3(self, tile_id):
            return tile_id >= GameMap.TILE_ID_A3 and tile_id < GameMap.TILE_ID_A4

        def is_tile_a4(self, tile_id):
            return tile_id >= GameMap.TILE_ID_A4 and tile_id < GameMap.TILE_ID_MAX

        def is_tile_a5(self, tile_id):
            return tile_id >= GameMap.TILE_ID_A5 and tile_id < GameMap.TILE_ID_A1

        def tileset_id(self):
            if hasattr(self, 'tileset_id_override') and self.tileset_id_override:
                return self.tileset_id_override
            return self.data()['tilesetId']

        def flags(self, tile_id):
            flag_data = self.state.tilesets()[self.tileset_id()]['flags']
            if len(flag_data) > tile_id:
                return flag_data[tile_id]
            else:
                return 0

        def is_table_tile(self, tile_id):
            return self.is_tile_a2(tile_id) and (self.flags(tile_id) & 0x80)

        def normal_tile_data(self, tile_id):
            if self.is_tile_a5(tile_id):
                set_number = 4
            else:
                set_number = 5 + tile_id // 256

            sx = ((tile_id // 128) % 2 * 8 + tile_id % 8) * rpgm_metadata.tile_width
            sy = ((tile_id % 256 // 8) % 16) * rpgm_metadata.tile_height

            return GameTile(tile_id = tile_id, sx = sx, sy = sy, dx = 0, dy = 0, w = rpgm_metadata.tile_width, h = rpgm_metadata.tile_height, set_number = set_number)

        def auto_tile_data(self, tile_id):
            result = []
            autotile_table = GameMap.FLOOR_AUTOTILE_TABLE
            kind = (tile_id - GameMap.TILE_ID_A1) // 48
            shape = (tile_id - GameMap.TILE_ID_A1) % 48
            tx = kind % 8
            ty = kind // 8
            bx = 0
            by = 0
            set_number = 0
            is_table = False

            if self.is_tile_a1(tile_id):
                animation_frame = 0
                water_surface_index = [0, 1, 2, 1][animation_frame % 4];
                set_number = 0
                if kind == 0:
                    bx = water_surface_index * 2
                    by = 0;
                elif kind == 1:
                    bx = water_surface_index * 2
                    by = 3
                elif kind == 2:
                    bx = 6
                    by = 0
                elif kind == 3:
                    bx = 6
                    by = 3
                else:
                    bx = (tx // 4) * 8
                    by = ty * 6 + (tx // 2) % 2 * 3
                    if kind % 2 == 0:
                        bx += water_surface_index * 2
                    else:
                        bx += 6
                        autotile_table = GameMap.WATERFALL_AUTOTILE_TABLE
                        by += animation_frame % 3
            elif self.is_tile_a2(tile_id):
                set_number = 1
                bx = tx * 2
                by = (ty - 2) * 3
                is_table = self.is_table_tile(tile_id)
            elif self.is_tile_a3(tile_id):
                set_number = 2
                bx = tx * 2
                by = (ty - 6) * 2
                autotile_table = GameMap.WALL_AUTOTILE_TABLE
            elif self.is_tile_a4(tile_id):
                set_number = 3
                bx = tx * 2
                by = int(math.floor((ty - 10) * 2.5 + (0.5 if ty % 2 == 1 else 0)))
                if ty % 2 == 1:
                    autotile_table = GameMap.WALL_AUTOTILE_TABLE

            table = autotile_table[shape]

            if table:
                w1 = rpgm_metadata.tile_width // 2
                h1 = rpgm_metadata.tile_height // 2
                for i in xrange(0, 4):
                    qsx = table[i][0]
                    qsy = table[i][1]
                    sx1 = (bx * 2 + qsx) * w1
                    sy1 = (by * 2 + qsy) * h1
                    dx1 = (i % 2) * w1
                    dy1 = (i // 2) * h1
                    if is_table and (qsy == 1 or qsy == 5):
                        qsx2 = qsx
                        qsy2 = 3
                        if qsy == 1:
                            qsx2 = [0,3,2,1][qsx]
                        sx2 = (bx * 2 + qsx2) * w1
                        sy2 = (by * 2 + qsy2) * h1
                        result.append(GameTile(tile_id = tile_id, sx = sx2, sy = sy2, dx = dx1, dy = dy1, w = w1, h = h1, set_number = set_number))
                        dy1 += h1 // 2
                        result.append(GameTile(tile_id = tile_id, sx = sx1, sy = sy2, dx = dx1, dy = dy1, w = w1, h = h1/2, set_number = set_number))
                    else:
                        result.append(GameTile(tile_id = tile_id, sx = sx1, sy = sy1, dx = dx1, dy = dy1, w = w1, h = h1, set_number = set_number))

            return result

        def is_visible_tile(self, tile_id):
            return tile_id > 0 and tile_id < GameMap.TILE_ID_MAX

        def forced_passible(self, x, y):
            if GameIdentifier().is_milfs_villa():
                if self.map_id == 1:
                    # Opening scene roof
                    if x == 30 and y == 10:
                        return True

                    if x == 29 and y in [12, 13, 14]:
                        return True
                elif self.map_id == 3:
                    # Main house roof
                    if x in [44, 45, 50, 51] and y == 19:
                        return True

                    if x == 40 and y in [15, 16, 17, 18]:
                        return True

                    if x == 39 and y == 12:
                        return True

                    if x == 30 and y == 12:
                        return True

                    if x in [23, 26] and y in [16, 17, 18]:
                        return True
                elif self.map_id == 49:
                    if x in [29] and y in [16, 17]:
                        return True

            elif GameIdentifier().is_ics1():
                # Streetlights in ICS1 - this is an actual game bug in the RPGM version
                # where you can zone into a new map and be facing an impassible streetlight
                # and your only choice is to go back and try to go forward again on a new y
                if self.map_id == 33:
                    if (x, y) in [(53, 1), (53, 7)]:
                        return True
                if self.map_id == 43:
                    if (x, y) in [(58,23), (58, 29)]:
                        return True
            return False

        def tile_id(self, x, y, z):
            try:
                return self.data()['data'][(z * self.height() + y) * self.width() + x]
            except IndexError:
                return 0

        def layered_tiles(self, x, y):
            tiles = [];
            for i in xrange(0,4):
                tiles.push(self.tile_id(x, y, 3 - i))
            return tiles

        def terrain_tag(self, x, y):
            if self.is_valid(x, y):
                for tile_id in self.layered_tiles(x, y):
                    tag = self.flags(tile_id) >> 12
                    if tag > 0:
                        return tag
            return 0

        def can_pass(self, x, y, direction):
            delta = GameDirection.delta_for_direction(direction)
            return (not self.is_impassible(x, y, direction)) and (not self.is_impassible(x + delta[0], y + delta[1], GameDirection.reverse_direction(direction)))

        def can_pass_diagonally(self, x, y, horz, vert):
            horiz_delta = GameDirection.delta_for_direction(horz)
            vert_delta = GameDirection.delta_for_direction(vert)
            x2 = x + horiz_delta[0]
            y2 = y + vert_delta[1]
            if self.can_pass(x, y, vert) and self.can_pass(x, y2, horz):
                return True
            if self.can_pass(x, y, horz) and self.can_pass(x2, y, horz):
                return True
            return False

        def is_impassible(self, x, y, direction = None):
            if direction:
                direction_bits = [1 << direction / 2 - 1]
            else:
                direction_bits = [1, 2, 4, 8]

            if self.forced_passible(x, y):
                return False

            tile_region = self.tile_region(x, y)
            yep_region_restrictions = game_state.yep_region_restrictions()
            if yep_region_restrictions:
                if tile_region in yep_region_restrictions.player_restricted_regions:
                    return True
                elif tile_region in yep_region_restrictions.player_allowed_regions:
                    return False

            # Technically this only applies if the Restrict_with_Region plugin is installed,
            # and the region ids are configurable, but it's simplest to just assume any
            # VX Ace game that uses these region ids intended them to be impassible.
            if rpgm_metadata.is_pre_mv_version and (tile_region in [61, 62]):
                return True

            tile_ids = [self.tile_id(x, y, z) for z in xrange(3, -1, -1)]
            for tile_id in tile_ids:
                flag = self.flags(tile_id)
                if ((flag & 0x10) != 0):
                    continue
                if any([(flag & direction_bit) == 0 for direction_bit in direction_bits]):
                    return False
                if all([(flag & direction_bit) == direction_bit for direction_bit in direction_bits]):
                    return True

            return False

        def is_valid_x_y(self, x, y):
            return x >= 0 and x < self.width() and y >= 0 and y < self.height()

        def is_counter(self, x, y):
            tile_ids = [self.tile_id(x, y, z) for z in xrange(3, -1, -1)]
            for tile_id in tile_ids:
                flag = self.flags(tile_id)
                if ((flag & 0x80) != 0):
                    return True
            return False

        def height(self):
            return self.data()['height']

        def width(self):
            return self.data()['width']

        def impassible_tiles(self):
            reachability_grid = self.reachability_grid_for_current_position()
            result = []
            for x in xrange(0, self.width()):
                for y in xrange(0, self.height()):
                    if reachability_grid[y][x] == 0:
                        result.append((x, y))

            return result

        def path_from_destination(self, current_x, current_y, dest_x, dest_y):
            if profile_timings:
                started = time.time()

            reachability_grid = self.reachability_grid_for_current_position()
            frontier = PriorityQueue()
            start = (current_x, current_y)
            came_from = {start: None}
            frontier.put((0, (current_x, current_y, game_state.player_direction)))
            total_locations_evaluated = 0

            max_x = self.width() - 1
            max_y = self.height() - 1

            while not frontier.empty():
                priority, current = frontier.get()
                total_locations_evaluated += 1

                for adjacent_coord in self.adjacent_coords(current[0], current[1], max_x, max_y):
                    ax, ay, adirection = adjacent_coord
                    if (ax, ay) in came_from:
                        continue

                    if ax == dest_x and ay == dest_y:
                        if profile_timings:
                            print "pathfinding took %s, evaluating %s locations" % (time.time() - started, total_locations_evaluated)
                        came_from[(ax, ay)] = current
                        sq = (ax, ay, adirection)
                        path = [sq]
                        while True:
                            prev = came_from[(sq[0], sq[1])]
                            if not prev:
                                return path
                            else:
                                path.append(prev)
                                sq = prev

                    if reachability_grid[ay][ax] == 3 and (not self.is_impassible(current[0], current[1], adirection) and not self.is_impassible(ax, ay, GameDirection.reverse_direction(adirection))):
                        came_from[(ax, ay)] = current
                        priority = abs(dest_x - ax) + abs(dest_y - ay)
                        frontier.put((priority, (ax, ay, adirection)))

            return None

        def first_open_adjacent_square(self, around_x ,around_y):
            directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            for d in directions:
                x, y = around_x + d[0], around_y + d[1]
                if not self.find_event_for_location(x, y) and not self.is_impassible(x, y):
                    return (x, y)
            return None

        def can_move(self, x, y):
            event_on_player = self.find_event_for_location(x, y)
            if event_on_player and (not event_on_player.page['through']) and event_on_player.page['priorityType'] == 1:
                return False

            max_x = self.width() - 1
            max_y = self.height() - 1

            reachability_grid = self.reachability_grid_for_current_position()
            for adjacent_coord in self.adjacent_coords(game_state.player_x, game_state.player_y, max_x, max_y):
                ax, ay, adirection = adjacent_coord
                if reachability_grid[ay][ax] == 3 and (not self.is_impassible(game_state.player_x, game_state.player_y, adirection) and not self.is_impassible(ax, ay, GameDirection.reverse_direction(adirection))):
                    return True

            return False

        def surrounded_by_events(self, x, y):
            max_x = self.width() - 1
            max_y = self.height() - 1

            count = 0
            reachability_grid = self.reachability_grid_for_current_position()
            for adjacent_coord in self.adjacent_coords(x, y, max_x, max_y):
                ax, ay, adirection = adjacent_coord
                if reachability_grid[ay][ax] == 2:
                    count += 1

            return count == 4

        def can_move_vector(self, x, y, delta_x, delta_y):
            new_x, new_y = x + delta_x, y + delta_y
            if delta_x == 0 and delta_y == -1:
                direction = GameDirection.UP
            elif delta_x == 0 and delta_y == 1:
                direction = GameDirection.DOWN
            elif delta_x == -1 and delta_y == 0:
                direction = GameDirection.LEFT
            elif delta_x == 1 and delta_y == 0:
                direction = GameDirection.RIGHT

            return self.can_pass(x, y, direction)

        def tile_region(self, x, y):
            region_z = 5
            return self.tile_id(x, y, region_z)

        def tiles(self):
            if profile_map_generation:
                start_time = time.time()
            result = []
            width = self.data()['width']
            height = self.data()['height']
            for x in xrange(0, width):
                for y in xrange(0, height):
                    for z in xrange(0, 4):
                        tile_id = self.data()['data'][(z * height + y) * width + x]

                        if not self.is_visible_tile(tile_id):
                            continue

                        set_number = 0

                        all_tiles = []

                        # "autotiles"
                        if tile_id > GameMap.TILE_ID_A1:
                            all_tiles = self.auto_tile_data(tile_id)

                        # "normal tiles"
                        else:
                            all_tiles = [self.normal_tile_data(tile_id)]

                        for tile in all_tiles:
                            tile.x = x
                            tile.y = y
                            tileset_names = self.state.tilesets()[self.tileset_id()]['tilesetNames']
                            if len(tileset_names) > tile.set_number:
                                tile.tileset_name = tileset_names[tile.set_number]

                                result.append(tile)

            if profile_map_generation:
                print "[MAP %s BG]: Enumerating tiles took %s" % (self.map_id, time.time() - start_time)

            return result

        def doodad_data(self):
            if hasattr(self, '_doodad_data'):
                return self._doodad_data

            self._doodad_data = game_file_loader.plugin_data_exact('YEP_GridFreeDoodads')
            return self._doodad_data

        def doodads(self):
            if not self.doodad_data():
                return []
            doodad_json = game_file_loader.json_file(rpgm_data_path("Doodads.json"))
            if not doodad_json or len(doodad_json) < self.map_id + 1:
                return []

            map_doodads = doodad_json[self.map_id]
            if not map_doodads:
                return []
            return map_doodads

        def character_sprite(self, image_data):
            img_base_filename = image_data['characterName'].replace(".", "_")

            character_prefix_match = re.match("^([!$])+", img_base_filename)
            is_big_character = False
            if character_prefix_match and '$' in character_prefix_match.groups()[0]:
                is_big_character = True

            is_object_character = False
            if character_prefix_match and '!' in character_prefix_match.groups()[0]:
                is_object_character = True

            img_size = image_size_cache.for_path(character_images[img_base_filename.lower()])

            pw = img_size[0] / 12
            ph = img_size[1] / 8

            n = image_data['characterIndex']

            character_block_x = n % 4 * 3
            character_block_y = (n // 4) * 4
            character_pattern_x = image_data['pattern'] if (image_data['pattern'] < 3) else 1
            character_pattern_y = (image_data['direction'] - 2) / 2
            if is_big_character:
                pw = img_size[0] / 3
                ph = img_size[1] / 4
                character_block_x = 0
                character_block_y = 0

            sy = (character_block_y + character_pattern_y) * ph
            if is_object_character and 'stepAnime' in image_data and image_data['stepAnime']:
                img_file = character_images[img_base_filename.lower()]
                picture_transitions = []
                for pattern_x in (0, 1, 2, 1):
                    picture_transitions.append(
                        Transform(
                            child = im.Crop(img_file, ((character_block_x + pattern_x) * pw, sy, pw, ph)),
                            xpos = 0,
                            ypos = 0,
                            size = (pw, ph)
                        )
                    )
                    animation_frames = (9 - image_data['moveSpeed']) * 3
                    picture_transitions.append(animation_frames / animation_fps)
                    picture_transitions.append(None)
                img = RpgmAnimation.create(*picture_transitions)
            else:
                sx = (character_block_x + character_pattern_x) * pw
                img = im.Crop(character_images[img_base_filename.lower()], (sx, sy, pw, ph))

            shift_y = 0 if is_object_character else 6
            return (img, pw, ph, shift_y)

        def tile_sprite(self, image_data):
            tileset_names = self.state.tilesets()[self.tileset_id()]['tilesetNames']
            set_number = 5 + (image_data['tileId'] // 256)
            tileset_name = tileset_names[set_number]

            sx = ((image_data['tileId'] // 128) % 2 * 8 + image_data['tileId'] % 8) * rpgm_metadata.tile_width
            sy = ((image_data['tileId'] % 256) // 8) % 16 * rpgm_metadata.tile_height

            img = im.Crop(tile_images[tileset_name.replace(".", "_")], (sx, sy, rpgm_metadata.tile_width, rpgm_metadata.tile_height))
            return (img,)

        def sprites(self):
            result = []

            lead_actor_id = self.state.party.leader()
            if lead_actor_id:
                player_character_actor = self.state.actors.by_index(lead_actor_id)
                if player_character_actor.get_property('characterName') != '':
                    player_character_sprite_data = {
                        "characterName": player_character_actor.get_property('characterName'),
                        "characterIndex": player_character_actor.get_property('characterIndex'),
                        "pattern": 0,
                        "direction": game_state.player_direction
                    }
                    result.append((game_state.player_x, game_state.player_y) + self.character_sprite(player_character_sprite_data))

            for e in self.active_events():
                for reverse_page_index, page in enumerate(reversed(e['pages'])):
                    if self.meets_conditions(e, page['conditions']):
                        loc = self.event_location(e)
                        image_data = page['image']
                        page_index = (len(e['pages']) - 1) - reverse_page_index
                        event_sprite_data = self.event_sprite_data(e, page, page_index)
                        if event_sprite_data.get('transparent', False):
                            break
                        if event_sprite_data['characterName'] != '':
                            character_sprite_data = self.character_sprite(event_sprite_data)
                            result.append(loc + character_sprite_data)
                        elif image_data['tileId'] != 0:
                            tile_sprite_data = self.tile_sprite(image_data)
                            result.append(loc + tile_sprite_data)
                        break
            return result

        def event_is_special(self, e):
            return bool(re.search('weightSwitch', e['note']))

        def page_is_projectile_target(self, e, page):
            if GalvMapProjectiles.plugin_active():
                return GalvMapProjectiles.is_projectile_page(page)

            return False

        def find_event_data_at_index(self, event_index):
            if not hasattr(self, 'erased_events'):
                self.initialize_erased_events()
            if event_index in self.erased_events:
                return None
            e = self.data()['events'][event_index]
            if e['id'] in self.erased_events:
                return None
            return e

        def find_event_at_index(self, event_index):
            e = self.find_event_data_at_index(event_index)
            if not e:
                return None
            for reverse_page_index, page in enumerate(reversed(e['pages'])):
                if self.meets_conditions(e, page['conditions']):
                    page_index = (len(e['pages']) - 1) - reverse_page_index
                    return GameEvent(self.state, self.map_id, e, page, page_index)
            return None

        def find_event_for_location(self, x, y, only_special = False):
            candidates = []
            for e in self.active_events():
                loc = self.event_location(e)
                if loc[0] == x and loc[1] == y:
                    for reverse_page_index, page in enumerate(reversed(e['pages'])):
                        if self.meets_conditions(e, page['conditions']) and page['trigger'] != 3:
                            page_index = (len(e['pages']) - 1) - reverse_page_index
                            if ((not only_special) and self.event_is_special(e)):
                                return None
                            if debug_events:
                                print "DEBUG_EVENTS: event %s, page -%s / %s" % (e['id'], reverse_page_index, page_index)
                            candidates.append(GameEvent(self.state, self.map_id, e, page, page_index))
                            break

            # Ensure that player / event touch events that have commands get priority over parallel / action button events
            return next((event for event in reversed(sorted(candidates, key=lambda candidate_event: (candidate_event.page['trigger'] in [1,2], self.has_commands(candidate_event.page))))), None)

        def boring_auto_trigger_page(self, page):
            # NOTE: the real RPGM event loop runs every auto trigger event, it just happens to be
            # that if an event doesn't trigger a 'wait' (see 'updateWaitMode' in rpgm code) the interpreter
            # continues on to run the rest of the auto trigger events before re-starting from the first auto trigger
            # event.
            #
            # Since rpgm2renpy doesn't have awareness of this waitMode stuff, in practice, this means an
            # auto trigger event that only does non-visual things like toggle switches can cause an infinite
            # loop as it continually re-tries itself. Usually game authors write their auto trigger events
            # such that they toggle a switch that prevents them from being re-run, but some games rely on this
            # only-rerun-when-waitMode-triggered behavior.

            # The hack for now is to ignore blank auto trigger events or those that contain only comments,
            # but this is sketchy because it doesn't cover all the cases that can do an infinite loop, and
            # isn't technically correct in the case where a plugin hacks in some user-facing behavior for comments.
            # The alternative would be for rpgm2renpy to have a better awareness of what commands trigger
            # a 'waitMode', but that's more work.
            return Set([command['code'] for command in page['list']]).issubset(Set([0, 108, 408]))

        def find_auto_trigger_event(self):
            for e in self.active_events():
                for reverse_page_index, page in enumerate(reversed(e['pages'])):
                    if self.meets_conditions(e, page['conditions']):
                        page_index = (len(e['pages']) - 1) - reverse_page_index
                        if page['trigger'] == 3 and not self.boring_auto_trigger_page(page):
                            return GameEvent(self.state, self.map_id, e, page, page_index)
                        else:
                            break
            return None

        def possible_parallel_event_indices(self):
            if not hasattr(self, '_possible_parallel_event_indices'):
                self._possible_parallel_event_indices = []
                for index, e in enumerate(self.data()['events']):
                    if e and any(p['trigger'] == 4 for p in e['pages']):
                        self._possible_parallel_event_indices.append(index)

            return self._possible_parallel_event_indices

        def parallel_event_pages(self):
            result = []
            for event_id in self.possible_parallel_event_indices():
                possible_parallel_event = self.parallel_event_at_index(event_id)
                if possible_parallel_event:
                    result.append((
                        possible_parallel_event.event_data['id'],
                        possible_parallel_event.page_index,
                        self.has_conditional(possible_parallel_event.page)
                    ))
            return result

        def parallel_events(self):
            if not hasattr(self, 'erased_events'):
                self.initialize_erased_events()
            result = []
            all_events = self.data()['events']
            for index in self.possible_parallel_event_indices():
                e = all_events[index]
                if e['id'] in self.erased_events:
                    continue

                for reverse_page_index, page in enumerate(reversed(e['pages'])):
                    if self.meets_conditions(e, page['conditions']):
                        if page['trigger'] == 4:
                            page_index = (len(e['pages']) - 1) - reverse_page_index
                            if self.has_commands(page):
                                result.append(GameEvent(self.state, self.map_id, e, page, page_index))
                        break
            return result

        def parallel_event_at_index(self, event_index):
            if not hasattr(self, 'erased_events'):
                self.initialize_erased_events()
            e = self.data()['events'][event_index]
            if e and e['id'] not in self.erased_events:
                for reverse_page_index, page in enumerate(reversed(e['pages'])):
                    if self.meets_conditions(e, page['conditions']):
                        if page['trigger'] == 4:
                            page_index = (len(e['pages']) - 1) - reverse_page_index
                            return GameEvent(self.state, self.map_id, e, page, page_index)
                        else:
                            break
            return None

        def meets_conditions(self, event_data, conditions):
            if conditions['switch1Valid']:
                if not self.state.switches.value(conditions['switch1Id']):
                    return False

            if conditions['switch2Valid']:
                if not self.state.switches.value(conditions['switch2Id']):
                    return False

            if conditions['variableValid']:
                if conditions['variableValue'] < 0 and rpgm_game_data.get('has_negative_variable_value_hack', None):
                    if self.state.variables.value(conditions['variableId']) != abs(conditions['variableValue']):
                        return False
                else:
                    if self.state.variables.value(conditions['variableId']) < conditions['variableValue']:
                        return False

            if conditions['selfSwitchValid']:
                key = (self.state.map.map_id, event_data['id'], conditions['selfSwitchCh'])
                if self.state.self_switches.value(key) != True:
                    return False

            if conditions['itemValid']:
                item = self.state.items.by_id(conditions['itemId'])
                if not self.state.party.has_item(item):
                    return False

            if conditions['actorValid']:
                actor = self.state.actors.by_index(conditions['actorId'])
                if not self.state.party.has_actor(actor):
                    return False

            return True

        def has_commands(self, page):
            for command in page['list']:
                if command['code'] not in [0, 108, 250]:
                    return True
            return False

        def has_conditional(self, page):
            for command in page['list']:
                if command['code'] == 111:
                    return True
            return False

        def interesting_move_route(self, page):
            has_commands = False
            has_wait = False
            for command in page['list']:
                if command['code'] == 45:
                    if GalvEventSpawnTimers.has_timer(command):
                        return True
                if command['code'] not in [0]:
                    has_commands = True
                elif command['code'] == 15:
                    has_wait = True
            if not has_commands:
                return False
            if not page['repeat']:
                return True
            return has_wait

        def page_label(self, page):
            for command in page['list']:
                if command['code'] == 408:
                    match = re.match('<Mini Label:(.*?)>', command['parameters'][0])
                    if match:
                        return match.groups()[0]
            return None

        def hide_buggy_event(self, event, page):
            if GameIdentifier().is_milfs_villa():
                return GameSpecificCodeMilfsVilla().hide_buggy_event(self, event, page)
            return False

        def adjacent_coords(self, x, y, max_x, max_y):
            result = []
            if x > 0:
                result.append((x - 1, y, GameDirection.LEFT))
            if y > 0:
                result.append((x, y - 1, GameDirection.UP))
            if x < max_x:
                result.append((x + 1, y, GameDirection.RIGHT))
            if y < max_y:
                result.append((x, y + 1, GameDirection.DOWN))
            return result

        def reachability_grid_for_current_position(self):
            return self.reachability_grid(
                game_state.player_x,
                game_state.player_y,
                self.map_options(game_state.player_x, game_state.player_y, ignore_clicky = True, include_parallel = True)
            )

        def reachability_grid(self, player_x, player_y, event_coords):
            player_position = (player_x, player_y)
            events_with_pages = tuple((coord.x, coord.y, coord.page_index, coord.through) for coord in event_coords)
            cached_grid = rpgm_reachability_grid_cache.get(player_position, events_with_pages)
            if cached_grid:
                if debug_reachability_grid:
                    print "REACHABILITY GRID FOR MAP %s / %s LOCS: Cache hit!" % (self.map_id, len(event_coords))
                return cached_grid
            else:
                if debug_reachability_grid:
                    print "REACHABILITY GRID FOR MAP %s / %s LOCS: Cache miss!" % (self.map_id, len(event_coords))

            if profile_timings:
                started = time.time()
            # 0 = unknown / impassible
            # 2 = impassible event
            # 3 = passible

            reachability_grid = [[0 for x in xrange(self.width())] for y in xrange(self.height())]

            for map_clickable in event_coords:
                if hasattr(map_clickable, 'walk_destination') and map_clickable.walk_destination:
                    continue

                # An event is generally considered passable unless it matches some of these conditions:

                # Consider an event impassible if it is 'solid' (on the same level as a player and not tagged as 'through')
                if not hasattr(map_clickable, 'solid') or map_clickable.solid:
                    reachability_grid[map_clickable.y][map_clickable.x] = 2
                # Consider an event impassible if it is triggered on touch (not action) and has any notable commands
                # this may become untenable depending on how much the definition of has_commands needs to expand
                elif (hasattr(map_clickable, 'touch_trigger') and map_clickable.touch_trigger) and (hasattr(map_clickable, 'has_commands') and map_clickable.has_commands) and not (hasattr(map_clickable, 'through') and map_clickable.through):
                    reachability_grid[map_clickable.y][map_clickable.x] = 2

            max_x = self.width() - 1
            max_y = self.height() - 1

            coords_to_mark = [(player_x, player_y)]
            while len(coords_to_mark) > 0:
                renpy.not_infinite_loop(10)
                mx, my = coords_to_mark.pop()
                reachability_grid[my][mx] = 3
                for adjacent_coord in self.adjacent_coords(mx, my, max_x, max_y):
                    ax, ay, adirection = adjacent_coord
                    if reachability_grid[ay][ax] == 0 and (not self.is_impassible(mx, my, adirection) and not self.is_impassible(ax, ay, GameDirection.reverse_direction(adirection))):
                        coords_to_mark.append(adjacent_coord[0:2])

            rpgm_reachability_grid_cache.set(player_position, events_with_pages, reachability_grid)
            if profile_timings:
                print "Reachability grid took %s" % (time.time() - started)

            return reachability_grid

        def assign_reachability(self, player_x, player_y, event_coords):
            reachability_grid = self.reachability_grid(player_x, player_y, event_coords)

            max_x = self.width() - 1
            max_y = self.height() - 1

            for map_clickable in event_coords:
                map_clickable.reachable = False
                if hasattr(map_clickable, 'clicky') and map_clickable.clicky:
                    map_clickable.reachable = True
                    continue

                for adjacent_coord in self.adjacent_coords(map_clickable.x, map_clickable.y, max_x, max_y):
                    ax, ay, adirection = adjacent_coord
                    if reachability_grid[ay][ax] == 3:
                        map_clickable.reachable = True
                        break
                    elif self.is_counter(ax, ay):
                        delta = GameDirection.delta_for_direction(adirection)
                        beyond_counter_x = ax + delta[0]
                        beyond_counter_y = ay + delta[1]
                        if reachability_grid[beyond_counter_y][beyond_counter_x] == 3:
                            map_clickable.reachable_via_counter = (beyond_counter_x, beyond_counter_y)
                            map_clickable.reachable = True
                            break

        def event_location(self, event_data):
            if event_data['id'] in self.event_location_overrides:
                return self.event_location_overrides[event_data['id']]
            else:
                if 'x' in event_data:
                    return (event_data['x'], event_data['y'])

        def override_tileset(self, tileset_id):
            self.tileset_id_override = tileset_id
            if hasattr(self, '_background_image'):
                delattr(self, '_background_image')

        def override_event_location(self, event_data, loc):
            if not hasattr(self, 'event_location_overrides'):
                self.event_location_overrides = {}
            self.event_location_overrides[event_data['id']] = loc

        def overrides_for_event_page(self, event_id, page_index):
            if event_id not in self.event_page_overrides:
                self.event_page_overrides[event_id] = {}
            existing_page_index = self.event_page_overrides[event_id].get('pageIndex', None)
            if existing_page_index != page_index:
                carryover_direction = None
                if existing_page_index:
                    event_data = self.data()['events'][event_id]
                    carryover_direction = self.carryover_direction(event_data, existing_page_index, page_index)

                self.event_page_overrides[event_id].clear()

                if carryover_direction:
                    self.event_page_overrides[event_id]['pageIndex'] = page_index
                    self.event_page_overrides[event_id][GameEvent.PROPERTY_DIRECTION] = carryover_direction
            return self.event_page_overrides[event_id]

        def override_event_page(self, event_data, page, page_index, key, value):
            event_id = event_data['id']
            if event_id not in self.event_page_overrides:
                self.event_page_overrides[event_id] = {}

            existing_page_index = self.event_page_overrides[event_id].get('pageIndex', None)
            if existing_page_index != page_index:
                carryover_direction = self.carryover_direction(event_data, existing_page_index, page_index)

                self.event_page_overrides[event_id].clear()
                self.event_page_overrides[event_id]['pageIndex'] = page_index

                if carryover_direction:
                    self.event_page_overrides[event_id][GameEvent.PROPERTY_DIRECTION] = carryover_direction

            self.event_page_overrides[event_id][key] = value

        def carryover_direction(self, event_data, old_page_index, new_page_index):
            # Replicates some very convoluted logic in the `setupPageSettings` JS function:
            # direction is only reset when swapping pages if the direction of the new page
            # differs from the 'original' (non-overridden) direction of the original page
            if not old_page_index:
                return None

            old_page = event_data['pages'][old_page_index]
            new_page = event_data['pages'][new_page_index]
            if old_page['image']['direction'] == new_page['image']['direction']:
                return self.event_page_overrides[event_data['id']].get(GameEvent.PROPERTY_DIRECTION, None)
            return None

        def event_page_property(self, event_data, page, page_index, property):
            overrides = self.overrides_for_event_page(event_data['id'], page_index)
            if property in overrides:
                return overrides[property]
            elif property in GameEvent.IMAGE_STORED_PROPERTIES:
                return page['image'][property]
            else:
                return page[property]

        def event_sprite_data(self, event_data, page, page_index):
            overrides = self.overrides_for_event_page(event_data['id'], page_index)
            return {
                'direction': overrides.get(GameEvent.PROPERTY_DIRECTION, page['image']['direction']),
                'characterName': overrides.get(GameEvent.PROPERTY_CHARACTER_NAME, page['image']['characterName']),
                'characterIndex': overrides.get(GameEvent.PROPERTY_CHARACTER_INDEX, page['image']['characterIndex']),
                'tileId': overrides.get(GameEvent.PROPERTY_TILE_ID, page['image']['tileId']),
                'transparent': overrides.get(GameEvent.PROPERTY_TRANSPARENT, False),
                'stepAnime': page['stepAnime'],
                'moveSpeed': page['moveSpeed'],
                'pattern': page['image']['pattern']
            }

        def make_surrounding_tiles_walkable(self, e, page, page_index):
            if GameIdentifier().is_my_summer() and (self.map_id in [9, 10]) and (page['image']['characterName'] == 'Box' or page['image']['characterName'] == 'Box2'):
                return True
            elif GameIdentifier().is_living_with_mia_part_2() and (self.map_id == 10) and (e['id'] == 2) and page_index == 2:
                return True
            else:
                pushable_events = rpgm_game_data.get('pushable_events', None)
                if pushable_events:
                    return e['id'] in pushable_events.get(str(self.map_id), [])
            return False

        def map_clickable_for_event_page(self, loc, e, page, page_index):
            return MapClickable(
                loc[0],
                loc[1],
                page_index = page_index,
                label = self.page_label(page),
                special = self.event_is_special(e),
                clicky = self.clicky_event(e, page),
                has_commands = self.has_commands(page),
                through = self.event_page_property(e, page, page_index, GameEvent.PROPERTY_THROUGH),
                solid = GameEvent.page_solid(e, page, page_index),
                projectile_target = self.page_is_projectile_target(e, page),
                touch_trigger = page['trigger'] in [1,2],
                action_trigger = page['trigger'] in [0],
                parallel_trigger = page['trigger'] in [4]
            )

        def map_options(self, player_x, player_y, only_special = False, ignore_clicky = False, include_parallel = False):
            coords = []
            clicky_screen = not ignore_clicky and self.is_clicky(player_x, player_y)

            pushable_locations = []

            for e in self.active_events():
                for reverse_page_index, page in enumerate(reversed(e['pages'])):
                    if self.meets_conditions(e, page['conditions']):
                        # Allow trigger 3/4 (autorun/parallel) events to match so the pages under them don't get matched instead
                        # But these events shouldn't actually show up on the map, they will be triggered by the event loop
                        if page['trigger'] == 3:
                            break

                        if page['trigger'] == 4 and not (include_parallel or GalvMapProjectiles.is_projectile_page(page)):
                            break

                        loc = self.event_location(e)
                        page_index = (len(e['pages']) - 1) - reverse_page_index
                        map_clickable = self.map_clickable_for_event_page(loc, e, page, page_index)
                        if self.hide_buggy_event(e, page):
                            break
                        if clicky_screen:
                            parameters = page['list'][0]['parameters']
                            if len(parameters) == 1 and parameters[0] == 'click_activate!':
                                coords.append(map_clickable)
                        elif self.has_commands(page) or page['priorityType'] > 0 or map_clickable.is_projectile_target():
                            coords.append(map_clickable)

                            if self.has_commands(page) and self.make_surrounding_tiles_walkable(e, page, page_index):
                                pushable_locations.append(loc)
                        break

            if len(pushable_locations) > 0:
                existing_coords = {(map_clickable.x, map_clickable.y):True for map_clickable in coords}
                for loc in pushable_locations:
                    max_x = self.width() - 1
                    max_y = self.height() - 1

                    for adjacent_coord in self.adjacent_coords(loc[0], loc[1], max_x, max_y):
                        ax, ay, adirection = adjacent_coord
                        if (ax, ay) in existing_coords or (game_state.player_x == ax and game_state.player_y == ay):
                            continue
                        if self.can_pass(loc[0], loc[1], adirection):
                            map_clickable = MapClickable(
                                ax,
                                ay,
                                walk_destination = True
                            )
                            existing_coords[(ax, ay)] = True
                            coords.append(map_clickable)

            for location in self.curated_walk_locations():
                map_clickable = MapClickable(
                    location[0],
                    location[1],
                    walk_destination = True
                )
                coords.append(map_clickable)

            return coords

        def curated_walk_locations(self):
            if GameIdentifier().is_incest_adventure():
                # Top floor of lab, you need to hide behind a plant while a character walks by
                if game_state.map.map_id == 76:
                    return [(19, 34)]

            walk_locations_from_json = rpgm_game_data.get('curated_walk_locations', None)
            if walk_locations_from_json:
                return walk_locations_from_json.get(str(game_state.map.map_id), [])

            return []

        def random_encounter_troop_id(self, x, y):
            encounter_list = []
            weight_sum = 0
            for encounter in self.data()['encounterList']:
                region_id = self.tile_region(x, y)
                if len(encounter['regionSet']) == 0 or region_id in encounter['regionSet']:
                    encounter_list.append(encounter)
                    weight_sum += encounter['weight']
            if weight_sum > 0:
                value = random.randint(0, weight_sum)
                for encounter in encounter_list:
                    value -= encounter['weight']
                    if value < 0:
                        return encounter['troopId']
            return 0

        def name(self):
            if 'displayName' in self.data() and len(self.data()['displayName']) > 0:
                return self.data()['displayName']
            return None

    class GameMapRegistry:
        def __init__(self, state):
            self.state = state
            self.maps = {}

        def get_map(self, map_id):
            if not map_id in self.maps:
                self.maps[map_id] = GameMap(self.state, map_id)

            return self.maps[map_id]
