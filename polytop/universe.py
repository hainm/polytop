
class Universe:

    default_polymer_name = 'polymer'
    _pad_char = '0'
    _n_pad = 3

    def __init__(self):
        self.molecules = {}
        self._mol_counter = 0

    def clear(self):
        self.molecules = {}
        self._mol_counter = 0
    
    @property
    def next_polymer_name(self):
        suffix = f'{self._mol_counter:{self._pad_char}^{self._n_pad}}'
        name = self.default_polymer_name + suffix
        return name
    
    def add_molecule(self, molecule):
        self.molecules[molecule.name] = molecule
        self._mol_counter += 1
