#!/usr/bin/env ruby

require 'json'
require 'fileutils'

if ARGV.length < 1
  puts "Usage: #{$0} path/to/an/rpgmaker/xp/vx/or/vxace/game [rpgm_sdk_path]"
  puts "SDK path is likely to be something like C:\Program Files (x86)\Common Files\Enterbrain\RGSS3\RPGVXAce"
  exit 0
end

game_dir = File.expand_path(ARGV[0])
sdk_path = File.expand_path(ARGV[1])

$rpgm_tilesets_path = Dir[File.join(game_dir, 'JsonData', 'Tilesets.json')][0]
tilesets = []
JSON.parse(File.read($rpgm_tilesets_path)).compact.each do |json_tileset|
    tilesets = tilesets.concat(json_tileset['tilesetNames'])
end

needed_tilesets = tilesets.sort.uniq.select do |tileset|
    Dir[File.join(game_dir, 'Graphics', 'Tilesets', "#{tileset}.*")].empty?
end

if needed_tilesets.length > 0
    puts " === Needed tilesets: === "
    puts needed_tilesets
    needed_tilesets.each do |tileset|
        src = File.join(sdk_path, 'Graphics', 'Tilesets', "#{tileset}.png")
        dest = File.join(game_dir, 'Graphics', 'Tilesets')
        puts "Copying #{src} to #{dest}"
        FileUtils.cp(src, dest)
    end
end

$rpgm_map_paths = Dir[File.join(game_dir, 'JsonData', 'Map[0-9]*.json')]
$rpgm_actors_path = Dir[File.join(game_dir, 'JsonData', 'Actors.json')][0]
characters = []
JSON.parse(File.read($rpgm_actors_path)).compact.each do |json_actor|
    characters.push(json_actor['characterName'])
end
$rpgm_map_paths.each do |map_path|
    JSON.parse(File.read(map_path))['events'].compact.each do |json_event|
        json_event['pages'].each do |json_page|
            character_name = json_page['image']['characterName']
            characters.push(character_name) if character_name.length > 0
        end
    end
end

needed_characters = characters.sort.uniq.select do |character|
    Dir[File.join(game_dir, 'Graphics', 'Characters', "#{character}.*")].empty?
end

if needed_characters.length > 0
    puts " === Needed characters: === "
    puts needed_characters
    needed_characters.each do |tileset|
        src = File.join(sdk_path, 'Graphics', 'Characters', "#{tileset}.png")
        if File.exist?(src)
            dest = File.join(game_dir, 'Graphics', 'Characters')
            puts "Copying #{src} to #{dest}"
            FileUtils.cp(src, dest)
        else
            puts "#{src} does not exist!"
        end
    end
end

