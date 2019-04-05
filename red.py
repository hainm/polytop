import os
import re
import datetime
import itertools
import numpy as np

def get_welcome_message(CHR_TYPE):
    debug_msg = ''
    if CHR_TYPE == 'DEBUG':
        debug_msg = "\n   Job generated for debugging purposes - Charge values are rotten!\n"
    msg = f"""
    	      ---------------------------
		     *  Welcome to R.E.D. III.4  *
		         RESP ESP charge Derive  
		  http://q4md-forcefieldtools.org/RED/ 

                --- Python version ---
                Author: Lily Wang
                Email: lily.wang@anu.edu.au
                    April 2019

    Distributed under the GNU General Public License
		      ---------------------------
		         CHARGE TYPE = {CHR_TYPE}{debug_msg}
		      ---------------------------

		  Date: {}
		  Machine: {}

		  Number of cpu(s) used in the QM jobs(s): {}
		      ---------------------------
		        * Operating system *
{' '.join(os.uname())}
		      ---------------------------
    """
    return msg


PDB_LINES = {
    'TITLE': 'REMARK TITLE',
    'CHARGE': 'REMARK CHARGE-VALUE',
    'MULTIPLICITY': 'REMARK MULTIPLICITY-VALUE',
    'ORIENT': 'REMARK ORIENT',
    'ROTATE': 'REMARK ROTATE',
    'TRANSLATE': 'REMARK TRANSLATE',
    'INTRA-MCC': 'REMARK INTRA-MCC',
    'INTER-MCC': 'REMARK INTER-MCC'
}

class Parameter:

    def error(self, msg, line):
        raise ValueError(msg + f' (Line: {line})')

class Atom:
    def __init__(self, line):
        fields = line.split()
        self.name = fields[2].strip()
        self.name_without_number = re.sub(f'[0-9]+', '', self.name)
        self.number = re.sub(r'[^0-9]', '', self.name)
        if len(fields) == 8:
            self.symbol = fields[-1]
        else:
            self.symbol = re.sub('T$', '', self.name_without_number)
        self.coords = tuple(map(float, fields[5:8]))

class MCCIntra(Parameter):

    p2n = 'REMARK INTRA-MCC'

    def __init__(self, line, n_atoms):
        constraint, atoms, Flag = line.split(self.p2n)[1].split('|')[:2]
        try:
            self.constraint = float(constraint)
        except ValueError:
            self.error(f'Invalid charge value {constraint}', line)
        try:
            self.atoms = map(int, atoms)
        except ValueError:
            self.error(f'Invalid atom numbers {atoms}', line)
        
        if not all(x >= 1 and x <= n_atoms for x in self.atoms):
            self.error(f'Atom numbers must be between 1 and {n_atoms}', line)
        if len(atoms) > n_atoms:
            self.error('Atom numbers in intra-molecular charge constraint cannot exceed total number of atoms', line)

        flag = Flag.lower()
        if flag not in ('K', 'R'):
            self.error('Bad flag in intramolecular charge constraint: Only K (Keep) or R (remove) allowed', line)
        if flag == 'k':
            self.keep = True
        else:
            self.keep = False

class MCCInter:
    p2n = 'REMARK INTER-MCC'

    def __init__(self, line, n_mols):
        try:
            constraint, molecules, atoms1, atoms2 = line.split(self.p2n)[1].split()[:4]
        except ValueError:
            self.error('Not enough fields specified', line)
        
        try:
            self.constraint = float(constraint)
        except ValueError:
            self.error(f'Invalid charge value {constraint}', line)
        
        try: 
            self.molecules = map(int(molecules.split()))
        except ValueError:
            self.error(f'Invalid molecule numbers {molecules}', line)
        
        if len(self.molecules) != 2:
            self.error(f'Only 2 molecules allowed', line)
        
        if max(self.molecules) <= n_mol:
            self.error(f'Molecule numbers must be between 1 and {n_mol}', line)
        if not min(self.molecules) == 1:
            self.error('Molecule 1 must be involved', line)
        
        try:
            self.atoms1 = map(int, atoms1.split())
        except ValueError:
            self.error('Atom numbers must be integers', line)
        # check atom numbers less than n_atoms etc

        try:
            self.atoms2 = map(int, atoms2.split())
        except ValueError:
            self.error('Atom numbers must be integers', line)




class Molecule:
    def __init__(self, counter=1):
        self.title = f'Molecule_{counter}'
        self.charge = 0
        self.multiplicity = 1
        self.atoms = []
        self.bonds = []
        self.orientations = []
        self.rotations = []
        self.translations = []
        self.mccs = []
    
    def read_pdb(self, pdb):
        with open(pdb, 'r') as f:
            contents = [x.strip() for x in f.readlines()]
        
        for line in contents:
            if line.startswith(PDB_LINES['TITLE']):
                self.title = line.split(PDB_LINES['TITLE'])[1]

            elif line.startswith(PDB_LINES['CHARGE']):
                chr_val = line.split(PDB_LINES['CHARGE'])[1]
                try:
                    self.chr_val = int(chr_val)
                except ValueError:
                    raise ValueError(f'Invalid charge value: {chr_val}')

            elif line.startswith(PDB_LINES['MULTIPLICITY']):
                mlt_val = line.split(PDB_LINES['MULTIPLICITY'])[1]
                try:
                    self.mlt_val = int(mlt_val)
                except ValueError:
                    raise ValueError(f'Invalid multiplicity value: {mlt_val}')
            
            elif line.startswith('ATOM') or line.startswith('HETATM'):
                self.atoms.append(Atom(line))

            elif line.startswith('CONECT'):
                atom1, *connected = line.split()[1:]
                for atom2 in connected:
                    bond1, bond2 = f'{atom1}-{atom2}', f'{atom2}-{atom1}'
                    if not bond1 in self.bonds and not bond2 in self.bonds:
                        self.bonds.append(bond1)
            
            elif line.startswith(PDB_LINES['ORIENT'])
                orients = line.split(PDB_LINES['ORIENT'])[1].split('|')
                for group in orients:
                    try:
                        atoms = map(int, group.split())
                    except:
                        raise ValueError(f'ERROR: Bad format in three atom based re-orientation! {group}')

                    if len(atoms) != 3:
                        raise ValueError(f'ERROR: three atoms must be specified for orientation, you gave {len(atoms)}: {group}')
                    self.orientations.append(atoms)

            elif line.startswith(PDB_LINES['ROTATE']):
                rotates = line.split(PDB_LINES['ROTATE'])[1]
                for group in rotates:
                    try:
                        atoms = map(int, group.split())
                    except:
                        raise ValueError(f'ERROR: Bad format in three atom based rotation! {group}')

                    if len(atoms) != 3:
                        raise ValueError(f'ERROR: three atoms must be specified for rotation, you gave {len(atoms)}: {group}')
                    self.rotations.append(atoms)
            
            elif line.startswith(PDB_LINES['TRANSLATE']):
                translates = line.split(PDB_LINES['TRANSLATE'])[1]
                for group in translates:
                    try:
                        atoms = map(int, group.split())
                    except:
                        raise ValueError(f'ERROR: Bad format in three atom based translation! {group}')

                    if len(atoms) != 3:
                        raise ValueError(f'ERROR: three atoms must be specified for translation, you gave {len(atoms)}: {group}')
                    self.translations.append(atoms)
                
            elif line.startswith(PDB_LINES['INTRA-MCC']):
               self.mcc.append(MCCIntra(line))
            
            # to do: inter mcc
            # meqa (around lines 1140)
                



            elif line.startswith('TER'):
                break
        
    def check_pdb(self):
        """ Continuation of ReadPDB. """

        # Check if there are two different elements ending with a "T" and a same number
        for atom1, atom2 in itertools.permutations(self.atoms, 2):
            if atom1.name_without_number.endswith('T') and atom2.name_without_number.endswith('T'):
                sub1 = atom1.name_without_number[:-1]
                sub2 = atom2.name_without_number[:-1]
                if sub1 != sub2 and atom1.number == atom2:
                    raise ValueError(f'Error: Redundant number in atom names {atom1.name}, {atom2.name}')

        # check if atoms are in the same order
        # check if multiple atoms end in T

