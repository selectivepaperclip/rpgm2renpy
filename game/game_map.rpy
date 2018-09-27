init python:
    import time
    import pygame
    import pygame_sdl2.image
    from Queue import PriorityQueue

    class ReachabilityGridCache:
        pass

    class ReachabilityGridCacheV2:
        MAX_CACHE_ITEMS = 5

        def __init__(self):
            self.cache = {}

        def get(self, player_position, events_with_pages):
            if events_with_pages in self.cache:
                if debug_reachability_grid:
                    print "RG: events_with_pages existed in reachability cache, checking positions..."
                time_added, position_groups_and_grids = self.cache[events_with_pages]
                for (player_positions, grid) in position_groups_and_grids:
                    if player_position in player_positions:
                        if debug_reachability_grid:
                            print "RG: Player position existed in cache item"
                        return grid
                    else:
                        reachability_bit = grid[player_position[1]][player_position[0]]
                        if debug_reachability_grid:
                            print "RG: Reachability bit for %s was %s" % (player_position, reachability_bit)
                        if reachability_bit == 3:
                            player_positions.append(player_position)
                            return grid
            return None

        def set(self, player_position, events_with_pages, grid):
            if len(self.cache) > ReachabilityGridCacheV2.MAX_CACHE_ITEMS:
                if debug_reachability_grid:
                    print "RG: More than %s items in grid (%s), purging oldest one" % (ReachabilityGridCacheV2.MAX_CACHE_ITEMS, len(self.cache))
                oldest_key = None
                oldest_time = time.time()
                for k, v in self.cache.iteritems():
                    time_added = v[0]
                    if time_added < oldest_time:
                        oldest_time = time_added
                        oldest_key = k
                del self.cache[oldest_key]

            new_position_group_and_grid = ([player_position], grid)
            if events_with_pages in self.cache:
                if debug_reachability_grid:
                    print "RG: Setting fresh position group and grid in the reachability cache"
                self.cache[events_with_pages][1].append(new_position_group_and_grid)
            else:
                if debug_reachability_grid:
                    print "RG: Adding position to existing item in reachability cache"
                self.cache[events_with_pages] = (time.time(), [new_position_group_and_grid])

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
            solid = False,
            touch_trigger = False,
            action_trigger = False
        ):
            self.x = x
            self.y = y
            self.label = label
            self.special = special
            self.reachable = True
            self.clicky = clicky
            self.has_commands = has_commands
            self.walk_destination = walk_destination
            self.page_index = page_index
            self.solid = solid
            self.touch_trigger = touch_trigger
            self.action_trigger = action_trigger

        def is_walk_destination(self):
            if hasattr(self, 'walk_destination') and self.walk_destination:
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
        def __init__(self, map_id, tiles, cache_file):
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

        def __getstate__(self):
            map_pickle_values = [(k, v) for k, v in self.__dict__.iteritems() if not k.startswith('_')]
            if debug_pickling:
                print ("picklin %s" % self.__class__.__name__)
                print map_pickle_values
            return dict(map_pickle_values)

        def save(self):
            # Caching code borrowed from https://github.com/renpy/renpy/blob/f40e61dfdfbf723f9eac88bbfec7765b45599682/renpy/display/imagemap.py
            # because it's hard as hell to figure out what incantations to do without source-diving

            surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)

            for tile in self.tiles:
                renpy.not_infinite_loop(10)
                if len(tile.tileset_name) > 0:
                    img_path = tile_images[tile.tileset_name.replace(".", "_")]
                    img_size = None
                    if img_path not in image_sizes:
                        image_sizes[img_path] = renpy.image_size(img_path)
                    img_size = image_sizes[img_path]
                    if tile.sx + tile.w <= img_size[0] and tile.sy + tile.h <= img_size[1]:
                        subsurface = renpy.display.im.cache.get(Image(img_path)).subsurface((tile.sx, tile.sy, tile.w, tile.h))
                        surf.blit(subsurface, (tile.dx + int(tile.x * rpgm_metadata.tile_width), tile.dy + int(tile.y * rpgm_metadata.tile_height)))
                    else:
                        print ("Image source out of bounds! '%s', imgWidth: %s, imgHeight: %s, sourceX: %s, sourceY: %s, sourceWidth: %s, sourceHeight: %s" % (tile.tileset_name, img_size[0], img_size[1], tile.sx, tile.sy, tile.w, tile.h))

            pygame_sdl2.image.save(surf, self.cache_file)

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

        def initialize_erased_events(self):
            self.erased_events = {}
            erased_events_from_metadata = rpgm_game_data.get('erased_events', None)
            if erased_events_from_metadata:
                for event_id in erased_events_from_metadata.get(str(self.map_id), []):
                    self.erased_events[event_id] = True

        def update_for_transfer(self):
            self.tileset_id_override = None
            self.event_location_overrides = {}
            self.event_overrides = {}
            self.initialize_erased_events()
            self.hide_unpleasant_moving_obstacles()

        def hide_unpleasant_moving_obstacles(self):
            if GameIdentifier().is_ics1():
                for e in self.active_events():
                    for page in reversed(e['pages']):
                        if self.meets_conditions(e, page['conditions']):
                            if page['trigger'] != 4:
                                continue

                            for command in page['list']:
                                if command['code'] != 205:
                                    continue

                                event_id = command['parameters'][0]
                                if event_id <= 0:
                                    continue

                                event = self.state.map.find_event_at_index(event_id)
                                if event:
                                    event.hide_if_unpleasant_moving_obstacle()

        def data(self):
            if not hasattr(self, '_data'):
                with rpgm_data_file("Map%03d.json" % self.map_id) as f:
                    self._data = json.load(f)

            return self._data

        def background_image(self):
            if not hasattr(self, '_background_image') or isinstance(self._background_image, GameMapBackground):
                if not os.path.exists(self.background_image_cache_file_absolute()):
                    self.generate_background_image()
                self._background_image = Image(self.background_image_cache_file())
            if not hasattr(self, 'image_width'):
                image_size = renpy.image_size(self._background_image)
                self.image_width = image_size[0]
                self.image_height = image_size[1]

            return self._background_image

        def background_image_cache_file(self):
            if hasattr(self, 'tileset_id_override') and self.tileset_id_override:
                basename = ('Map%03d_tileset%s.png' % (self.map_id, self.tileset_id_override))
            else:
                basename = ('Map%03d.png' % self.map_id)

            return os.path.join(map_cache_directory, basename).replace("\\", "/")

        def background_image_cache_file_absolute(self):
            return os.path.join(config.basedir, self.background_image_cache_file()).replace("\\", "/")

        def generate_background_image(self):
            bg = GameMapBackgroundGenerator(self.map_id, self.tiles(), self.background_image_cache_file_absolute())
            bg.save()

        def parallax_image(self):
            if not hasattr(self, '_parallax_image'):
                parallax_name = self.data()['parallaxName']
                if parallax_name and len(parallax_name) > 0:
                    self._parallax_image = parallax_images[rpgm_parallax_name(parallax_name)]
                else:
                    self._parallax_image = None

            return self._parallax_image

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

            some_event_is_clicky = False
            all_events_are_clicky = True
            for e in self.active_events():
                for page in reversed(e['pages']):
                    if self.meets_conditions(e, page['conditions']):
                        if self.clicky_event(e, page) and not self.ignored_clicky_page(page):
                            some_event_is_clicky = True
                        else:
                            all_events_are_clicky = False

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
            return result

        def character_sprite(self, image_data):
            img_base_filename = image_data['characterName'].replace(".", "_")

            character_prefix_match = re.match("^([!$])+", img_base_filename)
            is_big_character = False
            if character_prefix_match and '$' in character_prefix_match.groups()[0]:
                is_big_character = True

            is_object_character = False
            if character_prefix_match and '!' in character_prefix_match.groups()[0]:
                is_object_character = True

            if not img_base_filename in character_image_sizes:
                character_image_sizes[img_base_filename] = renpy.image_size(character_images[img_base_filename.lower()])
            img_size = character_image_sizes[img_base_filename]

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

            sx = (character_block_x + character_pattern_x) * pw
            sy = (character_block_y + character_pattern_y) * ph

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
                if player_character_actor['characterName'] != '':
                    player_character_sprite_data = {
                        "characterName": player_character_actor['characterName'],
                        "characterIndex": player_character_actor['characterIndex'],
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
                    return GameEvent(self.state, e, page, page_index)
            return None

        def find_event_for_location(self, x, y, only_special = False):
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
                            return GameEvent(self.state, e, page, page_index)
            return None

        def boring_auto_trigger_page(self, page):
            return [command['code'] for command in page['list']] == [0]

        def find_auto_trigger_event(self):
            for e in self.active_events():
                for reverse_page_index, page in enumerate(reversed(e['pages'])):
                    if self.meets_conditions(e, page['conditions']):
                        page_index = (len(e['pages']) - 1) - reverse_page_index
                        if page['trigger'] == 3 and not self.boring_auto_trigger_page(page):
                            return GameEvent(self.state, e, page, page_index)
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
                                result.append(GameEvent(self.state, e, page, page_index))
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
                            return GameEvent(self.state, e, page, page_index)
                        else:
                            break
            return None

        def parallel_events_activated_by_switch(self, switch_id):
            result = []
            for e in self.state.common_events_data():
                if e and e['trigger'] == 2 and e['switchId'] == switch_id:
                    result.append(e)
            return result

        def meets_conditions(self, event_data, conditions):
            if conditions['switch1Valid']:
                if not self.state.switches.value(conditions['switch1Id']):
                    return False

            if conditions['switch2Valid']:
                if not self.state.switches.value(conditions['switch2Id']):
                    return False

            if conditions['variableValid']:
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
            return self.reachability_grid(game_state.player_x, game_state.player_y, self.map_options(game_state.player_x, game_state.player_y, ignore_clicky = True))

        def reachability_grid(self, player_x, player_y, event_coords):
            if not hasattr(self, '_reachability_grid_cache') or not isinstance(self._reachability_grid_cache, ReachabilityGridCacheV2):
                self._reachability_grid_cache = ReachabilityGridCacheV2()

            player_position = (player_x, player_y)
            events_with_pages = tuple((coord.x, coord.y, coord.page_index) for coord in event_coords)
            cached_grid = self._reachability_grid_cache.get(player_position, events_with_pages)
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
                elif (hasattr(map_clickable, 'touch_trigger') and map_clickable.touch_trigger) and (hasattr(map_clickable, 'has_commands') and map_clickable.has_commands):
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

            self._reachability_grid_cache.set(player_position, events_with_pages, reachability_grid)
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
            if not hasattr(self, 'event_location_overrides'):
                self.event_location_overrides = {}
            if event_data['id'] in self.event_location_overrides:
                return self.event_location_overrides[event_data['id']]
            else:
                if 'x' in event_data:
                    return (event_data['x'], event_data['y'])

        def override_tileset(self, tileset_id):
            self.tileset_id_override = tileset_id
            delattr(self, '_background_image')

        def override_event_location(self, event_data, loc):
            if not hasattr(self, 'event_location_overrides'):
                self.event_location_overrides = {}
            self.event_location_overrides[event_data['id']] = loc

        def overrides_for_event_page(self, event_id, page_index):
            if not hasattr(self, 'event_overrides'):
                self.event_overrides = {}
            if hasattr(self, 'event_overrides') and event_id in self.event_overrides and self.event_overrides[event_id].get('pageIndex', -1) == page_index:
                return self.event_overrides[event_id]
            else:
                return {}

        def event_through(self, event_data, page, page_index):
            overrides = self.overrides_for_event_page(event_data['id'], page_index)
            return overrides.get('through', page['through'])

        def event_direction_fix(self, event_data, page, page_index):
            overrides = self.overrides_for_event_page(event_data['id'], page_index)
            return overrides.get('directionFix', page['directionFix'])

        def event_sprite_data(self, event_data, page, page_index):
            overrides = self.overrides_for_event_page(event_data['id'], page_index)
            return {
                'direction': overrides.get('direction', page['image']['direction']),
                'characterName': overrides.get('characterName', page['image']['characterName']),
                'characterIndex': overrides.get('characterIndex', page['image']['characterIndex']),
                'transparent': overrides.get('transparent', False),
                'pattern': page['image']['pattern']
            }

        def override_event(self, event_id, page_index, key, value):
            if not hasattr(self, 'event_overrides'):
                self.event_overrides = {}
            existing_event_overrides = self.event_overrides.get(event_id, None)
            if (not existing_event_overrides) or (page_index and existing_event_overrides.get('pageIndex', -1) != page_index):
                self.event_overrides[event_id] = {'pageIndex': page_index}
            if existing_event_overrides and existing_event_overrides.get('direction', None):
                # 'direction' applies to all pages, unlike properties like 'characterName' which get clobbered on page change
                self.event_overrides[event_id]['direction'] = existing_event_overrides['direction']

            self.event_overrides[event_id][key] = value

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
                solid = GameEvent.page_solid(page),
                touch_trigger = page['trigger'] in [1,2],
                action_trigger = page['trigger'] in [0]
            )

        def map_options(self, player_x, player_y, only_special = False, ignore_clicky = False):
            coords = []
            clicky_screen = not ignore_clicky and self.is_clicky(player_x, player_y)

            pushable_locations = []

            for e in self.active_events():
                for reverse_page_index, page in enumerate(reversed(e['pages'])):
                    if self.meets_conditions(e, page['conditions']):
                        # Allow trigger 3/4 (autorun/parallel) events to match so the pages under them don't get matched instead
                        # But these events shouldn't actually show up on the map, they will be triggered by the event loop
                        if page['trigger'] >= 3:
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
                        elif self.has_commands(page) or page['priorityType'] > 0:
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
