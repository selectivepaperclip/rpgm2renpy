screen mapscreen(
    coords = [],
    curated_clickables = [],
    mapfactor = None,
    fade_map = False,
    hud_pics = [],
    hud_lines = [],
    hud_groups = [],
    player_position = None,
    map_name = None,
    sprite_images_and_positions = None,
    balloon_images_and_positions = None,
    impassible_tiles = None,
    common_events_keymap = None,
    function_calls_keymap = [],
    background_image = None,
    overlay_ground_image = None,
    overlay_parallax_image = None,
    parallax_image = None,
    width = None,
    height = None,
    child_size = None,
    viewport_xadjustment = None,
    viewport_yadjustment = None,
    x_offset = None,
    y_offset = None,
    in_interaction = False,
    switch_toggler_buttons = [],
    common_event_queuers = [],
    picture_common_events = [],
    galv_screen_buttons = {},
    has_paused_events = False,
    has_realtime_events = False,
    has_random_encounter = False,
    skippable_events = [],
    paused_events_delay = 0,
    key_paused_events = [],
    active_timer = None,
    event_timers = [],
    faded_out = False,

    # cruft from old savegames
    sprites = None,
    x_initial = 0,
    y_initial = 0,
    show_synthesis_button = False,
):
    if not child_size:
        $ child_size = (width, height)

    if not sprite_images_and_positions:
        $ sprite_images_and_positions = game_state.sprite_images_and_positions()

    if not balloon_images_and_positions:
        $ balloon_images_and_positions = []

    if has_realtime_events:
        timer paused_events_delay / 60.0:
            action Function(game_state.tick_realtime_events)
            repeat True

    if not in_interaction:
        key "K_LEFT" action [
            Function(game_state.go_direction, GameDirection.LEFT),
            Jump("game")
        ]
        key "K_RIGHT" action [
            Function(game_state.go_direction, GameDirection.RIGHT),
            Jump("game")
        ]
        key "K_DOWN" action [
            Function(game_state.go_direction, GameDirection.DOWN),
            Jump("game")
        ]
        key "K_UP" action [
            Function(game_state.go_direction, GameDirection.UP),
            Jump("game")
        ]

        key "K_PAGEUP" action [
            Function(game_state.zoom_out),
            Jump("game")
        ]
        key "K_PAGEDOWN" action [
            Function(game_state.zoom_in),
            Jump("game")
        ]
        key "mousedown_4" action [
            Function(game_state.zoom_in),
            Jump("game")
        ]
        key "mousedown_5" action [
            Function(game_state.zoom_out),
            Jump("game")
        ]

        for key_str, event_id in common_events_keymap:
            key key_str:
                action SetVariable("keyed_common_event", event_id), Jump("game")

        for key_str, function_call in function_calls_keymap:
            key key_str:
                action SetVariable("keyed_function_call", function_call), Jump("game")

    key 'r':
        action Function(game_state.toggle_ask_for_random)

    if not faded_out:
        viewport id "map_bg_viewport":
            xadjustment viewport_xadjustment
            yadjustment viewport_yadjustment
            child_size child_size
            mousewheel False
            draggable (not in_interaction)
            scrollbars (not in_interaction)
            fixed at mapzoom(mapfactor):
                if parallax_image:
                    add parallax_image:
                        xpos x_offset
                        ypos y_offset

                add background_image:
                    id "map_bg_image"
                    xpos x_offset
                    ypos y_offset

                if overlay_ground_image:
                    add overlay_ground_image:
                        xpos x_offset
                        ypos y_offset

                if background_image:
                    button:
                        xpos x_offset + int(player_position[0] * rpgm_metadata.tile_width)
                        xsize rpgm_metadata.tile_width
                        ypos y_offset + int(player_position[1] * rpgm_metadata.tile_height)
                        ysize rpgm_metadata.tile_height
                        background Color("#00f", alpha = 0.5)

                if background_image:
                    for sprite_image_and_position in sprite_images_and_positions:
                        add sprite_image_and_position['img']:
                            xpos x_offset + sprite_image_and_position['x']
                            ypos y_offset + sprite_image_and_position['y']

                    for balloon_image_and_position in balloon_images_and_positions:
                        add balloon_image_and_position['img']:
                            xpos x_offset + balloon_image_and_position['x']
                            ypos y_offset + balloon_image_and_position['y']

                if overlay_parallax_image:
                    add overlay_parallax_image:
                        xpos x_offset
                        ypos y_offset

    for (id, args) in game_state.pictures():
        if ('opacity' not in args) or (args['opacity'] != 0):
            add args['image_name']:
                additive args.get('blend_mode') == 3
                alpha args.get('opacity', 255) / 255.0

    if not faded_out:
        for curated_clickable in curated_clickables:
            button:
                xpos curated_clickable['xpos']
                xsize curated_clickable['xsize']
                ypos curated_clickable['ypos']
                ysize curated_clickable['ysize']
                background Color("#f00", alpha = 0.5)
                hover_background Color("#00f", alpha = 0.5)
                tooltip curated_clickable['coord'].tooltip()
                action SetVariable("mapdest", curated_clickable['coord']), Jump("game")

        viewport id "map_fg_viewport":
            xadjustment viewport_xadjustment
            yadjustment viewport_yadjustment
            child_size child_size
            mousewheel False
            draggable None
            scrollbars None
            fixed at mapzoom(mapfactor):
                for coord in impassible_tiles:
                    button:
                        xpos x_offset + int(coord[0] * rpgm_metadata.tile_width)
                        xsize rpgm_metadata.tile_width
                        ypos y_offset + int(coord[1] * rpgm_metadata.tile_height)
                        ysize rpgm_metadata.tile_height
                        background Color("#000", alpha = 0.9)
                        tooltip("(%s, %s)" % coord)
                        action NullAction()

                for i, coord in enumerate(coords):
                    button:
                        xpos x_offset + int(coord.x * rpgm_metadata.tile_width)
                        xsize rpgm_metadata.tile_width
                        ypos y_offset + int(coord.y * rpgm_metadata.tile_height)
                        ysize rpgm_metadata.tile_height
                        if coord.is_projectile_target():
                            background "crosshair-small-red"
                            hover_background "crosshair-small-blue"
                        else:
                            background "square-small-red"
                            hover_background "square-small-blue"
                        tooltip coord.tooltip()
                        hovered SetVariable("hover_coord", coord)
                        action SetVariable("mapdest", coord), Jump("game")

    if fade_map:
        add Solid(Color("#000", alpha = 0.75))

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
        text hud_line['text']:
            ypos hud_line['Y']
            xpos hud_line['X']

    if background_image:
        for common_event_queuer in common_event_queuers:
            textbutton common_event_queuer['text']:
                xalign 0.98
                ypos common_event_queuer['ypos']
                background "#000"
                action Function(game_state.queue_common_event, common_event_queuer['event_id']), Jump("game")

        if not in_interaction:
            for galv_screen_button_id, galv_screen_button in galv_screen_buttons.iteritems():
                button:
                    background galv_screen_button['image']
                    xpos galv_screen_button['x']
                    ypos galv_screen_button['y']
                    action Function(game_state.queue_common_event, galv_screen_button['event_id']), Jump("game")

        for picture_common_event_button in picture_common_events:
            button:
                xpos picture_common_event_button['x']
                ypos picture_common_event_button['y']
                xsize picture_common_event_button['xsize']
                ysize picture_common_event_button['ysize']
                action Function(game_state.queue_common_event, picture_common_event_button['common_event_id']), Jump("game")

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

    if has_paused_events:
        textbutton "Advance Time (%s)" % paused_events_delay:
            xpos 5
            yalign 0.9
            background "#000"
            action Function(game_state.unpause_parallel_events), Jump("game")

    if not in_interaction:
        if len(skippable_events) > 0:
            textbutton "Skip event":
                xpos 5
                yalign 0.9
                background "#000"
                action Function(game_state.skip_event), Jump("game")
        if has_random_encounter:
            textbutton "Random encounter":
                xpos 5
                yalign 0.9
                background "#000"
                action SetVariable("random_encounter_next_round", function_call), Jump("game")

    if len(key_paused_events) > 0 or active_timer or len(event_timers) > 0:
        vbox:
            xalign 0.9
            yalign 0.8
            if active_timer:
                textbutton active_timer['text']:
                    background "#000"
                    action Function(game_state.finish_active_timer), Jump("game")
            for event_id in event_timers:
                textbutton ("Trigger Event Timer %s" % event_id):
                    background "#000"
                    action Function(GalvEventSpawnTimers.run_timer_actions, game_state.map), Jump("game")
            for key_paused_event_data in key_paused_events:
                hbox:
                    textbutton key_paused_event_data['text']:
                        background "#000"
                        action Function(game_state.unpause_parallel_events_for_key, key_paused_event_data['key']), Jump("game")
                    textbutton 'x50':
                        background "#000"
                        action Function(game_state.unpause_parallel_events_for_key, key_paused_event_data['key'], 50), Jump("game")