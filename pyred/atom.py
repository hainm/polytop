import re
import mendeleev as mv

alpha = re.compile('[a-zA-Z]')


class Atom:
    _symbol = NotImplemented
    atomic_number = 0
    _name = None
    resp_name = ''

    def __init__(self, name, mol):
        self.mol = mol
        self.name = name
        self.h_bonds = set()
        self._resp_number = 0
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
    def resp_number(self):
        return self._resp_number

    @resp_number.setter
    def resp_number(self, value):
        self._resp_number = value
        for atom in self.h_bonds:
            atom._resp_number = value

    def bond_to_heavy(self, other):
        if self._resp_number == 0:  # don't double count
            self._resp_number = other.resp_number
            other.h_bonds.add(self)
            if len(other.h_bonds) >= 2:
                if other.symbol == 'C':
                    other.resp_name = 'CT'
