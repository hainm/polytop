import logging
import os
import subprocess

from .gamess import GAMESS
from .molcollection import MolCollection

logger = logging.getLogger(__name__)


def same_number_with_T(atom, mol):
    """If another atom has the same number and its name ends with T"""
    for other in mol.atoms:
        if atom.resp_number == other.resp_number:
            if other.resp_name[-1] == 'T':
                return True
    return False


def run_resp(self, input_no, name, extension=""):
    """ Run resp in the system """
    suffix = f'{name}{extension}'
    rinput = f'input{input_no}_{suffix}'
    routput = f'output{input_no}_{suffix}'
    punch = f'punch{input_no}_{suffix}'

    espot = f'espot_{suffix}'
    qwts = f'qwts_{suffix}'
    esout = f'esout_{suffix}'

    qqout = f'qout{input_no-1}_{suffix}'
    qtout = f'qout{input_no}_{suffix}'

    subprocess.run(['resp', '-0', '-i', rinput, '-o', routput, '-p', punch,
                    '-e', espot, '-q', qqout, '-t', qtout, '-w', qwts, '-s',
                    esout], stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


class JobBase:
    _software = None
    qwt = 0
    firefly = False  # PCGVAR == 0 : No firefly found, PCGVAR==1: Firefly found

    def __init__(self, charge_type='RESP-A1',
                 software='GAMESS', n_processors=1, pdbs=[],
                 itps=[], inter_file=None, debug=False):
        self.charge_type = charge_type
        self.software = software
        self.n_processors = n_processors
        self.read_files(pdbs, itps, inter_file)

        self.resp_header = (f' {self.charge_type} RESP input generated PyRESP\n'
                            ' @cntrl\n'
                            f'  ioutopt=1, iqopt=1, nmol={{nmol}}, ihfree=1, irstrnt=1, qwt= {self.qwt:5.4f} \n'
                            ' &end \n')

    def read_files(self, pdbs, itps, inter_file=None):
        self.mols = MolCollection.from_pdbs(pdbs, itps, inter_file)

    def run(self):
        self.run_mep_and_espot()
        self.write_resp_input()

    @property
    def software(self):
        return self._software

    @software.setter
    def software(self, value):
        program = value.upper()
        if program == 'GAMESS':
            self.program = GAMESS()
        self.software = program

    def run_mep_and_espot(self):
        all_lines = []
        for mol in self.mols.mols:
            mol.write_redpdb()  # possibly unnecessary

            logger.info(f'Computing MEP for {mol.name}...')
            C, T, n_atoms = mol.n_confs, mol.n_transforms, mol.n_atoms
            header = f'{n_atoms:3d}{{pt:4d}}  {mol.charge:2d}    {mol.name}'
            prefix = self.program.get_mep_prefix(self, mol)
            lines = []
            for c, conf in enumerate(mol.get_mep_coordinates(), 1):
                for t, coords in enumerate(conf, 1):
                    # MEP_Calcul
                    logger.info(f'\t\tConf {c}/{C}, Transform {t}/{T}')
                    basename = f'{mol.name}-c{c:02d}-t{t:02d}'
                    self.program.write_job_file(basename, prefix, mol.atoms,
                                                coords)
                    self.program.run(basename, verify=True)

                    # Makespot
                    lines.extend(self.write_espot_single(
                        basename, mol, header))

            # Makespot
            mol_espot_name = f'espot_{mol.name}'
            with open(mol_espot_name, 'w') as f:
                f.write('\n'.join(lines + ['', '']))
            logger.info(f'Wrote {mol_espot_name}')

            mol.remove_espot_files()
            all_lines.extend(lines)

        # Inter_Calcul
        espot_name = f'espot_mm'
        with open(espot_name, 'w') as f:
            f.write('\n'.join(all_lines + ['', '']))
        logger.info(f'Wrote {espot_name}')

        logger.info('Finished all MEP computations.')

    def write_espot_single(self, basename, mol, header):
        point, atoms = self.program.get_espot_info(basename, mol)
        lines = [header.format(pt=point)] + atoms
        filename = f'espot_{basename}'
        with open(filename, 'w') as f:
            f.write('\n'.join(lines))
        logger.info(f'Wrote {filename}')
        return lines

    def write_resp_input(self):
        for mol in self.mols.mols:
            # Inputgene
            self.get_temps(mol)
            inputs = self.write_intra_resp(mol)
            # CHR_Calcul
            for i in inputs:
                run_resp(*i)
            self.get_charges_from_punch(mol)
        # Inter_Calcul
        inputs = self.write_inter_resp()
        for i in inputs:
            run_resp(*i)
        self.get_all_charges()  # TODO link punchx_mm charges to real charges I want

    def get_temps(self, mol):
        mol.create_temp_lines()
        temps = []
        for i, atom in enumerate(mol.atoms):
            temps.append(self.get_atom_temps(i, atom, mol))
        mol.temps1, mol.temps3 = zip(*temps)

    def write_intra_resp(self, mol):
        return mol.write_resp_input(self.resp_header, mol.temps1, mol.temps3,
                                    input_no=1)

    def write_inter_resp(self):
        self.mols.write_resp_input_1(self.resp_header)
        return [(1, 'mm', '')]

    def get_charges_from_punch(self, mol):
        raise NotImplementedError

    def get_atom_temps(self, i, atom, mol):
        raise NotImplementedError


class JobResp1(JobBase):
    """Job class for RESP-A1, RESP-C1"""
    qwt = 0.0005

    def charges_from_punch(self, mol):
        mol.check_punch_files(n_punch=1)
        mol.check_punch_files(n_punch=2)

    def write_intra_resp(self, mol):
        files = mol.write_resp_input(self.resp_header, mol.temps1, mol.temps3,
                                     input_no=1)
        files.extend(mol.write_resp_input(self.resp_header, mol.temps2, mol.temps4,
                                          input_no=2))
        return files

    def write_inter_resp(self):
        self.mols.write_resp_input_both(self.resp_header)
        return [(1, 'mm', ''), (2, 'mm', '')]

    def get_temps(self, mol):
        mol.create_temp_lines()
        temps = []
        for i, atom in enumerate(mol.atoms):
            temps.append(self.get_atom_temps(i, atom, mol))
        mol.temps1, mol.temps2, mol.temps3, mol.temps4 = zip(*temps)

    @staticmethod
    def get_atom_temps(i, atom, mol):
        """ Get temp values for RESP-A1, RESP-C1, DEBUG"""
        temp1 = temp2 = temp3 = temp4 = 0

        for j, other in enumerate(mol.atoms[:i], 1):
            if atom.full_resp_name == other.full_resp_name:
                if (atom.resp_name[-1] == 'T' or same_number_with_T(atom, mol)):
                    temp1 = 0
                    temp2 = j
                    temp3 = 0
                    temp4 = j
                else:
                    temp1 = j
                    temp2 = -1
                    temp3 = j
                    temp4 = -1
                break

        for constr in mol.constraints:
            if i in constr.atoms:
                temp4 = -1
                break

        return temp1, temp2, temp3, temp4


class JobResp2(JobBase):
    """Job class for RESP-A2, RESP-C2"""
    qwt = 0.01

    def charges_from_punch(self, mol):
        mol.check_punch_files(n_punch=1)

    @staticmethod
    def get_atom_temps(i, atom, mol):
        """Get temp values for RESP-A2, RESP-C2, ESP-A1, ESP-A2"""
        temp1 = temp3 = 0
        for j, other in enumerate(mol.atoms[:i], 1):
            if atom.full_resp_name == other.full_resp_name:
                temp1 = j
                temp3 = j
                break

        return temp1, temp3


class JobEsp1(JobResp2):
    qwt = 0.0000


class JobEsp2(JobBase):
    qwt = 0.0000

    def charges_from_punch(self, mol):
        mol.check_punch_files(n_punch=1)
        mol.write_punch_2_files()

    @staticmethod
    def get_atom_temps(i, atom, mol):
        """Get temp values for ESP-A2, ESP-C2"""
        temp1 = temp3 = 0

        for j, other in enumerate(mol.atoms[:i], 1):
            if atom.full_resp_name == other.full_resp_name:
                if any(j-1 in constr.atoms for constr in mol.constraints):
                    temp3 = j
                break

        return temp1, temp3


RESP_JOBS = {
    'RESP-A2': JobResp2,
    'RESP-C2': JobResp2,
    'RESP-A1': JobResp1,
    'RESP-C1': JobResp1,
    'ESP-A1': JobEsp1,
    'ESP-C1': JobEsp1,
    'ESP-A2': JobEsp2,
    'ESP-C2': JobEsp2
}
