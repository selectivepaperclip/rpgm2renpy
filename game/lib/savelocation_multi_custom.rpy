init python:
    class SavelocationMultiCustom(renpy.savelocation.MultiLocation):
        """
        Monkeypatched variant of MultiLocation that considers the 'local' save location
        to be inactive (via custom implementation of active_locations) except for saving
        developer hot-reload saves (via custom implementation of save)
        """

        def __init__(self, locations):
            self.locations = locations

        def active_locations(self, allow_local = False):
            """
            Differs from the upstream by ignoring 'local' save location unless allow_local is set
            """

            result = []
            for l in self.locations:
                if l.active and (allow_local or l.directory == renpy.config.savedir):
                    result.append(l)
            return result

        def save(self, slotname, record):
            """
            Differs from the upstream by sending `allow_local` param to `active_locations`
            (only if the thing being saved is a development hot-reload save)
            """

            saved = False
            for l in self.active_locations(allow_local = self.allow_local_for_slot(slotname)):
                l.save(slotname, record)
                saved = True

            if not saved:
                raise Exception("Not saved - no valid save locations.")

        def rename(self, old, new):
            for l in self.active_locations(allow_local = self.allow_local_for_slot(old)):
                l.rename(old, new)

        def allow_local_for_slot(self, slotname):
            return slotname.startswith('_reload')
