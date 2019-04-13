screen random_int_selection_screen(lower, upper):
    style_prefix "input"
    modal True
    add Solid(Color("#000", alpha = 0.75))
    frame:
        xalign 0.5
        yalign 0.5
        xpadding 15
        ypadding 15
        vbox:
            if hasattr(game_state, 'last_said_text') and game_state.last_said_text:
                text "{i}%s{/i}" % game_state.last_said_text
            null height 20
            text "Rolling a random value between %s and %s:" % (lower, upper) style "input_prompt"
            if (upper - lower) > 8:
                input id "input" default ((upper + lower) // 2)
            null height 20

            hbox:
                xalign 1.0
                if (upper - lower) > 8:
                    for i in [lower, (upper + lower) // 2, upper]:
                        textbutton str(i):
                            xsize 80
                            text_align 0.5
                            background "#009"
                            hover_background "#00f"
                            text_color "#fff"
                            action Return(i)
                        null width 20
                else:
                    for i in xrange(lower, upper + 1):
                        textbutton str(i):
                            xsize 80
                            text_align 0.5
                            background "#009"
                            hover_background "#00f"
                            text_color "#fff"
                            action Return(i)
                        null width 20