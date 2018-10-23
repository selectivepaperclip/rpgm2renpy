#!/usr/bin/env ruby

require 'json'
require 'fileutils'
require 'awesome_print'

if ARGV.length != 2
  puts "Usage: #{$0} path/to/folder/with/one/or/many/rpgm2renpy/games comma_separated_command_codes"
  exit 0
end

def data_dir(game_dir)
    ace_path = File.join(game_dir, 'JsonData')
    mv_path = File.join(game_dir, 'www', 'data')
    if File.exist?(ace_path)
        ace_path
    elsif File.exist?(mv_path)
        mv_path
    end
end

game_dirs = Dir.glob(File.join(ARGV[0], '*', 'rpgmdata'))
command_codes = ARGV[1].split(',').map(&:to_i)
game_dirs.each do |dir|
    puts "GAME DIR: #{dir}"
    maps = Dir[File.join(data_dir(dir), 'Map[0-9]*')]
    maps.each do |map_path|
        json = JSON.parse(File.read(map_path))
        json['events'].compact.each do |event_json|
            event_json['pages'].each do |page_json|
                commands = page_json['list']
                commands.each do |command|
                    if command_codes.include?(command['code'])
                        puts JSON.pretty_generate(command)
                    end
                end
            end
        end
    end
end