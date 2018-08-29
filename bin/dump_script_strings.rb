#!/usr/bin/env ruby

require 'json'
require 'fileutils'
require 'awesome_print'

if ARGV.length < 1
  puts "Usage: #{$0} path/to/an/rpgmaker/xp/vx/or/vxace/game"
  exit 0
end

game_dir = File.expand_path(ARGV[0])

def data_dir(game_dir)
    ace_path = File.join(game_dir, 'JsonData')
    mv_path = File.join(game_dir, 'www', 'data')
    if File.exist?(ace_path)
        ace_path
    elsif File.exist?(mv_path)
        mv_path
    end
end

script_strings = []

maps = Dir[File.join(data_dir(game_dir), 'Map[0-9]*')]
maps.each do |map_path|
    json = JSON.parse(File.read(map_path))
    json['events'].compact.each do |event_json|
        event_json['pages'].each do |page_json|
            commands = page_json['list']
            commands.each do |command|
                if command['code'] == 355
                    script_strings.push(command['parameters'][0])
                elsif command['code'] == 655
                    script_strings[-1] = "#{script_strings[-1]}\n#{command['parameters'][0]}"
                end
            end
        end
    end
end

puts script_strings.map(&:strip).uniq.sort