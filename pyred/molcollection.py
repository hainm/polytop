import logging
from typing import Iterable, Union

from .molecule import Molecule, charges_from_punch
from .remark import REMARKS, INPUT_INTER_REMARK, INPUT_MEQA_REMARK

L4ATOMS = ['K', 'CA', 'SC', 'TI', 'V', 'CR', 'MN', 'FE',
           'CO', 'NI', 'CU', 'ZN', 'GA', 'GE', 'AS', 'SE', 'BR']

logger = logging.getLogger(__name__)


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
        self.inter_constraints = []
        self.inter_equivalences = []
        self.test_l4a = False

    def read_pdb(self, pdb: str, itp: str = None):
        mol = Molecule.from_pdb(pdb, itp)
        self.add_mol(mol)

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
                                self.inter_constraints.append(rem)
                            else:
                                self.inter_equivalences.append(rem)
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
        for constr in self.inter_equivalences:
            for i in constr.atoms:
                numbers = [self.mols[j].atom_numbers[i] for j in constr.mols]
                if not len(set(numbers)) == 1:
                    heavy = [self.mols[j].n_heavy_atoms for j in constr.mols]
                    new_n = max(heavy) + 1
                    for j in constr.mols:
                        self.mols[j].atom_numbers[i] = new_n
                        self.mols[j].n_heavy_atoms = new_n

    def write_resp_input_both(self, header):
        n_structures = [x.n_structures for x in self.mols]
        n_total_structures = sum(n_structures)

        header = header.format(nmol=n_total_structures)
        input1_lines = [header]
        input2_lines = [header]

        input1_temps = []
        input2_temps = []

        intra_constr = []
        intra_equiv_1 = []
        intra_equiv_2 = []

        constraint_atoms = self.get_constraint_atoms()

        for i, mol in enumerate(self.mols):
            # temps
            if mol.intra_constraints:
                tempsa, tempsb = mol.temps3, mol.temps4
            else:
                tempsa, tempsb = mol.temps1, mol.temps2

            for j, t in enumerate(tempsb):
                if t in constraint_atoms[i]:
                    tempsb[j] = -1

            input1_temps.append(tempsa)
            input2_temps.append(tempsb)

            input1_lines.extend(mol.get_temp_lines(tempsa))
            input2_lines.extend(mol.get_temp_lines(tempsb))

            ref = 1 + sum(n_structures[:i])

            # input1
            intra_constr.extend(mol.get_intra_constraint_lines(ref_atom=ref))
            intra_equiv_1.extend(
                mol.get_intra_equiv_lines(tempsa, ref_atom=ref))

            # input2
            intra_equiv_2.extend(
                mol.get_intra_equiv_lines(tempsb, ref_atom=ref))

        equiv_1, equiv_2 = self.get_inter_equiv_lines_both(input1_temps,
                                                           input2_temps)

        # input1
        input1_lines.extend(intra_constr)
        if any(x == 0 for y in input1_temps for x in y):
            input1_lines.append(INPUT_INTER_REMARK)
        input1_lines.extend(intra_equiv_1)
        input1_lines.extend(equiv_1)

        # input2
        if any(x == 0 for y in input2_temps for x in y):
            input2_lines.append(INPUT_INTER_REMARK)

        input2_lines.extend(intra_equiv_2)
        input2_lines.extend(equiv_2)

        with open('input1_mm', 'w') as f:
            f.write('\n'.join(input1_lines))
        logger.info('Wrote input1_mm')

        with open('input2_mm', 'w') as f:
            f.write('\n'.join(input2_lines))
        logger.info('Wrote input2_mm')

    def write_resp_input_1(self, header):
        n_structures = [x.n_structures for x in self.mols]
        n_total_structures = sum(n_structures)

        header = header.format(nmol=n_total_structures)
        input1_lines = [header]

        input1_temps = []

        intra_constr = []
        intra_equiv_1 = []

        for i, mol in enumerate(self.mols):
            # temps
            if mol.intra_constraints:
                tempsa = mol.temps3
            else:
                tempsa = mol.temps1

            input1_temps.append(tempsa)

            input1_lines.extend(mol.get_temp_lines(tempsa))

            ref = 1 + sum(n_structures[:i])

            # input1
            intra_constr.extend(mol.get_intra_constraint_lines(ref_atom=ref))
            intra_equiv_1.extend(mol.get_intra_equiv_lines(tempsa,
                                                           ref_atom=ref))

        equiv_1 = self.get_inter_equiv_lines_1(input1_temps)

        # input1
        input1_lines.extend(intra_constr)
        if any(x == 0 for y in input1_temps for x in y):
            input1_lines.append(INPUT_INTER_REMARK)
        input1_lines.extend(intra_equiv_1)
        input1_lines.extend(equiv_1)

        with open('input1_mm', 'w') as f:
            f.write('\n'.join(input1_lines))
        logger.info('Wrote input1_mm')

    def get_inter_equiv_lines_1(self, temps):
        if not self.inter_equivalences:
            return []

        n_structures = [x.n_structures for x in self.mols]
        lines = []
        for constr in self.inter_equivalences:
            nmol = len(constr.molecules)

            for imeq in constr.atoms:
                lines.append(f'  {nmol: 3d}')
                conf_line = ''

                for i, mol in enumerate(constr.molecules, 1):
                    ref_atom = 1 + sum(n_structures[:mol])
                    conf_line += f'  {ref_atom: 3d}  {imeq: 3d}'

                    if not i % 8 and not i == nmol:
                        conf_line += '\n'
                lines.append(conf_line)

        if lines:
            lines[0] += INPUT_MEQA_REMARK
        # if tempimrs == 0; testaff == 1; flagequiv == 1
        if not any(x == 0 for y in x for x in temps):
            lines.insert(0, '\n')
        lines.append("\n\n\n\n\n\n")
        return lines

    def get_inter_equiv_lines_both(self, tempsa, tempsb):
        if not self.inter_equivalences:
            return []

        n_structures = [x.n_structures for x in self.mols]

        lines_1 = []
        lines_2 = []
        if not any(x == 0 for y in x for x in tempsa):
            lines_1.append('\n')
        if not any(x == 0 for y in x for x in tempsb):
            lines_2.append('\n')

        for constr in self.inter_equivalences:
            nmol = len(constr.molecules)

            for imeq in constr.atoms:
                conf_line_1 = ''
                conf_line_2 = ''
                i = 0

                for m, mol in enumerate(constr.molecules, 1):
                    temp = tempsb[mol][imeq]
                    ref_atom = 1 + sum(n_structures[:mol])

                    # input1
                    conf_line_1 += f'  {ref_atom: 3d}  {imeq: 3d}'
                    if not m % 8 and not m == nmol:
                        conf_line_1 += '\n'

                    # input2
                    if temp == 0:
                        conf_line_2 += f'  {ref_atom: 3d}  {imeq: 3d}'
                        i += 1
                        # newline for every 8th
                        if i and not i % 8 and not m == nmol:
                            conf_line_2 += '\n'
                            i = 0

                lines_1.append(f'  {nmol: 3d}')
                if conf_line_2:
                    # only on first mol where temp == 0
                    lines_2.append(f'  {nmol: 3d}')

                lines_1.append(conf_line_1)
                lines_2.append(conf_line_2)
        if lines_1:
            lines_1[0] += INPUT_MEQA_REMARK
        if lines_2:
            lines_2[0] += INPUT_MEQA_REMARK
        lines_1.append('\n\n\n\n\n\n')
        lines_2.append('\n\n\n\n\n\n')
        return lines_1, lines_2

    def get_inter_constraint_lines(self, ref_atoms=[]):
        if not self.inter_constraints:
            return []
        lines = []
        conf_line = ''
        for constr in self.inter_constraints:
            ref_atom1 = 1 + sum(ref_atoms[:constr.mol1])
            ref_atom2 = 1 + sum(ref_atoms[:constr.mol2])
            lines.append(f'  {constr.n_atoms} {constr.charge:> 4.2f}')

            for i, atom in enumerate(constr.atoms1):
                conf_line += f'  {ref_atom1:>3d}  {atom:>3d}'
                if not i % 8:
                    conf_line += '\n'
            for j, atom in enumerate(constr.atoms2, i+1):
                conf_line += f'  {ref_atom2:>3d}  {atom:>3d}'
                if not j % 8:
                    conf_line += '\n'
        lines.append(conf_line)
        return lines

    def get_constraint_atoms(self):
        constraint_atoms = {i: set() for i in range(len(self.mols))}

        for constr in self.inter_constraints:
            for i in constr.atoms1:
                constraint_atoms[constr.mol1].add(i)
            for j in constr.atoms2:
                constraint_atoms[constr.mol2].add(j)
        return constraint_atoms

    def check_punch_files(self, n_punch=1):
        punch = f'punch{n_punch}_mm'
        output = f'output{n_punch}_mm'
        try:
            charges = charges_from_punch(punch)
        except FileNotFoundError:
            raise ValueError(f'FAILED: {punch} not found. See {output}')

        for mol in self.mols:
            for atom in mol.atoms:
                atom.charge2 = charges.pop(0)
