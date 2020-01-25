screen battle_screen(
    background,
    troop_sprites
):
    add background
    for troop_sprite in troop_sprites:
        add troop_sprite['image']:
            xpos troop_sprite['x']
            ypos troop_sprite['y']
            xanchor 0.5
            yanchor 0.5