class RpgmYamlObject
  def method_missing(name, *args, &block)
    instance_variable_get("@#{name}")
  end

  def respond_to_missing?(name, include_private = false)
    instance_variable_defined?("@#{name}") || super
  end
end

module RPG
  class Actor < RpgmYamlObject; end
  class Class < RpgmYamlObject; end
  class Class::Learning < RpgmYamlObject; end
  class BaseItem < RpgmYamlObject; end
  class BaseItem::Feature < RpgmYamlObject; end
  class Skill < RpgmYamlObject; end
  class UsableItem < RpgmYamlObject; end
  class UsableItem::Effect < RpgmYamlObject; end
  class UsableItem::Damage < RpgmYamlObject; end
  class Item < RpgmYamlObject; end
  class Weapon < RpgmYamlObject; end
  class Armor < RpgmYamlObject; end
  class Tileset < RpgmYamlObject; end
  class CommonEvent < RpgmYamlObject; end
  class EventCommand < RpgmYamlObject
    def code
      @c
    end

    def code=(c)
      @c = c
    end

    def indent
      @i
    end

    def parameters
      @p
    end

    def parameters=(p)
      @p = p
    end
  end
  class MoveRoute < RpgmYamlObject; end
  class MoveCommand < RpgmYamlObject
    def code=(c)
      @code = c
    end

    def parameters=(p)
      @parameters = p
    end
  end
  class System < RpgmYamlObject; end
  class System::Vehicle < RpgmYamlObject; end
  class System::Terms < RpgmYamlObject; end
  class System::TestBattler < RpgmYamlObject; end
  class AudioFile < RpgmYamlObject; end
  class BGM < AudioFile; end
  class ME < AudioFile; end
  class SE < AudioFile; end
  class BGS < AudioFile; end
  class MapInfo < RpgmYamlObject; end
  class Map < RpgmYamlObject; end
  class Map::Encounter < RpgmYamlObject; end
  class Event < RpgmYamlObject; end
  class Event::Page < RpgmYamlObject; end
  class Event::Page::Condition < RpgmYamlObject; end
  class Event::Page::Graphic < RpgmYamlObject; end
end

class Color < RpgmYamlObject
  def red
    @r
  end

  def green
    @g
  end

  def blue
    @b
  end

  def alpha
    @a
  end

  def gray
    # TODO: not sure about this
    @a
  end
end
class Tone < Color; end

class Table
  attr_reader :dim

  def xsize
    @x
  end

  def ysize
    @y
  end

  def zsize
    @z
  end

  def [](x, y = nil, z = nil)
    unless @unpacked_data
      # TODO: unpack values in table data properly
      # this is probably wrong but at least im tryin

      @unpacked_data = @data.map do |data_line|
        data_line.split.map { |n| n.to_i(16) }
      end

      if dim == 1
        @unpacked_data.flatten!
      end
    end

    if dim == 1
      @unpacked_data[x]
    elsif dim == 2
      @unpacked_data[y][x]
    elsif dim == 3
      @unpacked_data[(z * @y) + y][x]
    end
  end
end

class DataManager
  def self.load_normal_database
  end
end
