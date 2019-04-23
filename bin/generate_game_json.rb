#!/usr/bin/env ruby

require 'yaml'
require 'ostruct'
require 'fileutils'
require_relative 'rpgmaker_fakes'
require_relative 'vx_ace_to_mv'

if ARGV.length != 1
  puts "Usage: #{$0} path/to/an/rpgmaker/xp/vx/or/vxace/game"
  exit 0
end

game_dir = File.expand_path(ARGV.first)
$rpgm_files = Dir[File.join(game_dir, 'YAML', '*.yaml')]

def yaml_file(name)
  $rpgm_files.find { |f| f.end_with?(name) }
end

def load_data(path)
  YAML.load_file(path)
end

$data_actors = YAML.load_file(yaml_file('Actors.yaml'))
$data_classes = YAML.load_file(yaml_file('Classes.yaml'))
$data_troops = YAML.load_file(yaml_file('Troops.yaml'))
$data_enemies = YAML.load_file(yaml_file('Enemies.yaml'))
$data_skills = YAML.load_file(yaml_file('Skills.yaml'))
$data_items = YAML.load_file(yaml_file('Items.yaml'))
$data_weapons = YAML.load_file(yaml_file('Weapons.yaml'))
$data_armors = YAML.load_file(yaml_file('Armors.yaml'))
$data_tilesets = YAML.load_file(yaml_file('Tilesets.yaml'))
$data_common_events = YAML.load_file(yaml_file('CommonEvents.yaml'))
$data_system = YAML.load_file(yaml_file('System.yaml'))
$data_mapinfos = YAML.load_file(yaml_file('MapInfos.yaml'))

destination_folder = File.join(game_dir, 'JsonData/')
FileUtils.mkdir_p(destination_folder)
map_files = $rpgm_files.select { |path| path =~ /Map\d+\.yaml$/ }

DEGICA::CONVERT::run(
  destination_folder: destination_folder,
  map_files: map_files
)

if system('js-beautify --version')
  puts "Beautifying result files..."
  Dir.chdir(destination_folder) do
    `js-beautify *.json -r`
  end
  puts "...beautifying complete!"
end
