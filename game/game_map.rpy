init python:
    class MapClickable:
        def __init__(self, x, y, label = None, special = False, clicky = False):
            self.x = x
            self.y = y
            self.label = label
            self.special = special
            self.reachable = True
            self.clicky = clicky

        def reachable_or_clickable(self):
            return (self.reachable if hasattr(self, 'reachable') else True) or (self.clicky if hasattr(self, 'clicky') else False)

        def map_color(self):
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

    class GameMapBackground(renpy.Displayable):
        def __init__(self, tiles, **kwargs):
            super(GameMapBackground, self).__init__(**kwargs)

            largest_x = 0
            largest_y = 0
            for tile in tiles:
                if tile.x > largest_x:
                    largest_x = tile.x
                if tile.y > largest_y:
                    largest_y = tile.y

            self.width = (largest_x + 1) * GameMap.TILE_WIDTH
            self.height = (largest_y + 1) * GameMap.TILE_HEIGHT
            self.tiles = tiles

        def __getstate__(self):
            map_pickle_values = [(k, v) for k, v in self.__dict__.iteritems() if not k.startswith('_')]
            if debug_pickling:
                print ("picklin %s" % self.__class__.__name__)
                print map_pickle_values
            return dict(map_pickle_values)

        def render(self, width, height, st, at):
            if not hasattr(self, '_r'):
              self._r = renpy.Render(self.width, self.height)

              for tile in self.tiles:
                  if len(tile.tileset_name) > 0:
                      img_path = tile_images[tile.tileset_name.replace(".", "_")]
                      img_size = None
                      if img_path not in image_sizes:
                          image_sizes[img_path] = renpy.image_size(img_path)
                      img_size = image_sizes[img_path]
                      if tile.sx + tile.w <= img_size[0] and tile.sy + tile.h <= img_size[1]:
                          img = im.Crop(img_path, (tile.sx, tile.sy, tile.w, tile.h))
                          self._r.blit(img.render(tile.w, tile.h, 0, 0), (tile.dx + int(tile.x * GameMap.TILE_WIDTH), tile.dy + int(tile.y * GameMap.TILE_HEIGHT)))
                      else:
                          print ("Image source out of bounds! '%s', imgWidth: %s, imgHeight: %s, sourceX: %s, sourceY: %s, sourceWidth: %s, sourceHeight: %s" % (tile.tileset_name, img_size[0], img_size[1], tile.sx, tile.sy, tile.w, tile.h))

            return self._r

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

        TILE_WIDTH = 48
        TILE_HEIGHT = 48

        def __init__(self, state, map_id):
            self.state = state
            self.map_id = map_id

        def data(self):
            if not hasattr(self, '_data'):
                with rpgm_file("www/data/Map%03d.json" % self.map_id) as f:
                    self._data = json.load(f)

            return self._data

        def background_image(self):
            if not hasattr(self, '_background_image'):
                self._background_image = self.generate_background_image()

            return self._background_image

        def generate_background_image(self):
            tiles = self.tiles()
            d = GameMapBackground(self.tiles())
            return d

        def clicky_command(self, command):
           return (command['code'] == 108) and (command['parameters'][0] == 'click_activate!')

        def clicky_event(self, event, page):
            first_event_command = event['pages'][0]['list'][0]
            if first_event_command and self.clicky_command(first_event_command):
                return True

            first_page_command = page['list'][0]
            return first_page_command and self.clicky_command(first_page_command)

        def ignored_clicky_page(self, page):
            # ZONE OF HACKS
            if GameIdentifier().is_milfs_villa():
                if len(page['list']) > 2 and page['list'][2]['parameters'][0] == "<Mini Label: Pool>":
                    return True
            return False

        def is_clicky(self, player_x, player_y):
            some_event_is_clicky = False
            all_events_are_clicky = True
            for e in self.data()['events']:
                if e:
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

        def flags(self, tile_id):
            flag_data = self.state.tilesets()[self.data()['tilesetId']]['flags']
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

            sx = ((tile_id // 128) % 2 * 8 + tile_id % 8) * GameMap.TILE_WIDTH
            sy = ((tile_id % 256 // 8) % 16) * GameMap.TILE_HEIGHT

            return GameTile(tile_id = tile_id, sx = sx, sy = sy, dx = 0, dy = 0, w = GameMap.TILE_WIDTH, h = GameMap.TILE_HEIGHT, set_number = set_number)

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
                w1 = GameMap.TILE_WIDTH // 2
                h1 = GameMap.TILE_HEIGHT // 2
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

                    if x == 23 and y in [16, 17, 18]:
                        return True
            return False

        def tile_id(self, x, y, z):
            try:
                return self.data()['data'][(z * self.height() + y) * self.width() + x]
            except IndexError:
                return 0

        def is_impassible(self, x, y, direction = None):
            if direction:
                direction_bits = [1 << direction / 2 - 1]
            else:
                direction_bits = [1, 2, 4, 8]

            if self.forced_passible(x, y):
                return False

            if self.tile_region(x, y) == 1:
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

        def last_square_before_dest(self, current_x, current_y, dest_x, dest_y):
            reachability_grid = self.reachability_grid_for_current_position()
            frontier = [(current_x, current_y)]
            visited = {(current_x, current_y): True}

            max_x = self.width() - 1
            max_y = self.height() - 1

            while len(frontier) > 0:
                current = frontier.pop()

                for adjacent_coord in self.adjacent_coords(current[0], current[1], max_x, max_y):
                    ax, ay, adirection = adjacent_coord
                    if (ax, ay) in visited:
                        continue
                    visited[(ax, ay)] = True

                    if ax == dest_x and ay == dest_y:
                        return (current, adirection)

                    if reachability_grid[ay][ax] == 3 and (not self.is_impassible(current[0], current[1], adirection) and not self.is_impassible(ax, ay, GameDirection.reverse_direction(adirection))):
                        frontier.append((ax, ay))

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
            if event_on_player:
                return False

            max_x = self.width() - 1
            max_y = self.height() - 1

            reachability_grid = self.reachability_grid_for_current_position()
            for adjacent_coord in self.adjacent_coords(game_state.player_x, game_state.player_y, max_x, max_y):
                ax, ay, adirection = adjacent_coord
                if reachability_grid[ay][ax] == 3 and (not self.is_impassible(game_state.player_x, game_state.player_y, adirection) and not self.is_impassible(ax, ay, GameDirection.reverse_direction(adirection))):
                    return True

            return False

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
                            tileset_names = self.state.tilesets()[self.data()['tilesetId']]['tilesetNames']
                            if len(tileset_names) > tile.set_number:
                                tile.tileset_name = tileset_names[tile.set_number]

                                result.append(tile)
            return result

        def sprites(self):
            result = []
            for e in self.data()['events']:
                if e:
                    for page in reversed(e['pages']):
                        if self.meets_conditions(e, page['conditions']):
                            image_data = page['image']
                            if image_data['characterName'] != '':
                                img_base_filename = image_data['characterName'].replace(".", "_")

                                is_big_character = False
                                if re.search("^[!$]+", img_base_filename) and img_base_filename[0] == '$':
                                    is_big_character = True

                                is_object_character = False
                                if re.search("^[!$]+", img_base_filename) and img_base_filename[0] == '!':
                                    is_object_character = True

                                if not img_base_filename in character_image_sizes:
                                    character_image_sizes[img_base_filename] = renpy.image_size(character_images[img_base_filename])
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

                                img = im.Crop(character_images[img_base_filename], (sx, sy, pw, ph))
                                shift_y = 0 if is_object_character else 6
                                result.append((e['x'], e['y'], img, pw, ph, shift_y))
                            elif image_data['tileId'] != 0:
                                tileset_names = self.state.tilesets()[self.data()['tilesetId']]['tilesetNames']
                                set_number = 5 + (image_data['tileId'] // 256)
                                tileset_name = tileset_names[set_number]

                                sx = ((image_data['tileId'] // 128) % 2 * 8 + image_data['tileId'] % 8) * GameMap.TILE_WIDTH
                                sy = ((image_data['tileId'] % 256) // 8) % 16 * GameMap.TILE_HEIGHT

                                img = im.Crop(tile_images[tileset_name.replace(".", "_")], (sx, sy, GameMap.TILE_WIDTH, GameMap.TILE_HEIGHT))
                                result.append((e['x'], e['y'], img))
                            break
            return result

        def event_is_special(self, e):
            return bool(re.search('weightSwitch', e['note']))

        def find_event_for_location(self, x, y, only_special = False):
            for e in self.data()['events']:
                if e and e['x'] == x and e['y'] == y:
                    for index, page in enumerate(reversed(e['pages'])):
                        if self.meets_conditions(e, page['conditions']) and page['trigger'] != 3:
                            if ((not only_special) and self.event_is_special(e)):
                                return None
                            if debug_events:
                                renpy.say(None, "event %s, page -%s / %s" % (e['id'], index, len(e['pages']) - index))
                            return GameEvent(self.state, e, page)
            return None

        def boring_auto_trigger_page(self, page):
            return [command['code'] for command in page['list']] == [0]

        def find_auto_trigger_event(self):
            for e in self.data()['events']:
                if e:
                    for page in reversed(e['pages']):
                        if self.meets_conditions(e, page['conditions']):
                            if page['trigger'] == 3 and not self.boring_auto_trigger_page(page):
                                return GameEvent(self.state, e, page)
                            else:
                                break
            return None

        def parallel_event_at_index(self, event_index):
            e = self.data()['events'][event_index]
            if e:
                for page in reversed(e['pages']):
                    if self.meets_conditions(e, page['conditions']):
                        if page['trigger'] == 4:
                            return GameEvent(self.state, e, page)
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
                if command['code'] != 0:
                    return True
            return False

        def page_label(self, page):
            for command in page['list']:
                if command['code'] == 408:
                    match = re.match('<Mini Label:(.*?)>', command['parameters'][0])
                    if match:
                        return match.groups()[0]
            return None

        def hide_buggy_event(self, event, page):
            # Milf's Villa has a scene where you need to cover a hole with an ottoman.
            # If you move the ottoman to the area before there is a hole, even in the original game, it will be lost forever.
            if GameIdentifier().is_milfs_villa():
                if self.map_id == 19:
                    # Fix broken state from savegames before this fix was in - if the hole was covered before the hole existed,
                    # the switches will be in the wrong state
                    if game_state.switches.value(59) == True and game_state.switches.value(61) == True:
                        game_state.switches.set_value(61, False)

                    # Hide the ottoman destination tiles if the quest is not to the phase where the ottoman should be moved there
                    if event['id'] in [14, 15, 16]:
                        return game_state.switches.value(59) != True
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
            if hasattr(self, '_reachability_grid_cache') and (player_x, player_y) in self._reachability_grid_cache:
                return self._reachability_grid_cache[(player_x, player_y)]

            # 0 = unknown / impassible
            # 2 = event
            # 3 = passible

            reachability_grid = [[0 for x in xrange(self.width())] for y in xrange(self.height())]

            for map_clickable in event_coords:
                reachability_grid[map_clickable.y][map_clickable.x] = 2

            max_x = self.width() - 1
            max_y = self.height() - 1

            coords_to_mark = [(player_x, player_y)]
            while len(coords_to_mark) > 0:
                mx, my = coords_to_mark.pop()
                reachability_grid[my][mx] = 3
                for adjacent_coord in self.adjacent_coords(mx, my, max_x, max_y):
                    ax, ay, adirection = adjacent_coord
                    if reachability_grid[ay][ax] == 0 and (not self.is_impassible(mx, my, adirection) and not self.is_impassible(ax, ay, GameDirection.reverse_direction(adirection))):
                        coords_to_mark.append(adjacent_coord[0:2])

            # for row in reachability_grid:
            #     print row

            if not hasattr(self, '_reachability_grid_cache'):
                self._reachability_grid_cache = {}
            self._reachability_grid_cache[(player_x, player_y)] = reachability_grid

            return reachability_grid

        def clear_reachability_grid_cache(self):
            self._reachability_grid_cache = {}

        def assign_reachability(self, player_x, player_y, event_coords):
            reachability_grid = self.reachability_grid(player_x, player_y, event_coords)

            max_x = self.width() - 1
            max_y = self.height() - 1

            for map_clickable in event_coords:
                map_clickable.reachable = False
                for adjacent_coord in self.adjacent_coords(map_clickable.x, map_clickable.y, max_x, max_y):
                    ax, ay, adirection = adjacent_coord
                    if reachability_grid[ay][ax] == 3:
                        map_clickable.reachable = True
                        break

        def map_options(self, player_x, player_y, only_special = False, ignore_clicky = False):
            coords = []
            clicky_screen = not ignore_clicky and self.is_clicky(player_x, player_y)
            for e in self.data()['events']:
                if e:
                    for page in reversed(e['pages']):
                        if page['trigger'] < 3 and self.meets_conditions(e, page['conditions']):
                            map_clickable = MapClickable(
                                e['x'],
                                e['y'],
                                label = self.page_label(page),
                                special = self.event_is_special(e),
                                clicky = self.clicky_event(e, page)
                            )
                            if self.hide_buggy_event(e, page):
                                break
                            if clicky_screen:
                                parameters = page['list'][0]['parameters']
                                if len(parameters) == 1 and parameters[0] == 'click_activate!':
                                    coords.append(map_clickable)
                            elif self.has_commands(page):
                                coords.append(map_clickable)
                            break

            return coords

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
