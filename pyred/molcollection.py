from .molecule import Molecule, indices_from_string


class Constraint:
    remark = ''
    not_enough_groups = ''

    @classmethod
    def from_line(cls, mol, line):
        groups = line.split(self.remark)[1].split('|')
        try:
            new = cls(mol, line, *groups)
        except TypeError:
            raise ValueError(f'{cls.not_enough_groups} Invalid line: {line}')


class ConstraintMEQA(Constraint):
    remark = 'INTER-MEQA'
    n_groups = 2

    def __init__(self, mol, line, molecules, atoms):
        try:
            mols = indices_from_string(molecules)
        except ValueError:
            try:
                self.mols = [mol.mols.index(mol.mol_names[x]) for x in mols]
            except ValueError:
                raise ValueError('INTER-MEQA must specify molecules with '
                                 'either the molecule names as given by '
                                 'REMARK TITLE or their integer numbers as '
                                 'indexed by 1. Invalid line: %s' % line)

        try:
            self.atoms = indices_from_string(atoms)
        except ValueError:
            raise ValueError('The atom numbers of INTER-MEQA must be integer '
                             'values. Invalid line: %s' % line)

        # TODO: check atom name compatibility


class ConstraintInter(Constraint):
    remark = 'INTER-MCC'
    not_enough_groups = ('INTER-MCC must have 4 fields:'
                         'charge | 2 molecule ids | '
                         'atom numbers of mol 1 | '
                         'atom numbers of mol 2.')

    def __init__(self, mol, line, charge, molecules, atoms1, atoms2):


class MolCollection:

    @classmethod
    def from_pdbs(cls, pdbs, itps, inter_file=None):
        collection = cls()
        for pdb, itp in zip(pdbs, itps):
            mol = Molecule.from_pdb(pdb, itp)
            collection.add_mol(mol)

        if inter_file:
            with open(inter_file, 'r') as f:
                for line in f:
                    record = line[:6].strip()

                    if record == 'REMARK':
                        fields = line[6:].split()
                        if fields:
                            remark = fields[0]

                            if remark == 'INTER-MCC':
                                collection.add_inter_mcc(line)

                            elif remark == 'INTER-MEQA':
                                collection.add_inter_meqa(line)
        collection.renumber_equivalent()
        return collection

    def __init__(self):
        self.mols = []
        self.mol_names = {}
        self.constraints = []
        self.equivalents = []

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
        self.equivalents.append((mols, atom_numbers))

    def renumber_equivalent(self):
        for mols, atoms in self.equivalents:
            for i in atoms:
                numbers = [self.mols[j].atom_numbers[i] for j in mols]
                if not len(set(numbers)) == 1:
                    max_heavy = [self.mols[j].n_heavy_atoms for j in mols]
                    new_n = max(max_heavy) + 1
                    for j in mols:
                        self.mols[j].atom_numbers[i] = new_n

    def write_resp_input_1(self, job):
        n_structures = [x.n_structures for x in self.mols]

        n_total_structures = sum(n_structures)
        header = self.mols[0].create_resp_header(job, nmol=n_total_structures)
        lines = [header]
        charge_lines = []
        intra_constraint_lines = []
        mol_temps = []

        for i, mol in enumerate(self.mols):
            ref_atom = 1 + sum(n_structures[:i])
            if mol.constraints:
                temps = mol.temps3
            else:
                temps = mol.temps1
            temps.append(temps)
            lines.extend(mol.get_temp_lines(temps))

            intra_constr = write_intra_constraints(mol.constraints, ref_atom)
            inter_constr = write_inter_constraints(self.constraints,
                                                   n_structures)
            intra_constraint_lines.extend(intra_constr[1:])
            inter_constraint_lines.extend(inter_constr)
            charge_lines.extend(write_intra_charge(temps, mol, ref_atom))

            for constr in self.meqs:
                nmol = len(constr.molecules)
                for imeq in constr.atoms:
                    temp = temps[imeq]

        inter = write_inter_constraints(self.constraints, n_structures)
        meqa = write_inter_equiv(self.constraints, mol_temps)

        # get around the intra/inter constraint comment
        lines.append(intra_constr[0])
        lines.extend(intra_constraint_lines)
        lines.extend(inter)
        lines.extend(charge_lines)

        if any(x == 0 for y in temps for x in y):
            lines.append('\n\n')
        lines.extend(write_inter_equiv(self.meq, temps, n_structures))

        with open('input1_mm', 'w') as f:
            f.write('\n'.join(lines))
