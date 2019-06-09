import numpy as np


def indices_from_string(string):
    return tuple(int(x)-1 for x in string.split())


class Remark:
    remark = ''
    n_fields = 0
    fields = ''

    @classmethod
    def from_line(cls, line):
        groups = line.split(cls.remark)[-1].split('|')
        try:
            new = cls(*groups)
        except (TypeError, ValueError):
            raise ValueError(f'REMARK {cls.remark} must have '
                             f'{cls.n_fields} fields: {cls.fields}.'
                             f'Integers are indexed from 1.'
                             f'Invalid line: {line}')
        return new


class RemarkIntra(Remark):
    remark = 'INTRA-MCC'
    n_fields = 3
    fields = ('charge (float) | atom numbers (integers) | K/R '
              '(keep/remove)')

    def __init__(self, charge, atoms, keep):
        self.charge = float(charge)
        self.atoms = indices_from_string(atoms)
        self.keep = keep.strip().upper() == 'K'


class RemarkReorient(Remark):
    remark = 'REORIENT'
    n_fields = '>=1'
    fields = 'groups of 3 integer atom numbers'

    @classmethod
    def from_line(cls, line):
        remarks = set()
        groups = line.split(cls.remark)[-1].split('|')
        for group in groups:
            try:
                new = cls(group)
            except (TypeError, ValueError):
                raise ValueError(f'REMARK {cls.remark} must have '
                                 f'{cls.n_fields} fields: {cls.fields}.'
                                 f'Integers are indexed from 1.'
                                 f'Invalid line: {line}')
            remarks.add(new)
        return remarks

    def __eq__(self, other):
        return self.ijk == other.ijk

    def __hash__(self):
        return hash(self.ijk)

    def __init__(self, atoms):
        i, j, k = indices_from_string(atoms)
        self.ijk = (i, j, k)


class RemarkRotate(RemarkReorient):
    remark = 'ROTATE'


class RemarkTranslate(RemarkReorient):
    remark = 'TRANSLATE'
    n_fields = '>1'
    fields = 'groups of 3 floating point coordinate translations'

    def __eq__(self, other):
        return np.array_equal(self.ijk, other.ijk)

    def __init__(self, xyz):
        i, j, k = map(float, xyz)
        self.ijk = np.array([i, j, k])


class InterRemark(Remark):

    @classmethod
    def from_line(cls, collection, line):
        groups = line.split(cls.remark)[-1].split('|')
        try:
            new = cls(collection, *groups)
        except (TypeError, ValueError):
            raise ValueError(f'REMARK {cls.remark} must have '
                             f'{cls.n_fields} fields: {cls.fields}.'
                             f'Integers are indexed from 1.'
                             f'Invalid line: {line}')
        except KeyError:
            raise ValueError(f'REMARK {cls.remark} must specify molecules '
                             'with either the molecule names as given by '
                             'REMARK TITLE or their integer numbers as '
                             f'indexed by 1. Invalid line: {line}')
        return new


class RemarkMeqa(InterRemark):
    remark = 'INTER-MEQA'
    n_fields = 2

    fields = ('Molecule ids (string names or integer numbers) | '
              'integer atom numbers of each molecule.')

    def __init__(self, collection, molecules, atoms):
        try:
            self.mols = indices_from_string(molecules)
        except ValueError:
            self.mols = collection.index(molecules.split())

        self.atoms = indices_from_string(atoms)

        # TODO: check atom name compatibility


class RemarkInter(InterRemark):
    remark = 'INTER-MCC'
    n_fields = 4
    fields = ('floating point charge | 2 molecule ids (string names '
              'or integer numbers) | '
              'integer atom numbers of mol 1 | '
              'integer atom numbers of mol 2. ')

    def __init__(self, collection, charge, molecules, atoms1, atoms2):
        try:
            a, b = indices_from_string(molecules)
        except ValueError:
            a, b = collection.index(molecules.split())

        self.mols = (a, b)
        self.mol1 = a
        self.mol2 = b
        self.charge = float(charge)
        self.atoms1 = indices_from_string(atoms1)
        self.atoms2 = indices_from_string(atoms2)
        self.n_atoms = len(self.atoms1) + len(self.atoms2)


REMARKS = {
    'REORIENT': RemarkReorient,
    'ROTATE': RemarkRotate,
    'TRANSLATE': RemarkTranslate,
    'INTRA-MCC': RemarkIntra,
    'INTER-MCC': RemarkInter,
    'INTER-MEQA': RemarkMeqa
}
