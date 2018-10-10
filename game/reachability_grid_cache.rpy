init -99 python:
    class ReachabilityGridCacheV2(object):
        MAX_CACHE_ITEMS = 5

        def __init__(self):
            self.cache = {}

        def get(self, player_position, events_with_pages):
            if events_with_pages in self.cache:
                if debug_reachability_grid:
                    print "RG: events_with_pages existed in reachability cache, checking positions..."
                time_added, position_groups_and_grids = self.cache[events_with_pages]
                for (player_positions, grid) in position_groups_and_grids:
                    if player_position in player_positions:
                        if debug_reachability_grid:
                            print "RG: Player position existed in cache item"
                        return grid
                    else:
                        reachability_bit = grid[player_position[1]][player_position[0]]
                        if debug_reachability_grid:
                            print "RG: Reachability bit for %s was %s" % (player_position, reachability_bit)
                        if reachability_bit == 3:
                            player_positions.append(player_position)
                            return grid
            return None

        def set(self, player_position, events_with_pages, grid):
            if len(self.cache) > ReachabilityGridCacheV2.MAX_CACHE_ITEMS:
                if debug_reachability_grid:
                    print "RG: More than %s items in grid (%s), purging oldest one" % (ReachabilityGridCacheV2.MAX_CACHE_ITEMS, len(self.cache))
                oldest_key = None
                oldest_time = time.time()
                for k, v in self.cache.iteritems():
                    time_added = v[0]
                    if time_added < oldest_time:
                        oldest_time = time_added
                        oldest_key = k
                del self.cache[oldest_key]

            new_position_group_and_grid = ([player_position], grid)
            if events_with_pages in self.cache:
                if debug_reachability_grid:
                    print "RG: Setting fresh position group and grid in the reachability cache"
                self.cache[events_with_pages][1].append(new_position_group_and_grid)
            else:
                if debug_reachability_grid:
                    print "RG: Adding position to existing item in reachability cache"
                self.cache[events_with_pages] = (time.time(), [new_position_group_and_grid])
