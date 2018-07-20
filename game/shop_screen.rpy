screen shopscreen(shop_items = None, purchase_only = None):
    zorder 1
    frame:
        xalign 0.1
        yalign 0.23
        background Color("#005", alpha = 0.75)

        vbox:
            textbutton "Leave":
                background "#000"
                hover_background "#00f"
                action Hide("shopscreen"), Jump("game")
                xalign 1.0

            text "Money: %s" % game_state.party.gold

            null height 10

            grid 3 len(shop_items):
                for item in shop_items:
                    textbutton item['name'] text_color "#fff":
                        tooltip game_state.replace_names(item['description'])
                        action NullAction()
                    textbutton "Own %s" % game_state.party.num_items(item) text_color "#fff"
                    textbutton ("Buy (%s)" % item['price']):
                        text_color "#fff"
                        sensitive (game_state.party.gold >= item['price'])
                        action [
                            Function(game_state.party.gain_item, item, 1),
                            Function(game_state.party.lose_gold, item['price'])
                        ]

    $ tooltip = GetTooltip()
    if tooltip:
        $ mousepos = renpy.get_mouse_pos()
        button:
            xpos mousepos[0]
            ypos mousepos[1]
            background "#000"
            text tooltip:
                outlines [ (2, "#000", 0, 0) ]
