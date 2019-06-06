import re
import mendeleev as mv

alpha = re.compile('[a-zA-Z]')
itp_bonds = re.compile('\s*(?P<ai>\d+)\s*(?P<aj>\d+)\s*\d\s+')

def indices_from_string(string):
    return tuple(int(x)-1 for x in string.split())

class Molecule:
    @classmethod
    def from_pdb(cls, file):
        mol = cls()
        n_atoms = 0

        with open(file, 'r') as f:
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
                            mol.add_inter_mcc(line)
                
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
            mol.n_atoms = len(mol.atom_names)
            mol.determine_elements()
            mol.get_resp_names()
            return mol

    def __init__(self):
        self.name = 'UNK'
        self.atom_names = []
        self.transform_remarks = []
        self.constraints = []
        self.resp_atom_names = []
        self.atom_atomic_numbers = []
        self.atom_numbers = []
        self.n_atoms = 0
        self.n_heavy_atoms = 0
        self.atom_elements = []
        self.coords = None
        self.n_h_bonds = []
        self.transforms = {'REORIENT': set(),
                           'ROTATE': set(),
                           'TRANSLATE': set()}

            
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
                self.atom_atomic_numbers.append(el.atomic_number)
                if el.symbol == 'H':
                    self.atom_numbers.append(0) #placeholder
                else:
                    self.n_heavy_atoms += 1
                    self.atom_numbers.append(self.n_heavy_atoms)
        
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
                            if self.atom_numbers[ai] == 0: # don't count twice
                                self.atom_numbers[ai] = self.atom_numbers[aj]
                                if zj == 'C':
                                    self.n_h_bonds[aj] += 1
                        
                        elif zj == 'H':
                            if self.atom_numbers[aj] == 0:
                                self.atom_numbers[aj] = self.atom_numbers[ai]
                                if zi == 'C':
                                    self.n_h_bonds[ai] += 1
    
    def get_resp_names(self):
        for symbol, n_H in zip(self.atom_elements, self.n_h_bonds):
            if symbol == 'C':
                if n_H > 1:
                    self.resp_atom_names.append('CT')
                    continue
            self.resp_atom_names.append(symbol)

                        




            


    

