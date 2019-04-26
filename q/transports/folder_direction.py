# A mixin used by the folder transport classes
class Direction:
    def __init__(self, is_destward):
        self.is_destward = is_destward

    @property
    def read_ext(self):
        """Which file extension do I read from?"""
        return ".out" if self.is_destward else ".in"

    @property
    def write_ext(self):
        """Which file extension do I write to?"""
        return ".in" if self.is_destward else ".out"

    @property
    def direction(self):
        return 'destward' if self.is_destward else 'srcward'

