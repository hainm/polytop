class Topology:

    @classmethod
    def from_itp(cls, itp):
        pass

    def __init__(self, *args, **kwargs):
        super(Topology, self).__init__(*args, **kwargs)
        self.atoms = []
        self.bonds = []
        self.angles = []
        self.dihedrals = []
        self.impropers = []
    
    def link_to_monomer(self, monomer):
        for atom in self.atoms:
            match = monomer.atom_by_name(atom.name)
            if match:
                atom.pointer = match
            else:
                replaced = monomer.atom_by_
    
    def delete_atoms(self, *atoms):
        pass
    
    def replace_atoms(self):
        pass
        
class Atom:

    def link(self, other):
        other.topology = self
        self.pointer = other

class BondedTopology:
    n_atoms = 2

    def __init__(self, *atoms, **kwargs):
        if len(atoms) != self.n_atoms:
            raise ValueError('{clsname} requires {n_atoms1} atoms: '
                             '{n_atoms2} given.'.format(
                                 clsname=self.__class__.__name__,
                                 n_atoms=self.n_atoms, n_atoms2=len(atoms)
                             ))
        
        self.atoms = atoms
        self.kwargs = kwargs

class Bond(BondedTopology):
    n_atoms = 2

