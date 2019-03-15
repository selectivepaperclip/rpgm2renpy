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
            input id "input" default ((upper + lower) // 2)
            null height 20

            hbox:
                xalign 1.0
                textbutton str(lower):
                    xsize 80
                    text_align 0.5
                    background "#009"
                    hover_background "#00f"
                    text_color "#fff"
                    action Return(lower)
                null width 20
                textbutton str((upper + lower) // 2):
                    xsize 80
                    text_align 0.5
                    background "#009"
                    hover_background "#00f"
                    text_color "#fff"
                    action Return((upper + lower) // 2)
                null width 20
                textbutton str(upper):
                    xsize 80
                    text_align 0.5
                    background "#009"
                    hover_background "#00f"
                    text_color "#fff"
                    action Return(upper)
