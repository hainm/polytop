import numpy as np

class Atom:
    def __eq__(self, other):
        if self.name == other.name:
            return True
        return False

    def __init__(self, monomer, name=None, element=None, serial=0, xyz=None):
        self.monomer = monomer
        self.polymer = monomer.polymer
        self.name = name
        self.element = element
        self.pointer = self

        if xyz is None:
            xyz = np.zeros(3)
        self.xyz = np.asarray(xyz)
    
    @property
    def resname(self):
        return self.monomer.name
    
    def replace(self, other):
        other.pointer = self
    


class Molecule:

    _default_name = 'mol'
    _pad_char = '0'
    _n_pad = 3
    _counter = 1

    @classmethod
    def next_default_name(cls):
        suffix = f'{cls._counter:{cls._pad_char}^{cls._n_pad}}'
        name = cls._default_name + suffix
        cls._counter += 1
        return name


    def __init__(self, name=None):
        super(Molecule, self).__init__()
        if name is None:
            name = self.next_default_name()
        self.name = name

class Monomer(Molecule):
    
    _default_name = 'molecule'

    def __init__(self, polymer, name=None, chain_id=0):
        super(Monomer, self).__init__(name=name)
        self.polymer = polymer
        self.chain_id = chain_id
        self.atoms = []


class Polymer(Molecule):

    _default_name = 'polymer'

    @classmethod
    def from_mdtraj(cls, trajectory):
        polymer = cls()
        polymer.add_mdtraj(trajectory)
        return polymer
    
    def __init__(self, name=None):
        super().__init__(name=name)
        self.monomers = []
        self.atoms = []
        self._original_atoms = []
    
    @property
    def n_atoms(self):
        return len(self.atoms)
    
    def add_mdtraj(self, trajectory):
        coords = trajectory.xyz[0]  # first frame
        df, bonds = trajectory.top.to_dataframe()
        bonds += self.n_atoms
        _last_resseq = 0
        _current_monomer = None
        for coord, row in zip(coords, df):
            # new monomer
            if row.resSeq != _last_resseq:
                if _current_monomer:
                    self.append(_current_monomer)
                _current_monomer = Monomer(row.resName, chain_id=row.chainID)
            # new atom
            atom = Atom(_current_monomer, name=row.name, element=row.element,
                        serial=row.serial, xyz=coord)
            _current_monomer.append(atom)

        if _current_monomer:
            self.append(_current_monomer)
    
    def link_topology(self):
        pass
    
    def append(self, monomer):
        self.monomers.append(monomer)

    def rename_monomers(self):
        pass
    
    def run_resp(self):
        pass
    
    def fragment_to_monomers(self, n_levels=3):
        pass
    
