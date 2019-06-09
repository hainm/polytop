import re
import os
import logging
from collections import namedtuple
import numpy as np


from .atom import Atom
from .remark import REMARKS
from .reorientation import rigid_body_orient, rigid_body_rotate
from .chr_calcul import write_charge_equiv, write_intra_constraints

logger = logging.getLogger(__name__)

alpha = re.compile('[a-zA-Z]')
itp_bonds = re.compile('\s*(?P<ai>\d+)\s*(?P<aj>\d+)\s*\d\s+')


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
                            mol.constraints.append(new)

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
        self.constraints = []
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
                        elif zi == 'H':
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

    def write_espot(self, job):
        """ Write espot file."""
        header = f'{len(self.atoms):3d}{{pt:4d}}  {self.charge:2d}    {self.name}'
        all_lines = []

        for c in range(1, self.n_confs+1):
            for w in range(1, self.n_transforms+1):
                basename = f'{self.name}-{c}-{w}'

                point, atoms = job.get_espot_info(basename)

                lines = [header.format(pt=point)] + atoms
                all_lines.extend(lines)
                filename = f'espot_{self.name}-{c}-{w}'
                with open(filename, w) as f:
                    f.write('\n'.join(lines))
                logger.info(f'Wrote {filename}')

        filename = f'espot_{self.name}'
        with open(filename, 'w') as f:
            f.write('\n'.join(all_lines + ['', '']))
        logger.info(f'Wrote {filename}')

        if self.n_transforms <= 1:
            if os.path('./espot1').isfile:
                os.remove('./espot1')
        return all_lines

    def write_espot_conf(self, point, atoms):
        """ Write espot file."""
        header = f'{len(self.atoms):3d}{{pt:4d}}  {self.charge:2d}    {self.name}'
        all_lines = []

        for c in range(1, self.n_confs+1):
            for w in range(1, self.n_transforms+1):
                basename = f'{self.name}-{c}-{w}'

                point, atoms = job.get_espot_info(basename)

                lines = [header.format(pt=point)] + atoms
                all_lines.extend(lines)
                filename = f'espot_{self.name}-{c}-{w}'
                with open(filename, w) as f:
                    f.write('\n'.join(lines))
                logger.info(f'Wrote {filename}')

        filename = f'espot_{self.name}'
        with open(filename, 'w') as f:
            f.write('\n'.join(all_lines + ['', '']))
        logger.info(f'Wrote {filename}')
        return all_lines

    def remove_espot_files(self):
        if self.n_transforms <= 1:
            if os.path('./espot1').isfile:
                os.remove('./espot1')

    def create_resp_header(self, job, nmol=None):
        if nmol is None:
            nmol = self.n_transforms

        return (f' {job.charge_type} RESP input generated PyRESP\n'
                ' @cntrl\n'
                f'  ioutopt=1, iqopt=1, nmol={nmol}, ihfree=1, irstrnt=1, qwt= {job.qwt:5.4f} \n'
                ' &end \n')

    def get_temps(self, job):
        sep = f'\n  1.0\n {self.name} \n{self.charge:>5d}{self.n_atoms:>5d}'
        self.temp_lines = [sep]
        temps = []
        for i, atom in enumerate(self.atoms):
            temps.append(job.get_atom_temps(i, self))
            line = f"  {atom.atomic_number:2d} {{temp:3d}} {'':20} {i+1:3d}"
            self.temp_lines.append(line)
        self.temps1, self.temps2, self.temps3, self.temps4 = zip(*temps)

    def get_temp_lines(self, temps):
        templates = []
        atom_lines = []
        for x, temp in zip(self.temp_lines, temps):
            templates.append(x.format(temp=temp))

        atom_lines = templates * self.n_structures
        atom_lines[0] += f'          Column not used by RESP'  # first line
        return atom_lines

    def write_resp_input_single(self, header):
        """Write RESP input files for charge calculation"""
        header = [header.format(nmol=self.n_transforms)]

        atoms1, charges1 = self.get_atoms_equivalences(self.temps1)
        atoms2, charges2 = self.get_atoms_equivalences(self.temps2)
        atoms3, charges3 = self.get_atoms_equivalences(self.temps3)
        atoms4, charges4 = self.get_atoms_equivalences(self.temps4)

        constraints3 = write_intra_constraints(self.constraints, 1)

        with open(f'input1_{self.name}', 'w') as f:
            f.write('\n'.join(header + atoms1 + charges1))

        with open(f'input2_{self.name}', 'w') as f:
            f.write('\n'.join(header + atoms2 + charges2))

        with open(f'input1_{self.name}.sm', 'w') as f:
            f.write('\n'.join(header + atoms3 + constraints3 + charges3))

        with open(f'input2_{self.name}.sm', 'w') as f:
            f.write('\n'.join(header + atoms4 + charges4))

        logger.info(f'Wrote RESP input files for {self.name}')

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

    def get_transform_equivalence(self, temps):
        conf_lines = []
        if any(x == 0 for x in temps):
            conf_lines.append(INPUT_INTER_REMARK)
        for i, temp in enumerate(temps, 1):
            if temp == 0:
                conf_lines.append(f'  {self.n_structures:3d}')
                conf_line = ''
                for j in enumerate(self.n_structures, 1):
                    conf_line += f'  {j:3d}  {i:3d}'
                    if j and not j % 8:  # new line every 8th step
                        conf_line += '\n'
                conf_line += '\n'
                conf_lines.append(conf_line)
        conf_lines.append('\n\n\n\n\n')
        return conf_lines

    def get_atoms_equivalences(self, temps):
        atoms = self.get_temp_lines(temps)
        confs = self.get_transform_equivalence(temps)
        return atoms, confs

    def write_punch_file(self, charges, atom_name_indices, filename):
        charges = np.array(charges)
        lines = ["     Averaged ESP charges from punch1",
                 "  Z     Equiv.    q(opt)	Rounding-Off"]

        for i, atom in enumerate(self.atoms):
            indices = atom_name_indices.get(atom.full_resp_name, [i])
            equiv_charges = charges[indices]  # get charges of equivalent atoms
            avg = np.mean(equiv_charges)
            z = atom.atomic_number
            j = indices[0]+1  # serial of first match
            lines.append(f"{z:<2d}     {j:<2d}     {avg:<8.7f}  {avg:<5.4f}")

        with open(filename, 'w') as f:
            f.write('\n'.join(lines))
        logger.info(f'Wrote {filename}')

    def get_atom_name_indices(self):
        indices = {}
        for i, atom in enumerate(self.atoms):
            if atom.full_resp_name in indices:
                indices[atom.full_resp_name].append(i)
            else:
                indices[atom.full_resp_name] = [i]
        return indices

    def write_all_punch_files(self):
        indices = self.get_atom_name_indices()
        try:
            charges = charges_from_punch(f'punch1_{self.name}')
            self.write_punch_file(charges, indices, f'punch2_{self.name}')
        except FileNotFoundError:
            pass

        if self.constraints:
            atoms = set([x for y in self.constraints for x in y.atoms])
            free_indices = {}
            for k, v in indices.items():
                free_indices[k] = [x for x in v if x not in atoms]
            try:
                charges = charges_from_punch(f'punch1_{self.name}.sm')
                self.write_punch_file(charges, free_indices,
                                      f'punch2_{self.name}.sm')
            except FileNotFoundError:
                pass
