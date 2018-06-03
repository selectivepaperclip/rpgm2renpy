init -10 python:
    class SelectivelyPickle:
        def __getstate__(self):
            return dict((k, v) for k, v in self.__dict__.iteritems() if not k.startswith('_'))
