from typing import Iterable, Union

from .molecule import Molecule, indices_from_string, Remark
from .remark import REMARKS

L4ATOMS = ['K', 'CA', 'SC', 'TI', 'V', 'CR', 'MN', 'FE',
           'CO', 'NI', 'CU', 'ZN', 'GA', 'GE', 'AS', 'SE', 'BR']


class MolCollection:

    @classmethod
    def from_pdbs(cls, pdbs: Iterable[str], itps: Iterable[str],
                  inter_file: str = None):
        collection = cls()
        for pdb, itp in zip(pdbs, itps):
            collection.read_pdb(pdb, itp)

        if inter_file:
            collection.read_inter(inter_file)
        return collection

    def index(self, iterable: Iterable[str]):
        names = (self.mol_names[x] for x in iterable)
        return (self.mols.index(x) for x in names)

    def __init__(self):
        self.mols = []
        self.mol_names = {}
        self.constraints = []
        self.equivalents = []
        self.test_l4a = False

    def read_pdb(self, pdb: str, itp: str = None):
        mol = Molecule.from_pdb(pdb, itp)
        collection.add_mol(mol)

    def read_itp(self, mol: str, itp: str):
        self.mol_names[mol].h_bonds_from_itp(itp)

    def read_inter(self, inter_file):
        with open(inter_file, 'r') as f:
            for line in f:
                record = line[:6].strip()

                if record == 'REMARK':
                    fields = line[6:].split()
                    if fields:
                        remark = fields[0]

                        if remark in ('INTER-MCC', 'INTER-MEQA'):
                            rem = REMARKS[remark].from_line(line)
                            if remark == 'INTER-MCC':
                                self.constraints.append(remark)
                            else:
                                self.equivalents.append(remark)
        self.renumber_equivalent()

    def add_mol(self, mol):
        n = 2
        while mol.name in self.mols:
            mol.name += str(n)
            n += 1
        self.mols.append(mol)
        self.mol_names[mol.name] = mol
        if any(x.symbol in L4ATOMS for x in mol.atoms):
            self.test_l4a = True

    def renumber_equivalent(self):
        """Ensure equivalent atoms have same name"""
        for constr in self.equivalents:
            for i in constr.atoms:
                numbers = [self.mols[j].atom_numbers[i] for j in constr.mols]
                if not len(set(numbers)) == 1:
                    heavy = [self.mols[j].n_heavy_atoms for j in constr.mols]
                    new_n = max(heavy) + 1
                    for j in constr.mols:
                        self.mols[j].atom_numbers[i] = new_n
                        self.mols[j].n_heavy_atoms = new_n

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
            mol_temps.append(temps)
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

        if not any(x == 0 for y in temps for x in y):
            lines.append('\n\n')
        lines.extend(write_inter_equiv(self.meq, temps, n_structures))

        with open('input1_mm', 'w') as f:
            f.write('\n'.join(lines))

    def write_resp_input_2(self, job):
        n_structures = [x.n_structures for x in self.mols]

        n_total_structures = sum(n_structures)
        header = self.mols[0].create_resp_header(job, nmol=n_total_structures)
        lines = [header]
        charge_lines = []
        intra_constraint_lines = []
        mol_temps = []

        constraint_atoms = dict(i: set() for i in range(len(self.mols)))

        for constr in self.constraints:
            for i in constr.atoms1:
                constraint_atoms[constr.mol1].add(i)
            for j in constr.atoms2:
                constraint_atoms[constr.mol2].add(j)

        for i, mol in enumerate(self.mols):
            ref_atom = 1 + sum(n_structures[:i])
            if mol.constraints:
                temps = mol.temps4
            else:
                temps = mol.temps2
            for j, t in enumerate(temps):
                if t in constraint_atoms[i]:
                    temps[j] = -1

            temps.append(temps)
            lines.extend(mol.get_temp_lines(temps))

        intra_equivs = write_intra_equivalences_all(
            tesmps, self.mols, n_structures)
        inter_equivs = write_inter_equivalences_2(
            self.meq, temps, n_structures)

        lines.extend(intra_equivs)
        lines.extend(inter_equivs)

        with open('input2_mm', 'w') as f:
            f.write('\n'.join(lines))
