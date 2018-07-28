screen mapscreen(
    coords = [],
    mapfactor = None,
    hud_pics = [],
    hud_lines = [],
    hud_groups = [],
    player_position = None,
    map_name = None,
    sprites = None,
    impassible_tiles = None,
    common_events_keymap = None,
    background_image = None,
    width = None,
    height = None,
    x_initial = 0,
    y_initial = 0,
    viewport_xadjustment = None,
    viewport_yadjustment = None,
    x_offset = None,
    y_offset = None,
    in_interaction = False,
    switch_toggler_buttons = [],
    common_event_queuers = [],
    show_synthesis_button = False, # cruft from old savegames
):
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

    viewport id "map_bg_viewport":
        xadjustment viewport_xadjustment
        yadjustment viewport_yadjustment
        child_size (width, height)
        mousewheel (not in_interaction)
        draggable (not in_interaction)
        scrollbars (not in_interaction)
        fixed at mapzoom(mapfactor):
            add background_image:
                xpos x_offset
                ypos y_offset

            if background_image:
                button:
                    xpos x_offset + int(player_position[0] * GameMap.TILE_WIDTH)
                    xsize GameMap.TILE_WIDTH
                    ypos y_offset + int(player_position[1] * GameMap.TILE_HEIGHT)
                    ysize GameMap.TILE_HEIGHT
                    background Color("#00f", alpha = 0.5)

            if background_image:
                for sprite_data in sprites:
                    python:
                        x, y, img = sprite_data[0:3]
                        screen_x = x * GameMap.TILE_WIDTH
                        screen_y = y * GameMap.TILE_HEIGHT
                        if len(sprite_data) > 3:
                            pw, ph, shift_y = sprite_data[3:6]
                            screen_x += (GameMap.TILE_WIDTH / 2) - (pw / 2)
                            screen_y += (GameMap.TILE_HEIGHT) - (ph + shift_y)

                    add img:
                        xpos x_offset + int(screen_x)
                        ypos y_offset + int(screen_y)

    for (id, args) in game_state.pictures():
        if ('opacity' not in args) or (args['opacity'] != 0):
            add args['image_name']

    viewport id "map_fg_viewport":
        xadjustment viewport_xadjustment
        yadjustment viewport_yadjustment
        child_size (width, height)
        mousewheel (not in_interaction)
        draggable (not in_interaction)
        scrollbars (not in_interaction)
        fixed at mapzoom(mapfactor):
            for coord in impassible_tiles:
                button:
                    xpos x_offset + int(coord[0] * GameMap.TILE_WIDTH)
                    xsize GameMap.TILE_WIDTH
                    ypos y_offset + int(coord[1] * GameMap.TILE_HEIGHT)
                    ysize GameMap.TILE_HEIGHT
                    background Color("#000", alpha = 0.9)
                    tooltip("(%s, %s)" % coord)
                    action NullAction()

            for i, coord in enumerate(coords):
                button:
                    xpos x_offset + int(coord.x * GameMap.TILE_WIDTH)
                    xsize GameMap.TILE_WIDTH
                    ypos y_offset + int(coord.y * GameMap.TILE_HEIGHT)
                    ysize GameMap.TILE_HEIGHT
                    background Color(coord.map_color(), alpha = 0.5)
                    hover_background Color("#00f", alpha = 0.5)
                    tooltip coord.tooltip()
                    hovered SetVariable("hover_coord", coord)
                    action SetVariable("mapdest", coord), Jump("game")

    for hud_group in hud_groups:
        button:
            xpos int(hud_group['parameters']['HudX'])
            ypos int(hud_group['parameters']['HudY'])
            xsize int(hud_group['parameters']['HudWidth'])
            ysize int(hud_group['parameters']['HudHeight'])
            background Color("#191970", alpha = 0.95)

    for hud_pic in hud_pics:
        add hud_pic['image']:
            xpos hud_pic['X']
            ypos hud_pic['Y']
            size hud_pic['size']

    for hud_line in hud_lines:
        text hud_line['text'] ypos hud_line['Y'] xpos hud_line['X']

    if background_image:
        for common_event_queuer in common_event_queuers:
            textbutton common_event_queuer['text']:
                xalign 0.98
                ypos common_event_queuer['ypos']
                background "#000"
                action Function(game_state.queue_common_event, common_event_queuer['event_id']), Jump("game")

    for switch_toggler in switch_toggler_buttons:
        textbutton switch_toggler['text']:
            xpos 5
            ypos 5
            background "#000"
            action Function(game_state.switches.set_value, switch_toggler['switch_id'], not game_state.switches.value(switch_toggler['switch_id'])), Jump("game")

    $ tooltip = GetTooltip()
    if tooltip:
        $ mousepos = renpy.get_mouse_pos()
        text tooltip:
            xpos mousepos[0]
            ypos mousepos[1]
            outlines [ (2, "#000", 0, 0) ]

    if map_name:
        text map_name ypos 10 xpos 10 outlines [ (2, "#000", 0, 0) ]