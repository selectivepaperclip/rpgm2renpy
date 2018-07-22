screen synthesisscreen(synthesizables = []):
    modal True
    zorder 1
    add Solid(Color("#000", alpha = 0.75))

    frame:
        xalign 0.1
        yalign 0.23
        background Color("#f00", alpha = 0.75)

        vbox:
            textbutton "Exit":
                background "#f00"
                hover_background "#00f"
                action Hide("synthesisscreen"), Jump("game")
                xalign 1.0

            for item in synthesizables:
                textbutton item['name']:
                    action [
                        Function(game_state.synthesize_item, item),
                        Hide("synthesisscreen"),
                        Jump("game")
                    ]
