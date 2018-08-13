screen synthesisscreen(synthesizables = []):
    modal True
    zorder 1
    add Solid(Color("#000", alpha = 0.75))

    frame:
        xalign 0.1
        yalign 0.23
        background Color("#333", alpha = 0.75)

        vbox:
            text "Combine Items:"
            null height 20
            for item in synthesizables:
                textbutton item['name']:
                    if 'tooltip' in item:
                        tooltip item['tooltip']
                    if 'synthesizable' in item and item['synthesizable']:
                        background Color("#33c", alpha = 0.75)
                        hover_background Color("#33f", alpha = 0.75)
                        action [
                            Function(game_state.synthesize_item, item),
                            Hide("synthesisscreen"),
                            Jump("game")
                        ]
                    else:
                        background Color("#444", alpha = 0.75)
                        action NullAction()

            null height 20
            textbutton "Exit":
                background "#500"
                hover_background "#00f"
                action Hide("synthesisscreen"), Jump("game")
                xalign 0

    $ tooltip = GetTooltip()
    if tooltip:
        $ mousepos = renpy.get_mouse_pos()
        button:
            xpos mousepos[0]
            ypos mousepos[1]
            background "#000"
            text tooltip:
                outlines [ (2, "#000", 0, 0) ]