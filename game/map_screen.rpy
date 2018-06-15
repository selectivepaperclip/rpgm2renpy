screen mapscreen(coords = None, mapfactor = None, hud_pics = [], hud_lines = [], player_position = None, map_name = None, sprites = None, impassible_tiles = None, common_events_keymap = None, background_image = None, width = None, height = None, x_offset = None, y_offset = None, show_synthesis_button = False):
    #key "viewport_wheelup" action [
    #    SetVariable('mapfactor', mapfactor * 1.5),
    #    renpy.restart_interaction
    #]
    #key "viewport_wheeldown" action [
    #    SetVariable('mapfactor', mapfactor * 0.66),
    #    renpy.restart_interaction
    #]

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

    for hud_pic in hud_pics:
        add hud_pic['image']:
            xpos hud_pic['X']
            ypos hud_pic['Y']
            size renpy.image_size(normal_images[hud_pic['image']])

    for hud_line in hud_lines:
        text hud_line['text'] ypos hud_line['Y'] xpos hud_line['X']

    if show_synthesis_button:
        textbutton "Combine Items" xalign 0.98 ypos 140 background "#000" action SetVariable("show_synthesis", True), Jump("game")

    if map_name:
        text map_name ypos 10 xpos 10 outlines [ (2, "#000", 0, 0) ]