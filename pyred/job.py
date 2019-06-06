from .gamess import run_gamess, write_gamess_mep
from .molcollection import MolCollection


class RespJob:
    run_job = NotImplemented
    write_mep = NotImplemented
    _software = None

    def __init__(self, charge_type='RESP-A1', calculate_mep=True,
                 software='GAMESS', n_processors=1, pdbs=[],
                 itps=[], inter_file=None):
        self.charge_type = charge_type
        self.calculate_mep = calculate_mep
        self.software = software
        self.n_processors = n_processors
        self.read_files(pdbs, itps, inter_file)

    def read_files(self, pdbs, itps, inter_file=None):
        self.mols = MolCollection.from_pdbs(pdbs, itps, inter_file)

    def run(self):
        if self.calculate_mep:
            self.run_mep()

    def run_mep(self):
        for i, mol in enumerate(self.mols.mols, 1):
            # write_reddb(mol)

            filenames = self.write_mep(mol)
            for file in filenames:
                self.run_job(file, verify=True)

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
