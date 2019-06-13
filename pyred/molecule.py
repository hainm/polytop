import re
import os
import logging
from collections import namedtuple
import numpy as np


from .atom import Atom
from .remark import REMARKS, INPUT_INTER_REMARK, INPUT_INTRA_REMARK
from .reorientation import rigid_body_orient, rigid_body_rotate

logger = logging.getLogger(__name__)

alpha = re.compile('[a-zA-Z]')
itp_bonds = re.compile(r'\s*(?P<ai>\d+)\s*(?P<aj>\d+)\s*\d\s+')

PUNCH_PATTERN = re.compile(
    r'\s+\d+\s+\d+\s+(\-\d|\d)\.\d+\s+(\-\d|\d)\.\d+\s+')


def charges_from_punch(filename):
    charges = []
    with open(filename, 'r') as f:
        for line in f:
            if re.match(PUNCH_PATTERN, line):
                subbed = re.sub(r'\s+', ':', line)
                try:
                    ch = subbed.split(':')[4]
                except IndexError:
                    raise ValueError('No charge found; job failed.'
                                     f' See {filename}')
                if 'nan' in ch or '*' in ch:
                    raise ValueError('At least one charge invalid.'
                                     f' See {filename}')
                charges.append(float(ch))
    return charges


class Molecule:
    @classmethod
    def from_pdb(cls, pdb, itp=None):
        mol = cls()
        n_atoms = 0
        conf = []
        with open(pdb, 'r') as f:
            for line in f:
                record = line[:6].strip()
                fields = line[6:]

                if record == 'END':
                    return mol

                elif record == 'TER':
                    n_atoms = 0
                    if conf:
                        mol.conf_pdbs.append(conf)
                    conf = []

                # read molecule name
                elif record == 'TITLE':
                    name = fields.split()
                    if name:
                        mol.name = name[0]

                elif record == 'REMARK':
                    rem = fields.split()
                    if len(rem) > 2:
                        # skip real REMARKs and allow unnumbered
                        try:
                            nr = int(rem[0])
                            if nr >= 6 and nr <= 99:
                                rem = rem[1:]
                            else:
                                continue
                        except:
                            pass

                        # RED p2n REMARKs
                        remark, *info = rem
                        if remark == 'CHARGE' or remark == 'CHARGE-VALUE':
                            try:
                                mol.charge = int(info[0])
                            except ValueError:
                                raise ValueError('Your CHARGE must be an '
                                                 'integer value. Invalid '
                                                 'line: %s' % line)

                        elif (remark == 'MULTIPLICITY' or
                              remark == 'MULTIPLICITY-VALUE'):
                            try:
                                mol.multiplicity = int(info[0])
                            except ValueError:
                                raise ValueError('Your MULTIPLICITY must be '
                                                 'an integer value. Invalid '
                                                 'line: %s' % line)

                        elif remark in ('REORIENT', 'ROTATE', 'TRANSLATE'):
                            mol.add_transform(remark, line)

                        elif remark == 'INTRA-MCC':
                            new = REMARKS[remark].from_line(line)
                            mol.intra_constraints.append(new)

                elif record in ('ATOM', 'HETATM'):
                    _xyz = [line[30:38], line[38:46], line[46:54]]
                    xyz = list(map(float, _xyz))
                    try:
                        mol.atom_coords[n_atoms].append(xyz)
                    except IndexError:
                        mol.add_atom(line[12:16].strip())
                        mol.atom_coords.append([xyz])
                    conf.append(line)
                    n_atoms += 1
            if conf:
                mol.conf_pdbs.append(conf)
            mol.coords = np.array(mol.atom_coords).T
            mol.count_structures()
            if itp:
                mol.h_bonds_from_itp(itp)
            return mol

    def __init__(self):
        self.name = 'UNK'
        self.conf_pdbs = []
        self.atoms = []
        self.atom_coords = []
        self.transform_remarks = []
        self.intra_constraints = []
        self.n_atoms = 0
        self.n_heavy_atoms = 0
        self.coords = None
        self.n_transforms = 0
        self.n_confs = 0
        self.transforms = {'REORIENT': set(),
                           'ROTATE': set(),
                           'TRANSLATE': set()}

    def count_structures(self):
        self.n_confs, self.n_atoms, _ = self.coords.shape
        self.n_transforms = sum([len(x) for x in self.transforms.values()])
        self.n_structures = self.n_confs * self.n_transforms

    def add_transform(self, remark, line):
        self.transform_remarks.append(line)
        self.transforms[remark] |= REMARKS[remark].from_line(line)

    def add_atom(self, name):
        atom = Atom(name=name, mol=self)
        self.atoms.append(atom)

    def h_bonds_from_itp(self, itp):
        bond_section = False

        with open(itp, 'r') as f:
            for line in f:
                if '[ bonds ]' in line:
                    bond_section = True
                    continue
                if bond_section:
                    match = itp_bonds.match(line)
                    if match:
                        ai = match.group('ai') - 1
                        aj = match.group('aj') - 1

                        zi = self.atoms[ai].symbol
                        zj = self.atoms[aj].symbol

                        if zi == 'H':
                            self.atoms[ai].bond_to_heavy(self.atoms[aj])
                        elif zj == 'H':
                            self.atoms[aj].bond_to_heavy(self.atoms[ai])

    def get_mep_coordinates(self):
        coords = []
        for conf_coords in self.coords, 1:
            transform_coords = []

            for ijk in self.transforms['REORIENT']:
                xyz = conf_coords.copy()
                rigid_body_orient(*ijk, xyz)
                transform_coords.append(xyz)

            for ijk in self.transforms['ROTATE']:
                xyz = conf_coords.copy()
                rigid_body_rotate(*ijk, xyz)
                transform_coords.append(xyz)

            for coords in self.transforms['TRANSLATE']:
                xyz = conf_coords.copy() + coords
                transform_coords.append(xyz)

            coords.append(transform_coords)
        return coords

    # def write_espot(self, job):
    #     """ Write espot file."""
    #     header = f'{len(self.atoms):3d}{{pt:4d}}  {self.charge:2d}    {self.name}'
    #     all_lines = []

    #     for c in range(1, self.n_confs+1):
    #         for w in range(1, self.n_transforms+1):
    #             basename = f'{self.name}-{c}-{w}'

    #             point, atoms = job.get_espot_info(basename)

    #             lines = [header.format(pt=point)] + atoms
    #             all_lines.extend(lines)
    #             filename = f'espot_{self.name}-{c}-{w}'
    #             with open(filename, w) as f:
    #                 f.write('\n'.join(lines))
    #             logger.info(f'Wrote {filename}')

    #     filename = f'espot_{self.name}'
    #     with open(filename, 'w') as f:
    #         f.write('\n'.join(all_lines + ['', '']))
    #     logger.info(f'Wrote {filename}')

    #     if self.n_transforms <= 1:
    #         if os.path('./espot1').isfile:
    #             os.remove('./espot1')
    #     return all_lines

    # def write_espot_conf(self, point, atoms):
    #     """ Write espot file."""
    #     header = f'{len(self.atoms):3d}{{pt:4d}}  {self.charge:2d}    {self.name}'
    #     all_lines = []

    #     for c in range(1, self.n_confs+1):
    #         for w in range(1, self.n_transforms+1):
    #             basename = f'{self.name}-{c}-{w}'

    #             point, atoms = job.get_espot_info(basename)

    #             lines = [header.format(pt=point)] + atoms
    #             all_lines.extend(lines)
    #             filename = f'espot_{self.name}-{c}-{w}'
    #             with open(filename, w) as f:
    #                 f.write('\n'.join(lines))
    #             logger.info(f'Wrote {filename}')

    #     filename = f'espot_{self.name}'
    #     with open(filename, 'w') as f:
    #         f.write('\n'.join(all_lines + ['', '']))
    #     logger.info(f'Wrote {filename}')
    #     return all_lines

    # def remove_espot_files(self):
    #     if self.n_transforms <= 1:
    #         if os.path('./espot1').isfile:
    #             os.remove('./espot1')

    def create_temp_lines(self, job):
        sep = f'\n  1.0\n {self.name} \n{self.charge:>5d}{self.n_atoms:>5d}'
        self.temp_lines = [sep]
        # temps = []
        for i, atom in enumerate(self.atoms):
            # temps.append(job.get_atom_temps(i, self))
            line = f"  {atom.atomic_number:2d} {{temp:3d}} {'':20} {i+1:3d}"
            self.temp_lines.append(line)
        # self.temps1, self.temps2, self.temps3, self.temps4 = zip(*temps)

    def get_temp_lines(self, temps):
        templates = []
        atom_lines = []
        for x, temp in zip(self.temp_lines, temps):
            templates.append(x.format(temp=temp))

        atom_lines = templates * self.n_structures
        atom_lines[0] += f'          Column not used by RESP'  # first line
        return atom_lines

    def write_resp_input(self, header, temps1, temps2, input_no=1):
        """Write RESP input files for charge calculation"""
        header = [header.format(nmol=self.n_transforms)]

        atoms1, charges1 = self.get_atoms_equivalences(temps1)
        atoms2, charges2 = self.get_atoms_equivalences(temps2)

        filename = f'input{input_no}_{self.name}'
        files = [(input_no, self.name, '')]
        with open(filename, 'w') as f:
            f.write('\n'.join(header + atoms1 + charges1))
        logger.info(f'Wrote RESP input files for {self.name}')

        if self.intra_constraints:
            if input_no == 1:
                constraints = self.get_intra_constraint_lines(1)
            with open(f'{filename}.sm', 'w') as f:
                f.write('\n'.join(header + atoms2 + constraints + charges2))
            files.append((input_no, self.name, '.sm'))

        return files

    def write_redpdb(self):
        lines = ['REMARK', *self.transform_remarks, 'REMARK']

        for conf in self.conf_pdbs:
            lines.extend(conf)
            lines.append('TER')
        if not self.transform_remarks:
            lines.append("REMARK QMRA")
        lines.append('END')

        filename = f'File4REDDB_{self.name}.pdb'
        with open(filename, 'w') as f:
            f.write('\n'.join(lines))
        logger.info(f'Wrote {filename}')

    def get_intra_equiv_lines(self, temps, ref_atom=1):
        conf_lines = []
        for i, temp in enumerate(temps, 1):
            if temp == 0:
                conf_lines.append(f'  {self.n_structures:3d}')
                conf_line = ''
                for j in enumerate(self.n_structures, 1):
                    conf_line += f'  {j+ref_atom-1:3d}  {i:3d}'
                    # new line every 8th step
                    if not j % 8 and not j == len(self.n_structures):
                        conf_line += '\n'
                conf_lines.append(conf_line)
        conf_lines.append('\n\n\n\n\n')
        return conf_lines

    def get_atoms_equivalences(self, temps):
        atoms = self.get_temp_lines(temps)
        confs = self.get_intra_equiv_lines(temps)
        if any(x == 0 for x in temps):
            confs.insert(0, INPUT_INTER_REMARK)
        return atoms, confs

    def get_intra_constraint_lines(self, ref_atom=1):
        if not self.intra_constraints:
            return []
        lines = []
        conf_line = ''
        for constr in self.intra_constraints:
            n_atoms = len(constr.atoms)
            lines.append(f'  {n_atoms} {constr.charge:> 4.2f}')

            for i, atom in enumerate(constr.atoms):
                conf_line += f'  {ref_atom:>3d}  {atom:>3d}'
                if i and not i % 8 and not i == n_atoms:
                    conf_line += '\n'
        lines.append(conf_line)
        if ref_atom == 1:
            lines = [INPUT_INTRA_REMARK] + lines
        return lines

    def write_punch(self, charges, atom_name_indices, filename):
        charges = np.array(charges)
        averages = []
        lines = ["     Averaged ESP charges from punch1",
                 "  Z     Equiv.    q(opt)	Rounding-Off"]

        for i, atom in enumerate(self.atoms):
            indices = atom_name_indices.get(atom.full_resp_name, [i])
            equiv_charges = charges[indices]  # get charges of equivalent atoms
            avg = np.mean(equiv_charges)
            averages.append(avg)
            z = atom.atomic_number
            j = indices[0]+1  # serial of first match
            lines.append(f"{z:<2d}     {j:<2d}     {avg:<8.7f}  {avg:<5.4f}")

        with open(filename, 'w') as f:
            f.write('\n'.join(lines))
        logger.info(f'Wrote {filename}')
        return averages

    def get_atom_name_indices(self):
        indices = {}
        for i, atom in enumerate(self.atoms):
            if atom.full_resp_name in indices:
                indices[atom.full_resp_name].append(i)
            else:
                indices[atom.full_resp_name] = [i]
        return indices

    def write_punch_2_files(self):
        punch = f'punch2_{self.name}'
        indices = self.get_atom_name_indices()
        self.charges = self.write_punch(self.charges, indices, punch)

        if not self.intra_constraints:
            return

        atoms = set([x for y in self.intra_constraints for x in y.atoms])
        ex_indices = {}
        for k, v in indices.items():
            ex_indices[k] = [x for x in v if x not in atoms]
        self.charges_intra = self.write_punch(self.charges_intra, ex_indices,
                                              f'{punch}.sm')

    def check_punch_files(self, n_punch=1):
        punch = f'punch{n_punch}_{self.name}'
        output = f'output{n_punch}_{self.name}'
        try:
            self.charges = charges_from_punch(punch)
        except FileNotFoundError:
            raise ValueError(f'FAILED: {punch} not found. See {output}')

        if self.intra_constraints:
            try:
                self.charges = charges_from_punch(f'{punch}.sm')
            except FileNotFoundError:
                raise ValueError(
                    f'FAILED: {punch}.sm not found. See {output}.sm')

        for c, a in zip(self.charges, self.atoms):
            a.charge = c
