var PolyTop = {};

PolyTop.MoleculeTop = function (molecule) {
      this.molecule = molecule;
      this.init()

      return this
}

PolyTop.MoleculeTop.prototype.init = function () {
    this.atoms = [];
    this.residues = [];
    this.chargeGroups = [];
    this.paramNames = [];
    this.paramItems = {};
    this.completeTopology = false;
}

PolyTop.MoleculeTop.prototype.addParsedITP = function (molecule) {
    this.init()
    this.addAtoms(molecule.atoms);
    this.addParams(molecule);
    this.completeTopology = true;
};


PolyTop.MoleculeTop.prototype.addNGLStructure = function (structure) {
    var self = this;
    this.init()
    if (!structure) {structure = self.structure}
    var atoms = []
    structure.eachAtom(function (atomProxy) {
        atoms.push({items: {
            name: atomProxy.atomname,
            chargeGroupSeq: atomProxy.serial,
            resSeq: atomProxy.resno,
            resName: atomProxy.resname
            }
        })
    })
    self.addAtoms(atoms)
    
}

PolyTop.MoleculeTop.prototype.toMonomer = function (name) {
    var self = this;
    var res = new PolyTop.ResidueTop(self, name)
    self.residues = [res]
    self.atoms.forEach(function (atom) {
        atom.setResidue(res)
    })
    self.removeEmpty()
    res.renameAtomsUnique()
}

PolyTop.MoleculeTop.prototype.orderByResidue = function () {
    var self = this;
    self.atoms = []
    self.residues.forEach(function (res) {
        self.atoms = self.atoms.concat(res.atoms)
    })
    self.chargeGroups = []
    self.atoms.forEach(function (atom) {
        if (!self.chargeGroups.includes(atom.chargeGroup)) {
            self.chargeGroups.push(atom.chargeGroup)
        }
    })
}

PolyTop.MoleculeTop.prototype.addAtoms = function (atomList) {
    var self = this;
    var currentResidue = new PolyTop.ResidueTop(self);
    var currentChargeGroup = new PolyTop.ChargeGroup(self);
    var lastResSeq = -1;
    var lastChargeGroupSeq = -1;
    atomList.forEach(function (atomObject) {
        var _atom = atomObject.items
        if (_atom.chargeGroupSeq !== lastChargeGroupSeq) {
            if (currentChargeGroup.atoms.length > 0) {
                self.chargeGroups.push(currentChargeGroup);
            }
            currentChargeGroup = new PolyTop.ChargeGroup(self);
            lastChargeGroupSeq = _atom.chargeGroupSeq;
        }
        if (_atom.resSeq !== lastResSeq) {
            if (currentResidue.atoms.length > 0) {
                self.residues.push(currentResidue);
                currentResidue.updateStructureResidue()
            }
            currentResidue = new PolyTop.ResidueTop(self, _atom.resName);
            lastResSeq = _atom.resSeq;
        }
        var atomTop = new PolyTop.AtomTop(self, currentResidue, currentChargeGroup, atomObject);
        currentResidue.atoms.push(atomTop);
        
        self.atoms.push(atomTop);
        currentChargeGroup.atoms.push(atomTop);
        atomTop.updateStructureAtom()
        
    });
    if (currentChargeGroup.atoms.length > 0) {
        self.chargeGroups.push(currentChargeGroup);
    };
    if (currentResidue.atoms.length > 0) {
        self.residues.push(currentResidue);
        currentResidue.updateStructureResidue()
    };
};
PolyTop.MoleculeTop.prototype.addParams = function (other) {
    var self = this;
    other.paramNames.forEach(function (name) {
        self.checkAddParam(name)
        var selfList = self.paramItems[name]
        var thatList = other.paramItems[name]

        thatList.forEach(function (param) {
            if (self.containsAtomIndices(param.atomIndices)) {
                selfList.push(new PolyTop.ParamTop(self, param))
            }
        })

    })
};

PolyTop.MoleculeTop.prototype.checkAddParam = function (name) {
    var self = this;
    if (!self.paramNames.includes(name)) {
        self.paramNames.push(name)
        self.paramItems[name] = []
    }
}

PolyTop.MoleculeTop.prototype.addParamsFromOther = function (other) {
    var self = this;
    other.paramNames.forEach(function (name) {
        self.checkAddParam()

    })
    thatList.forEach(function (param) {
            if (self.containsAtomIndices(param.atomIndices)) {
                selfList.push(new PolyTop.ParamTop(self, param))
            }
        })
}

PolyTop.MoleculeTop.prototype.containsAtomIndices = function (atomIndices) {
    var self = this;
    atomIndices.forEach(function (index) {
        if (index >= self.atoms.length) {
            return false;
        }
    });
    return true;
};
PolyTop.MoleculeTop.prototype.addOther = function (other) {
    var self = this;
    other.atoms.forEach(function (atom) {
        atom.updateStructureAtom()
        atom.molecule = self;
        self.atoms.push(atom);
    });
    other.residues.forEach(function (res) {
        res.updateStructureResidue()
        res.molecule = self;
        self.residues.push(res);
    });
    
    other.chargeGroups.forEach(function (cg) {
        cg.molecule = self;
        self.chargeGroups.push(cg);
    });
    self.addParams(other);
};

PolyTop.MoleculeTop.prototype.updateFromStructure = function () {
    var self = this;
    self.atoms.forEach(function (atom) {
        atom.updateStructureAtom()
    })
    self.residues.forEach(function (res) {
        res.updateStructureResidue()
    })
}

Object.defineProperty(PolyTop.MoleculeTop.prototype, "paramLists", {
    get: function () {
        var self = this;
        var value = []
        this.paramNames.forEach(function (name) {
            value.push(self.paramItems[name])
        })
        return value
    },
    enumerable: true,
    configurable: true
});

Object.defineProperty(PolyTop.MoleculeTop.prototype, "structure", {
    get: function () {
        return this.molecule.structure;
    },
    enumerable: true,
    configurable: true
});

PolyTop.MoleculeTop.prototype.containsAtoms = function (atoms) {
    var self = this;
    atoms.forEach(function (atom) {
        if (!self.atoms.includes(atom)) {
            return false;
        }
    });
    return true;
};
PolyTop.MoleculeTop.prototype.toObject = function () {
    var self = this;
    var obj = {
        atoms: [],
        paramNames: self.paramNames.slice(),
        paramItems: {}
    };
    this.atoms.forEach(function (atom) {
        obj.atoms.push(atom.toObject());
    });
    self.paramNames.forEach(function(name) {
        obj.paramItems[name] = []
        self.paramItems[name].forEach(function (param) {
            obj.paramItems[name].push(param.toObject())
        })
    })
    return obj;
};
PolyTop.MoleculeTop.prototype.fromObject = function (structure, jsonObj) {
    var newObj = new PolyTop.MoleculeTop(structure);
    newObj.addParams(jsonObj);
    return newObj;
};

PolyTop.MoleculeTop.prototype.forParamList = function (callback) {
    var self = this;
    self.paramNames.forEach(function (name) {
        var pList = self.paramItems[name]
        pList.forEach(function (param) {
            callback(pList, param)
        })
    })
}

PolyTop.MoleculeTop.prototype.copy = function () {
    return this.fromObject(this.structure, this.toObject());
};

PolyTop.MoleculeTop.prototype.deleteAtoms = function (atomList) {
    var self = this;
    atomList.forEach(function (atom) {
        self.atoms.splice(atom.index, 1);
        self.residues[atom.residue.index].removeAtom(atom)
        self.chargeGroups[atom.chargeGroupSeq-1].removeAtom(atom)
    });

    self.forParamList( function (pList, param) {
        if (param.anyInAtomList(atomList)) {
            pList.splice(pList.indexOf(param), 1)
        }
    })

    
};
PolyTop.MoleculeTop.prototype.replaceAtom = function (underAtom, overAtom, underAtomList) {
    this.forParamList(function (pList, param) {
        if (!param.allInAtomList(underAtomList)) {
                param.replaceAtom(underAtom, overAtom);
        }
    })
};
PolyTop.MoleculeTop.prototype.replaceAtoms = function (underAtoms, overAtoms, underAtomList) {
    var self = this;
    for (var i = 0; i < underAtoms.length; i++) {
        self.replaceAtom(underAtoms[i], overAtoms[i], underAtomList);
    }
};
PolyTop.MoleculeTop.prototype.removeEmpty = function () {
    var self = this;
    // Remove residues without atoms
    for (var i = self.residues.length; i > 0; i --) {
        if (!self.residues[i-1].atoms.length) {
            self.residues.splice(i-1, 1)
        }
    }

    // Remove charge groups without atoms
    for (var i = self.chargeGroups.length; i > 0; i --) {
        if (!self.chargeGroups[i-1].atoms.length) {
            self.chargeGroups.splice(i-1, 1)
        }
    }
}


PolyTop.ResidueTop = function (molecule, name) {
    if (!name) {
        name = molecule.molecule.name
    }
    this.name = name.slice(0, 4)
    this.molecule = molecule;
    this.atoms = [];
    return this;
}


PolyTop.ResidueTop.prototype.updateStructureResidue = function () {
    this.structureResidue = this.proxy.toObject()
}

PolyTop.ResidueTop.prototype.removeAtom = function (atom) {
    var idx = this.atoms.indexOf(atom)
    this.atoms.splice(idx, 1)
}

PolyTop.ResidueTop.prototype.renameAtomsUnique = function () {
    var self = this;
    var named = []
    self.atoms.forEach(function (atom) {
        if (named.includes(atom.name)) {
            var i = 1;
            while (named.includes(atom.name)) {
                atom.name = atom.element + (atom.index+i).toString()
                i++
            }
        }
        named.push(atom.name)
    })
}

PolyTop.ResidueTop.prototype.getLabel = function () {
    return this.resSeq + ' ' + this.name
}

Object.defineProperty(PolyTop.ResidueTop.prototype, "index", {
    get: function () {
        return this.molecule.residues.indexOf(this);
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.ResidueTop.prototype, "structure", {
    get: function () {
        return this.molecule.structure;
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.ResidueTop.prototype, "proxy", {
    get: function () {
        return this.molecule.structure.getResidueProxy(this.index);
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.ResidueTop.prototype, "resSeq", {
    get: function () {
        return this.index + 1;
    },
    enumerable: true,
    configurable: true
});




PolyTop.ChargeGroup = function (molecule) {
      this.molecule = molecule;
      this.atoms = [];
  }
Object.defineProperty(PolyTop.ChargeGroup.prototype, "index", {
    get: function () {
        return this.molecule.chargeGroups.indexOf(this);
    },
    enumerable: true,
    configurable: true
});

PolyTop.ChargeGroup.prototype.removeAtom = function (atom) {
    var idx = this.atoms.indexOf(atom)
    this.atoms.splice(idx, 1)
}


PolyTop.ParamTop = function (molecule, paramObject) {
    var self = this;
    this.molecule = molecule;
    this.atoms = [];
    this.keys = paramObject.keys.slice();
    this.items = paramObject.items;
    paramObject.atomIndices.forEach(function (index) {
        self.atoms.push(molecule.atoms[index]);
    });
}
PolyTop.ParamTop.prototype.toObject = function () {
    var self = this;
    var newItems = {};
    self.keys.forEach(function (key) {
        newItems[key] = self.items[key];
    });
    return {
        atomSerials: self.atomSerials,
        atomIndices: self.atomIndices,
        keys: self.keys.slice(),
        items: newItems,
    };
};
PolyTop.ParamTop.prototype.fromObject = function (molecule, jsonObj) {
    return new PolyTop.ParamTop(molecule, jsonObj);
};
Object.defineProperty(PolyTop.ParamTop.prototype, "atomSerials", {
    get: function () {
        var serials = [];
        this.atoms.forEach(function (atom) {
            serials.push(atom.serial);
        });
        return serials;
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.ParamTop.prototype, "atomIndices", {
    get: function () {
        var indices = [];
        this.atoms.forEach(function (atom) {
            indices.push(atom.index);
        });
        return indices;
    },
    enumerable: true,
    configurable: true
});
PolyTop.ParamTop.prototype.replaceAtom = function (under, over) {
    var self = this;
    if (self.atoms.includes(under)) {
        var index = self.atoms.indexOf(under);
        self.atoms[index] = over;
    }
};
PolyTop.ParamTop.prototype.allInAtomList = function (atomList) {
    for (var i = 0; i < this.atoms.length; i++) {
        var atom = this.atoms[i]
        if (!atomList.includes(atom)) {
            return false;
        }
    }
    return true;
};
PolyTop.ParamTop.prototype.anyInAtomList = function (atomList) {
    this.atoms.forEach(function (atom) {
        if (atomList.includes(atom)) {
            return true;
        }
    });
    return false;
};


PolyTop.AtomTop = function (molecule, residue, chargeGroup, fields) {
    this.molecule = molecule;
    this.residue = residue;
    this.chargeGroup = chargeGroup;
    this.keys = fields.keys;
    this.name = fields.items.name
    this.atomType = fields.items.atomType;
    this.charge = fields.items.charge;
    this.mass = fields.items.mass;
    this.structureAtom = undefined;
}
PolyTop.AtomTop.prototype.updateStructureAtom = function () {
    this.structureAtom = this.proxy.toObject();
};


Object.defineProperty(PolyTop.AtomTop.prototype, "proxy", {
    get: function () {
        return this.structure.getAtomProxy(this.index);
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.AtomTop.prototype, "element", {
    get: function () {
        return this.structureAtom.element;
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.AtomTop.prototype, "structure", {
    get: function () {
        return this.molecule.structure;
    },
    enumerable: true,
    configurable: true
});
// Object.defineProperty(PolyTop.AtomTop.prototype, "name", {
//     get: function () {
//         return this.element + this.serial.toString();
//     },
//     enumerable: true,
//     configurable: true
// });
Object.defineProperty(PolyTop.AtomTop.prototype, "index", {
    get: function () {
        return this.molecule.atoms.indexOf(this);
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.AtomTop.prototype, "serial", {
    get: function () {
        return this.index + 1;
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.AtomTop.prototype, "resName", {
    get: function () {
        return this.residue.name;
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.AtomTop.prototype, "resSeq", {
    get: function () {
        return this.residue.index + 1;
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.AtomTop.prototype, "chargeGroupSeq", {
    get: function () {
        return this.chargeGroup.index + 1;
    },
    enumerable: true,
    configurable: true
});

PolyTop.AtomTop.prototype.getAtomTypeId = function () {
    return this.proxy.atomStore.atomTypeId[this.index]
}

PolyTop.AtomTop.prototype.toObject = function () {
    var self = this;
    return {
        serial: self.serial,
        index: self.index,
        atomType: self.atomType,
        resSeq: self.resSeq,
        resName: self.resName,
        name: self.name,
        chargeGroupSeq: self.chargeGroupSeq,
        charge: self.charge,
        mass: self.mass,
        label: '[' + self.resName + ']' + self.resSeq + ':' + self.serial + '.' + self.name,
    };
};
PolyTop.AtomTop.prototype.fromObject = function (molecule, residue, chargeGroup, jsonObj) {
    return new PolyTop.AtomTop(molecule, residue, chargeGroup, jsonObj);
};

PolyTop.AtomTop.prototype.pushCoordinates = function (coordList) {
    this.updateStructureAtom()
    coordList.push(this.structureAtom.x);
    coordList.push(this.structureAtom.y)
    coordList.push(this.structureAtom.z)
}

PolyTop.AtomTop.prototype.setResidue = function (residueTop) {
    var self = this;
    if (self.residue) {
        self.residue.atoms.splice(self.residue.atoms.indexOf(self), 1)
        self.residue.molecule.removeEmpty()
    }
    self.residue = residueTop;
    if (!self.residue.atoms.includes(self)) {
        self.residue.atoms.push(self)
    }

    if (!self.molecule.chargeGroups.includes(self.chargeGroup)) {
        self.chargeGroup.removeAtom(self)
        var newCG = new PolyTop.ChargeGroup(self.molecule)
        self.chargeGroup = newCG
        newCG.atoms.push(self)
    }

    self.residue.molecule.orderByResidue()
    self.residue.renameAtomsUnique()
}