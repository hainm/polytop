
class BaseTopology:

    def load(self, filename):
        with open(filename, 'r') as f:
            content = f.read()
        return self._from_string(content)

    def _from_string(self, string):
        pass
    
    def _to_string(self):
        pass


class ITP:
    extension = 'itp'

class PSF:
    extension = 'psf'