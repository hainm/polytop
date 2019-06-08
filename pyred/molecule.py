import re
import os
import logging
from collections import namedtuple
import numpy as np
import mendeleev as mv

from .chr_calcul import write_charge_equiv, write_intra_constraints

logger = logging.getLogger(__name__)

alpha = re.compile('[a-zA-Z]')
itp_bonds = re.compile('\s*(?P<ai>\d+)\s*(?P<aj>\d+)\s*\d\s+')


class Atom:
    _symbol = NotImplemented
    atomic_number = 0
    _name = None
    resp_number = 0
    resp_name = ''

    def __init__(self, name, mol):
        self.mol = mol
        self.name = name
        self._n_h_bonds = 0
        self.temp1 = 0
        self.temp2 = 0
        self.temp3 = 0
        self.temp4 = 0

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        letters = alpha.search(name)
        if not letters:
            raise ValueError(f"There is no letter in atom {name}")

        match = letters.group(1)[:2]
        try:
            el = mv.element(match)
        except Exception:
            try:
                el = mv.element(match[:1])
            except Exception:
                raise ValueError(f"There is no letter in atom {name}")

        self.symbol = el.symbol
        self.atomic_number = el.atomic_number
        self.resp_name = name
        self._name = name

    @property
    def full_resp_name(self):
        return f'{self.resp_name}{self.resp_number}'

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self, value):
        if value == 'H':
            self.resp_number = 0
        else:
            self.mol.n_heavy_atoms += 1
            self.resp_number = self.mol.n_heavy_atoms
        self._symbol = value

    @property
    def n_h_bonds(self):
        return self._n_h_bonds

    @n_h_bonds.setter
    def n_h_bonds(self, value):
        """Turn C to CT if it has 2+ bonds to H. Possibly inefficient."""
        if value >= 2:
            if self.symbol == 'C':
                self.resp_name = 'CT'
        self._n_h_bonds = value

    def bond_to_heavy(self, other):
        if self.resp_number == 0:  # don't double count
            self.resp_number = other.resp_number
            other.n_h_bonds += 1


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
                        mol.add_atom(line[12:16].strip())
                        mol.atom_coords.append([xyz])
                    n_atoms += 1

            mol.coords = np.array(mol.atom_coords).T
            mol.count_structures()
            mol.h_bonds_from_itp(itp)
            return mol

    def __init__(self):
        self.name = 'UNK'
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

    def write_resp_input_single(self, job):
        """Write RESP input files for charge calculation"""
        header = [self.create_resp_header(job, nmol=self.n_transforms)]

        atoms1 = self.get_temp_lines(self.temps1)
        charges1 = write_charge_equiv(self.temps1, self.n_structures)

        atoms2 = self.get_temp_lines(self.temps2)
        charges2 = write_charge_equiv(self.temps2, self.n_structures)

        atoms3 = self.get_temp_lines(self.temps3)
        constraints3 = write_intra_constraints(self.constraints, 1)
        charges3 = write_charge_equiv(self.temps3, self.n_structures)

        atoms4 = self.get_temp_lines(self.temps4)
        charges4 = write_charge_equiv(self.temps4, self.n_structures)

        with open(f'input1_{self.name}', 'w') as f:
            f.write('\n'.join(header + atoms1 + charges1))

        with open(f'input2_{self.name}', 'w') as f:
            f.write('\n'.join(header + atoms2 + charges2))

        with open(f'input1_{self.name}.sm', 'w') as f:
            f.write('\n'.join(header + atoms3 + constraints3 + charges3))

        with open(f'input2_{self.name}.sm', 'w') as f:
            f.write('\n'.join(header + atoms4 + charges4))

        logger.info(f'Wrote RESP input files for {self.name}')
