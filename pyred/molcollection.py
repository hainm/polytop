from .molecule import Molecule

class MolCollection:

    @classmethod
    def from_pdbs(cls, pdbs, inter_file=None):
        collection = cls()
        for pdb in pdbs:
            mol = Molecule.from_pdb(pdb)
            collection.add_mol(mol)

        if inter_file:
            with open(inter_file, 'r') as f:
                contents = f.readlines()
        
        for line in contents:
            record = line[:6].strip()
            
            if record == 'REMARK':
                fields = line[6:].split()
                if fields:
                    remark = fields[0]

                    if remark == 'INTER-MCC':
                        collection.add_inter_mcc(line)
                    
                    elif remark == 'INTER-MEQA':
                        collection.add_inter_meqa(line)

        return collection
        

    def __init__(self):
        self.mols = []
        self.mol_names = {}
        self.constraints = []
    
    def add_mol(self, mol):
        n = 2
        while mol.name in self.mols:
            mol.name += str(n)
            n += 1
        self.mols.append(mol)
        self.mol_names[mol.name] = mol

    
    def add_inter_mcc(self, line):
        groups = line.split('INTER-MCC')[-1].split('|')

        try:
            charge, mols, atoms1, atoms2 = groups
        except ValueError:
            raise ValueError('INTER-MCC must have 4 fields:'
                             'charge | 2 molecule ids | '
                             'atom numbers of mol 1 | '
                             'atom numbers of mol 2. Invalid line: %s' % line)
        
        try:
            a, b = mols.split()
            mols = (int(a-1), int(b-1))
        except ValueError:
            try:
                mols = (self.mols.index(self.mol_names[a]),
                        self.mols.index(self.mol_names[b]))
            except ValueError:
                raise ValueError('INTER-MCC must specify two molecules '
                                 'in the second field: either the molecule '
                                 'names as given by REMARK TITLE or their '
                                 'integer numbers as indexed by 1. Invalid '
                                 'line: %s' % line)

        try:
            entry = {
                'charge': float(charge),
                'mols': mols,
                'atoms1': list(map(int, atoms1.split())),
                'atoms2': list(map(int, atoms2.split()))
            }
        except ValueError:
            raise ValueError('INTER-MCC must have 4 fields:'
                             'floating point charge | 2 molecule ids | '
                             'integer atom numbers of mol 1 | '
                             'integer atom numbers of mol 2. Invalid line: '
                             '%s' % line)
        self.constraints.append(entry)
    
    def add_inter_meqa(self, line):
        groups = line.split('INTER-MEQA')[-1].split('|')

        try:
            mols, atoms = groups
        except ValueError:
            raise ValueError('INTER-MEQA must have 2 fields:'
                             'Molecule ids | atom numbers of each molecule. '
                             'Invalid line: %s' % line)
        
        try:
            mols = [int(x)-1 for x in mols]
        except ValueError:
            try:
                mols = [self.mols.index(self.mol_names[x]) for x in mols]
            except ValueError:
                raise ValueError('INTER-MEGA must specify molecules with '
                                 'either the molecule names as given by '
                                 'REMARK TITLE or their integer numbers as '
                                 'indexed by 1. Invalid line: %s' % line)

        try:
            atom_numbers = list(map(int, atoms.split()))
        except ValueError:
            raise ValueError('The atom numbers of INTER-MEQA must be integer '
                             'values. Invalid line: %s' % line)
        # TODO: Fix this when I get to the calc part
        self.equivalent.append((mols, atom_numbers))
    
    def renumber_equivalent(self):
        for entry in self.equivalent:
