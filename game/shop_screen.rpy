screen shopscreen(shop_items = None, purchase_only = None):
    zorder 1
    frame:
        xalign 0.1
        yalign 0.23
        background Color("#f00", alpha = 0.75)

        vbox:
            textbutton "Leave":
                background "#f00"
                hover_background "#00f"
                action Hide("shopscreen"), Jump("game")
                xalign 1.0

            text "Money: %s" % game_state.party.gold

            null height 10

            grid 3 len(shop_items):
                for item in shop_items:
                    textbutton item['name']
                    textbutton "Own %s" % game_state.party.num_items(item)
                    textbutton ("Buy (%s)" % item['price']):
                        sensitive (game_state.party.gold >= item['price'])
                        action [
                            Function(game_state.party.gain_item, item, 1),
                            Function(game_state.party.lose_gold, item['price'])
                        ]
