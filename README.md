# rpgm2renpy

A RPGMaker MV / VX Ace "emulator" made in RenPy

Designed for games that are mostly 'visual novels' so they don't need all that RPGM runaround.

rpgm2renpy parses and (mostly) understands the .json data files that an RPGMaker MV game is composed of,
and tries to (somewhat) faithfully reproduce the RPGMaker gameplay, but less annoying.

* No combat, ever
* Map screens are 'clickable' rather than 'walkable'
* Real-time event loop becomes synchronous, while fast-forwarding most animations that occur on the RPGM map.
* Configurable rpgm_game_data.json file allows certain events to be skipped, for getting rid of minigames and such.

## VX Ace Support

RPGMaker VX Ace games need to be converted into MV format first.

The process is something like this:

* Use the `rvpacker` gem (`gem install rvpacker`) to convert the raw VX Ace data files into .yaml
  * e.g. `rvpacker -a unpack -t ace -d /some/vx/ace/game`
* Use the `generate_game_json` script to convert the .yaml files into .json files
  * e.g. `bin/generate_game_json.rb /some/vx/ace/game`
* (sometimes) Use the `enumerate_needed_tilesets` script to copy base files from the VX Ace SDK
  * e.g. `bin/enumerate_needed_tilesets.rb /some/vx/ace/game C:\Program Files (x86)\Common Files\Enterbrain\RGSS3\RPGVXAce`
