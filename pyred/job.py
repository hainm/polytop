import logging
import os

from .gamess import run_gamess, write_gamess_mep, get_espot_info_gamess
from .molcollection import MolCollection
from .chr_calcul import (resp_1_temps, resp_2_temps, esp_temps,
                         input_inter, input_intra, run_resp_1, run_resp_2, run_resp_3)

logger = logging.getLogger(__name__)


class RespJob:
    run_job = NotImplemented
    write_mep = NotImplemented
    _software = None
    qwt = 0
    firefly = False  # PCGVAR == 0 : No firefly found, PCGVAR==1: Firefly found
    _charge_type = 'RESP-A1'

    def __init__(self, charge_type='RESP-A1', calculate_mep=True,
                 software='GAMESS', n_processors=1, pdbs=[],
                 itps=[], inter_file=None, debug=False):
        self.get_atom_temps = resp_1_temps
        self.run_resp = run_resp_1
        self.charge_type = charge_type
        if debug:
            self.charge_type = 'DEBUG'
        self.calculate_mep = calculate_mep
        self.software = software
        self.n_processors = n_processors
        self.read_files(pdbs, itps, inter_file)

    def read_files(self, pdbs, itps, inter_file=None):
        self.mols = MolCollection.from_pdbs(pdbs, itps, inter_file)

    def run(self):
        # MEP_Calcul
        if self.calculate_mep:
            self.run_mep()

        # CHR_Calcul
        self.write_espot()
        for mol in self.mols.mols:
            mol.write_espot(self)
            mol.write_resp_input(self)
            self.run_resp(mol)

        # INTER_Calcul

    @property
    def charge_type(self):
        return self._charge_type

    @charge_type.setter
    def charge_type(self, value):
        self.write_espot = self.write_espot_all

        if value == 'DEBUG':
            self.qwt = 0.0005
            self.get_atom_temps = resp_2_temps
            self.run_resp = run_resp_1
            self.write_espot = self.
        elif value == 'RESP-A1':
            self.qwt = 0.0005
            self.get_atom_temps = resp_2_temps
            self.run_resp = run_resp_2
        elif value == 'RESP-C1':
            self.qwt = 0.0005
            self.get_atom_temps = resp_2_temps
            self.run_resp = run_resp_2
        elif value == 'RESP-A2':
            self.qwt = 0.01
            self.get_atom_temps = resp_1_temps
            self.run_resp = run_resp_1
        elif value == 'RESP-C2':
            self.qwt = 0.01
            self.get_atom_temps = resp_1_temps
            self.run_resp = run_resp_1
        elif value == 'ESP-A1':
            self.qwt = 0.0000
            self.get_atom_temps = resp_1_temps
            self.run_resp = run_resp_3
        elif value == 'ESP-C1':
            self.qwt = 0.0000
            self.get_atom_temps = resp_1_temps
            self.run_resp = run_resp_3
        else:
            self.qwt = 0.0000
            self.get_atom_temps = esp_temps
            self.run_resp = run_resp_1
            self.write_espot = self.write_espot_single
        self._charge_type = value

    @property
    def software(self):
        return self._software

    @software.setter
    def software(self, value):
        program = value.upper()
        if program == 'GAMESS':
            self.run_job = run_gamess
            self.write_mep = write_gamess_mep
            self._software = program
            self.get_espot_info = get_espot_info_gamess

    def write_espot(self):
        lines = []
        for mol in self.mols.mols:
            lines.extend(mol.write_espot(self))
        lines += ['', '']
        with open("espot_mm", 'w') as f:
            f.write('\n'.join(lines))
        logger.info('Wrote espot_mm.')

    def run_mep_and_espot(self):
        all_lines = []
        for mol in self.mols.mols:
            mol.write_redpdb()  # possibly unnecessary

            logger.info(f'Computing MEP for {mol.name}...')
            C, T, n_atoms = mol.n_confs, mol.n_transforms, mol.n_atoms
            espot_header = f'{n_atoms:3d}{{pt:4d}}  {mol.charge:2d}    {mol.name}'
            prefix = self.get_mep_prefix(mol)
            lines = []
            for c, conf in enumerate(mol.get_mep_coordinates(), 1):
                for t, coords in enumerate(conf, 1):
                    # MEP_Calcul
                    logger.info(f'\t\tConf {c}/{C}, Transform {t}/{T}')
                    basename = f'{mol.name}-c{c:02d}-t{t:02d}'
                    self.write_mep_input(basename, prefix, mol.atoms, coords)
                    self.run_job(basename, verify=True)

                    # Makespot
                    lines.extend(self.write_espot_single(basename, header))

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

    def write_espot_single(self, basename, header):
        point, atoms = self.get_espot_info(basename)
        lines = [header.format(pt=point)] + atoms
        filename = f'espot_{basename}'
        with open(filename, 'w') as f:
            f.write('\n'.join(lines))
        logger.info(f'Wrote {filename}')
        return lines

    def run_chr_calc(self):
        if self.calculate_mep:
            self.write_input()

    def write_resp_input(self):
        # Inputgene
        header = (f' {self.charge_type} RESP input generated PyRESP\n'
                  ' @cntrl\n'
                  f'  ioutopt=1, iqopt=1, nmol={{nmol}}, ihfree=1, irstrnt=1, qwt= {self.qwt:5.4f} \n'
                  ' &end \n')
        for mol in self.mols.mols:
            mol.write_resp_input_single(header)
            # CHR_Calcul
            self.run_resp(mol.name)
            self.read_punch(mol)

    def read_punch(self, mol):
        if self.charge_type in ('ESP-A2', 'ESP-C2'):
