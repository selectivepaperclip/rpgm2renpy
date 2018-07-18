init -15 python:
    class SelectivelyPickle:
        def __getstate__(self):
            map_pickle_values = [(k, v) for k, v in self.__dict__.iteritems() if not k.startswith('_')]
            if debug_pickling:
                print ("picklin %s" % self.__class__.__name__)
                print map_pickle_values
            return dict(map_pickle_values)
