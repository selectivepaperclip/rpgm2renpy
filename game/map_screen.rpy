screen mapscreen(coords = None, mapfactor = None, player_position = None, map_name = None, sprites = None, impassible_tiles = None, common_events_keymap = None, background_image = None, width = None, height = None, x_offset = None, y_offset = None):
    #key "viewport_wheelup" action [
    #    SetVariable('mapfactor', mapfactor * 1.5),
    #    renpy.restart_interaction
    #]
    #key "viewport_wheeldown" action [
    #    SetVariable('mapfactor', mapfactor * 0.66),
    #    renpy.restart_interaction
    #]

    key 'i':
        action SetVariable("show_inventory", True), Jump("game")

    for key_str, event_id in common_events_keymap:
        key key_str:
            action SetVariable("keyed_common_event", event_id), Jump("game")

    viewport:
        child_size (width * GameMap.TILE_WIDTH, height * GameMap.TILE_HEIGHT)
        mousewheel True
        draggable True
        scrollbars True
        fixed at mapzoom(mapfactor):
            add background_image:
                xpos x_offset
                ypos y_offset

            button:
                xpos x_offset + int(player_position[0] * GameMap.TILE_WIDTH)
                xsize GameMap.TILE_WIDTH
                ypos y_offset + int(player_position[1] * GameMap.TILE_HEIGHT)
                ysize GameMap.TILE_HEIGHT
                background "#00f"

            for coord in impassible_tiles:
                button:
                    xpos x_offset + int(coord[0] * GameMap.TILE_WIDTH)
                    xsize GameMap.TILE_WIDTH
                    ypos y_offset + int(coord[1] * GameMap.TILE_HEIGHT)
                    ysize GameMap.TILE_HEIGHT
                    background "#0f0"

            for x, y, img in sprites:
                button:
                    xpos x_offset + int(x * GameMap.TILE_WIDTH)
                    xsize GameMap.TILE_WIDTH
                    ypos y_offset + int(y * GameMap.TILE_HEIGHT)
                    ysize GameMap.TILE_HEIGHT
                    add img

            for i, coord in enumerate(coords):
                button:
                    xpos x_offset + int(coord[0] * GameMap.TILE_WIDTH)
                    xsize GameMap.TILE_WIDTH
                    ypos y_offset + int(coord[1] * GameMap.TILE_HEIGHT)
                    ysize GameMap.TILE_HEIGHT
                    background Color("#f00", alpha = 0.75)
                    hover_background "#00f"
                    action SetVariable("mapdest", coord), Jump("game")

    if map_name:
        text map_name ypos 10 xpos 10 outlines [ (2, "#000", 0, 0) ]