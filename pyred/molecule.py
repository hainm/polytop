import re
import os
import logging
import numpy as np
import mendeleev as mv

from .chr_calcul import input_inter, input_intra

logger = logging.getLogger(__name__)


alpha = re.compile('[a-zA-Z]')
itp_bonds = re.compile('\s*(?P<ai>\d+)\s*(?P<aj>\d+)\s*\d\s+')


def indices_from_string(string):
    return tuple(int(x)-1 for x in string.split())


class Molecule:
    @classmethod
    def from_pdb(cls, pdb, itp):
        mol = cls()
        n_atoms = 0

        with open(pdb, 'r') as f:
            for line in f:
                record = line[:6].strip()
                fields = line[6:]

                if record == 'END':
                    return mol

                elif record == 'TER':
                    n_atoms = 0

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
                            mol.add_intra_mcc(remark, line)

                elif record in ('ATOM', 'HETATM'):
                    _xyz = [line[30:38], line[38:46], line[46:54]]
                    xyz = list(map(float, _xyz))
                    try:
                        mol.atom_coords[n_atoms].append(xyz)
                    except IndexError:
                        mol.atom_names.append(line[12:16].strip())
                        mol.atom_coords.append([xyz])
                    n_atoms += 1

            mol.coords = np.array(mol.atom_coords).T
            mol.count_structures()
            mol.determine_elements()
            mol.h_bonds_from_itp(itp)
            mol.get_resp_names()
            return mol

    def __init__(self):
        self.name = 'UNK'
        self.atom_names = []
        self.atom_coords = []
        self.transform_remarks = []
        self.constraints = []
        self.resp_atom_names = []
        self.atomic_Z = []
        self.resp_atom_numbers = []
        self.n_atoms = 0
        self.n_heavy_atoms = 0
        self.atom_elements = []
        self.coords = None
        self.n_h_bonds = []
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
        groups = line.split(remark)[-1].split('|')

        if remark in ('REORIENT', 'ROTATE'):
            for group in groups:
                try:
                    ijk = indices_from_string(group)
                except ValueError:
                    raise ValueError('%s requires groups of 3 integer '
                                     'atom numbers. Invalid line: %s'
                                     % (remark, line))
                self.transforms[remark].add(ijk)

        elif remark == 'TRANSLATE':
            for group in groups:
                try:
                    i, j, k = map(float, group.split())
                except ValueError:
                    raise ValueError('%s requires groups of 3 coordinate '
                                     'floating point number values. '
                                     'Invalid line: %s' % (remark, line))
                self.transforms[remark].add(np.array([i, j, k]))

    def add_intra_mcc(self, remark, line):
        groups = line.split(remark)[-1].split('|')

        try:
            charge, atoms, keep = groups
        except ValueError:
            raise ValueError('INTRA-MCC must have 3 fields:'
                             'charge | atom numbers | K/R. Invalid '
                             'line: %s' % line)
        try:
            entry = {
                'charge': float(charge),
                'atoms': indices_from_string(atoms),
                'keep': keep.strip().upper() == 'K'
            }
        except ValueError:
            raise ValueError('INTRA-MCC fields must have a single '
                             'float charge, at least one integer '
                             'atom number, and either K or R. '
                             'Invalid line: %s' % line)
        self.constraints.append(entry)

    def determine_elements(self):
        for name in self.atom_names:
            letters = alpha.search(name)
            if letters:
                match = letters.group(1)[:2]
                try:
                    el = mv.element(match)
                except Exception:
                    try:
                        el = mv.element(match[:1])
                    except Exception:
                        raise ValueError(f"There is no letter in atom {name}")
                self.atom_elements.append(el.symbol)
                self.atomic_Z.append(el.atomic_number)
                if el.symbol == 'H':
                    self.resp_atom_numbers.append(0)  # placeholder
                else:
                    self.n_heavy_atoms += 1
                    self.resp_atom_numbers.append(self.n_heavy_atoms)

        else:
            raise ValueError(f"There is no letter in atom {name}")

    def h_bonds_from_itp(self, itp):
        bond_section = False

        with open(itp, 'r') as f:
            for line in f:
                if '[ bonds ]' in line:
                    self.n_h_bonds = [0] * self.n_atoms
                    bond_section = True
                    continue
                if bond_section:
                    match = itp_bonds.match(line)
                    if match:
                        ai = match.group('ai') - 1
                        aj = match.group('aj') - 1

                        zi = self.atom_elements[ai]
                        zj = self.atom_elements[aj]

                        if zi == 'H':
                            # don't count twice
                            if self.resp_atom_numbers[ai] == 0:
                                self.resp_atom_numbers[ai] = self.resp_atom_numbers[aj]
                                if zj == 'C':
                                    self.n_h_bonds[aj] += 1

                        elif zj == 'H':
                            if self.resp_atom_numbers[aj] == 0:
                                self.resp_atom_numbers[aj] = self.resp_atom_numbers[ai]
                                if zi == 'C':
                                    self.n_h_bonds[ai] += 1

    def get_resp_names(self):
        for symbol, n_H in zip(self.atom_elements, self.n_h_bonds):
            if symbol == 'C':
                if n_H > 1:
                    self.resp_atom_names.append('CT')
                    continue
            self.resp_atom_names.append(symbol)

    def write_espot(self, job):
        header = f'{self.n_atoms:3d}{{pt:4d}}  {self.charge:2d}    {self.name}'
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

    def write_resp_input(self, job):
        header = (f' {job.charge_type} RESP input generated PyRESP\n'
                  ' @cntrl\n'
                  f'  ioutopt=1, iqopt=1, nmol={self.n_transforms}, ihfree=1, irstrnt=1, qwt= {job.qwt:5.4f} \n'
                  ' &end \n'
                  '  1.0\n'
                  f' {self.name} \n'
                  f'{self.charge:5}{self.n_atoms:5d}          Column not used by RESP')

        lines = [header]
        atom_lines = ['', f'1.0\n {self.name}']
        temps = []

        for i, z in enumerate(self.atomic_Z):
            line = f"  {z:2d} {{temp:3d}}                      {i+1:3d}"
            atom_lines.append(line)
            temps.append(job.get_atom_temps(i, self))

        temp1, temp2, temp3, temp4 = zip(*temps)

        atoms1, inter_conf1 = input_inter(atom_lines, temp1, self.n_structures)
        atoms2, inter_conf2 = input_inter(atom_lines, temp2, self.n_structures)
        atoms3, inter_conf3 = input_inter(atom_lines, temp3, self.n_structures)
        atoms4, inter_conf4 = input_inter(atom_lines, temp4, self.n_structures)

        intra_confs = input_intra(self)

        with open(f'input1_{self.name}', 'w') as f:
            f.write('\n'.join(lines + atoms1 + inter_conf1))

        with open(f'input2_{self.name}', 'w') as f:
            f.write('\n'.join(lines + atoms2 + inter_conf2))

        with open(f'input1_{self.name}.sm', 'w') as f:
            f.write('\n'.join(lines + atoms3 + intra_confs + inter_conf3))

        with open(f'input2_{self.name}.sm', 'w') as f:
            f.write('\n'.join(lines + atoms4 + inter_conf4))

        logger.info(f'Wrote RESP input files for {self.name}')

        return temp3
