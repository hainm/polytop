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
    _charge_type = 'RESP-A1'

    def __init__(self, charge_type='RESP-A1', calculate_mep=True,
                 software='GAMESS', n_processors=1, pdbs=[],
                 itps=[], inter_file=None):
        self.get_atom_temps = resp_1_temps
        self.run_resp = run_resp_1
        self.charge_type = charge_type
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
        for mol in self.mols.mols:
            mol.write_espot(self)
            mol.write_resp_input(self)
            self.run_resp(mol)

        # INTER_Calcul

    def run_mep(self):
        for i, mol in enumerate(self.mols.mols, 1):
            # write_reddb(mol)

            filenames = self.write_mep(mol)
            for file in filenames:
                self.run_job(file, verify=True)

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

    def write_espot_all(self):
        lines = []
        for mol in self.mols.mols:
            lines.extend(mol.write_espot(job))
        lines += ['', '']
        with open("espot_mm", 'w') as f:
            f.write('\n'.join(lines))
        logger.info('Wrote espot_mm')

    def write_espot_single(self):
        for mol in self.mols.mols:
            mol.write_espot(job)
