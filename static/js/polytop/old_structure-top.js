/**
 * @fileoverview The StructureTop class. 
 * Depends on topology-item.js and ngl.js
 * 
 * @author Lily Wang <lily.wang@anu.edu.au>
 */

const DEFAULT_FRAGMENT_NAME = 'fragment'

 /**
  * Constructor for StructureTop class from JSON.
  * @param {NGL.Stage} stage The stage this molecule is drawn on.
  * @param {Object} jsonObj The JSON object to parse
  * @return {PolyTop.StructureTop} 
  */
PolyTop.StructureTopFromObject = function (stage, jsonObj) {
    var newObj = new PolyTop.StructureTop(stage, jsonObj.name);
    var pdbBlob = new Blob([jsonObj.pdbString], {type: 'text/plain'})
    var itpBlob = new Blob([jsonObj.itpString], {type: 'text/plain'})
    return newObj.loadCoordinates(pdbBlob, jsonObj.name)
        .then(function () {
            return newObj.loadITP(itpBlob).then(function () {
                newObj.addFragments(jsonObj.fragments);
                return newObj;
            })
        })
};


 /**
  * Represents a 'molecule', combining the NGL.Structure (coordinates)
  * and PolyTop.MoleculeTop (topology).
  * @param {NGL.Stage} stage The stage this molecule is drawn on.
  * @param {string} name Name of the molecule
  * @return {PolyTop.StructureTop} 
  */

class StructureTop {

    constructor(stage, name) {
        if (name === void 0) { name = 'UNK'; }
        this.stage = stage;
        this.name = name;
        this.structure = new NGL.Structure();
        var component
        this.component = component
        this.topology = new PolyTop.MoleculeTop(this);
        this.fragments = {}
        this._fragmentNameCounter = {}
        this.newFragment();
        this.totalCharge = 0;
        this.alignments = []
        return this;
    }
    
}

PolyTop.StructureTop = function (stage, name) {
    if (name === void 0) { name = 'UNK'; }
    this.stage = stage;
    this.name = name;
    this.structure = new NGL.Structure();
    var component
    this.component = component
    this.topology = new PolyTop.MoleculeTop(this);
    this.fragments = {}
    this._fragmentNameCounter = {}
    this.newFragment();
    this.totalCharge = 0;
    this.alignments = []
    return this;
}

PolyTop.StructureTop.prototype.toMonomer = function (name) {
    if (!name) {
        name = this.name + ' monomer'
    }
    this.copy(this.stage).then(function (molCopy) {
        molCopy.name = name
        molCopy.topology.toMonomer(name)
    })
    return molCopy
}


PolyTop.StructureTop.prototype.removeAlignments = function () {
    var self = this;
    self.alignments.forEach(function (alignment) {
        self.stage.removeComponent(alignment.comp)
    })
    self.alignments = []
}



PolyTop.StructureTop.prototype.finishTransitions = function () {
    var self = this;
    self.alignments.forEach(function (alignment) {
        alignment.finishTransition()
    })
    self.alignments = []
}

PolyTop.StructureTop.prototype.atomsToOptions = function () {
    var self = this;
    var options = [];
    self.topology.atoms.forEach(function (proxy) {
        options.push(proxy.toObject())
    })
    return options;
}

PolyTop.StructureTop.prototype.getTotalCharge = function () {
    var self = this;
    var charge = 0;
    self.topology.atoms.forEach(function (atom) {
        charge = charge + atom.charge
    })
    self.totalCharge = charge
    return charge
}

PolyTop.StructureTop.prototype.toPDB = function () {
    var writer = new NGL.PdbWriter(this.structure)
    var data = writer.getData()
    return data
}

PolyTop.StructureTop.prototype.toITP = function () {
    var writer = new PolyTop.ItpWriter(this)
    var data = writer.getData()
    return data
}

PolyTop.StructureTop.prototype.toObject = function () {
    var self = this;
    var fragments = {}
    for (var label in self.fragments) {
        fragments[label] = self.fragments[label].toObject()
    }
    
    return {
        name: self.name,
        pdbString: self.toPDB(),
        fragments: fragments,
        itpString: self.toITP()
    };
};

PolyTop.StructureTop.prototype.incrementFragmentCounter = function (name) {
    var self = this;
    if (self._fragmentNameCounter[name]) {
        self._fragmentNameCounter[name] += 1
        return ' ' + self._fragmentNameCounter[name].toString()
    } else {
        self._fragmentNameCounter[name] = 1
        return ''
    }
}

PolyTop.StructureTop.prototype.addFragments = function (fragments) {
    var self = this;
    for (var label in fragments) {
        var fragment = fragments[label]
        self.addFragment(fragment.name, fragment.color, fragment.atomIndices)
    }
};

PolyTop.StructureTop.prototype.addFragmentsFromOther = function (other) {
    var self = this;
    // remove own first
    self.forFragment(function (fragment) {
        if (!fragment.notNegative()) {
            fragment.dispose()
        }
    })
    other.forFragment(function (fragment) {
        if (fragment.notNegative()) {
            self.addFragment(fragment.name, fragment.color, fragment.atomIndices)
        }
    })
}



PolyTop.StructureTop.prototype.forFragment = function (callback) {
    var self = this;
    for (var name in self.fragments) {
        callback(self.fragments[name])
    }
}

PolyTop.StructureTop.prototype.replaceAtoms = function (underAtoms, overAtoms, underAtomList) {
    var self = this;
    self.topology.replaceAtoms(underAtoms, overAtoms, underAtomList)
    self.forFragment(function (fragment) {
        fragment.replaceAtoms(underAtoms, overAtoms, underAtomList)
    })
}

PolyTop.StructureTop.prototype.newFragment = function () {
    this.currentFragment = new PolyTop.Fragment(this, DEFAULT_FRAGMENT_NAME, '#f3f3f3')
}

PolyTop.StructureTop.prototype.addFragment = function (name, color, atomIndices) {
    var self = this;
    if (!self.currentFragment) {
        self.newFragment()
    }
    if (name) {
        self.currentFragment.name = name
    }
    
    if (color) {
        self.currentFragment.color = color
    }
    
    if (atomIndices) {
        self.currentFragment.setAtomIndices(atomIndices)
    }

    if (self.currentFragment.atomProxies.length > 0 && self.currentFragment.notNegative()) {
        self._addFragment(self.currentFragment);
    }
    self.newFragment()
};

PolyTop.StructureTop.prototype._addFragment = function (fragment) {
    var self = this;
    fragment.ctr = self.incrementFragmentCounter(fragment.name)
    self.fragments[fragment.label] = fragment
}


PolyTop.StructureTop.prototype.deleteFragmentByLabel = function (label) {
    if (this.fragments[label]) {
        this.fragments[label].dispose()
    }
}



PolyTop.StructureTop.prototype.copy = function (stage) {
    var self = this;
    if (stage === undefined) {stage = self.stage}
    return PolyTop.StructureTopFromObject(stage, this.toObject());
};

PolyTop.StructureTop.prototype.loadCoordinates = function (files, name) {
    var self = this
    if (!name) {
        var name = getFileInfo(path).base;
    }
    self.name = name;

    var onLoadComp = function (comp) {
        self.structure = comp.structure;
        self.component = comp;
        return self
    }

    return self.stage.loadFile(files,  {ext: 'pdb'}).then(onLoadComp)
    // return self;
};

PolyTop.StructureTop.prototype.draw = function () {
    this.component.addRepresentation('ball+stick')
    this.stage.autoView(30)
}

PolyTop.StructureTop.prototype.loadBlob = function (pdbStr) {
    var self = this;
    var pdbBlob = new Blob([pdbStr], {'type': 'text/plain'})
    return self.stage.loadFile(pdbBlob, {'ext': 'pdb'}).then(
        function (comp) {
            self.structure = comp.structure;
            self.component = comp;
            self.draw()
        }
    )
}

PolyTop.StructureTop.prototype.loadITP = function (path) {
    var self = this;
    return NGL.autoLoad(path,  {ext: 'itp'})
        .then(function (parsed) {
            if (parsed.atoms.length > 0) {
                self.topology.addParsedITP(parsed);
                self.updateAtomStore()
                self.updateBondStore()
            }
            return this;
        })
};

PolyTop.StructureTop.prototype.updateBondStore = function () {
    var self = this
    var bondStore = this.structure.bondStore
    bondStore.resize(this.bonds.length);
    for (var i = 0; i < this.bonds.length; i++) {
        var indices = self.bonds[i].atomIndices;
        bondStore.atomIndex1[i] = Math.min.apply(Math, indices);
        bondStore.atomIndex2[i] = Math.max.apply(Math, indices);
    }
    bondStore.count = this.bonds.length;
    this.structure.bondStore = bondStore;
    this.structure.finalizeBonds();
};

PolyTop.StructureTop.prototype.updateAtomStore = function () {
    var self = this;

    var chainname = this.structure.chainStore.getChainname(0)
    var chainid = this.structure.chainStore.getChainid(0)

    var structure = new NGL.Structure()
    var atomStore = structure.atomStore
    var atomMap = structure.atomMap
    var residueMap = structure.residueMap
    var residueStore = structure.residueStore
    this.structure = structure
    
    atomStore.resize(self.atoms.length);
    residueStore.resize(self.residues.length);
    

    var atomIdx = 0;
    for (var i = 0; i < self.residues.length; i++) {
        
        var res = self.residues[i]
        var idList = [];
        residueStore.atomOffset[i] = atomIdx;
        res.atoms.forEach(function (atom) {
            var atomId = atomMap.add(atom.name, atom.element);
            atomStore.residueIndex[atomIdx] = atom.residue.index;
            atomStore.atomTypeId[atomIdx] = atomId;
            atomStore.x[atomIdx] = atom.structureAtom.x;
            atomStore.y[atomIdx] = atom.structureAtom.y;
            atomStore.z[atomIdx] = atom.structureAtom.z;
            atomStore.serial[atomIdx] = atom.serial;
            atomStore.bfactor[atomIdx] = atom.structureAtom.bfactor;
            atomStore.altloc[atomIdx] = atom.structureAtom.altloc;
            atomStore.occupancy[atomIdx] = 1;
            idList.push(atomId)
            atomIdx ++;
        })
        var resId = residueMap.add(res.name, idList, true);
        residueStore.chainIndex[i] = 0;
        
        residueStore.atomCount[i] = res.atoms.length;
        residueStore.residueTypeId[i] = resId;
        residueStore.resno[i] = res.resSeq;
        residueStore.sstruc[i] = res.structureResidue.sstruc;
        residueStore.inscode[i] = res.structureResidue.inscode;
    }

    atomStore.count = self.atoms.length;
    
    structure.finalizeAtoms();
    residueStore.count = self.residues.length;

    var modelStore = structure.modelStore
    var chainStore = structure.chainStore

    modelStore.growIfFull()
    chainStore.growIfFull()
    chainStore.setChainname(0, chainname)
    chainStore.setChainid(0, chainid)
    modelStore.chainOffset[0] = 0
    modelStore.chainCount[0] = 1
    modelStore.count = 1
    chainStore.modelIndex[0] = 0
    chainStore.residueOffset[0] = 0
    chainStore.residueCount[0] = this.residues.length;
    chainStore.count = 1

    self.residues.forEach(function (res) {
        
        res.atoms.forEach(function (atom) {
            atom.updateStructureAtom()
        })
        res.updateStructureResidue()
    })

};

Object.defineProperty(PolyTop.StructureTop.prototype, "residues", {
    get: function () {
        return this.topology.residues;
    },
    enumerable: true,
    configurable: true
});

Object.defineProperty(PolyTop.StructureTop.prototype, "bonds", {
    get: function () {
        return this.topology.paramItems.bonds || [];
    },
    enumerable: true,
    configurable: true
});

Object.defineProperty(PolyTop.StructureTop.prototype, "fragmentLabels", {
    get: function () {
        var self = this;
        var fragments = {}
        self.forFragment(function (fragment) {
            fragments[fragment.label] = fragment
        })
        return fragments
    },
    enumerable: true,
    configurable: true
});

PolyTop.StructureTop.prototype.deleteAtomsByIndex = function (indices) {
    var self = this;
    var atoms = []
    indices.forEach(function (i) {
        atoms.push(self.atoms[i])
    })
    self.deleteAtoms(atoms)
}

PolyTop.StructureTop.prototype.atomsByIndex = function (indices) {
    var self = this;
    var atoms = [];
    indices.forEach(function (i) {
        if (self.topology.atoms[i]) {
            atoms.push(self.topology.atoms[i])
        } else {
            console.log('Warning: no atom found at index ', i, 'in molecule ', self.name)
        }
    })
    return atoms
}

PolyTop.StructureTop.prototype.moveAtomsToResidueIndex = function (atomList, i) {
    var res = this.topology.residues[i]
    if (res) {
        atomList.forEach(function (atom) {
            atom.setResidue(res)
        })
    }
    self.updateNGLAtoms()
}

PolyTop.StructureTop.prototype.deleteAtoms = function (atomList) {
    var self = this;
    var containedAtoms = [];
    atomList.forEach(function (atom) {
        if (self.atoms.includes(atom)) {
            containedAtoms.push(atom)
        }
    })
    self.topology.deleteAtoms(containedAtoms);
    self.topology.removeEmpty();
    self.updateNGLAtoms()
    
};

PolyTop.StructureTop.prototype.updateNGLAtoms = function () {
    this.structure.atomStore.count = this.atoms.length;
    this.structure.finalizeAtoms();
    this.updateAtomStore();
    this.updateBondStore();
}

PolyTop.StructureTop.prototype.superposeOnto = function (other, selfIndices, otherIndices) {
    var self = this;
    // NGL.superpose(self.structure, other.structure, false, selfSele, otherSele)
    var atoms1 = self.getArray(selfIndices) //self.structure.getView((new NGL.Selection(selfSele)))
    var atoms2 = other.getArray(otherIndices) //other.structure.getView(new NGL.Selection(otherSele))
    var superpose = new NGL.Superposition(atoms1, atoms2)
    superpose.transform(self.structure)
    self.structure.refreshPosition()
    self.component.updateRepresentations({position:true})
};

PolyTop.StructureTop.prototype.getArray = function (indices) {
    var self = this;
    var arr = []
    indices.forEach(function (index) {
        self.atoms[index].pushCoordinates(arr)
    })
    return Float32Array.from(arr)


}

PolyTop.StructureTop.prototype.getCoords = function (indices) {
    var self = this;
    var coords = new NGL.Matrix(3, indices.length);
    var coordsT = new NGL.Matrix(indices.length, 3);
    const cd = coords.data;
    var i = 0;
    indices.forEach(function (index) {
        var atom = self.structure.getAtomProxy(index)
        cd[ i + 0 ] = atom.x
        cd[ i + 1 ] = atom.y
        cd[ i + 2 ] = atom.z
        i += 3
    })
    return coords, coordsT
}

Object.defineProperty(PolyTop.StructureTop.prototype, "atoms", {
    get: function () {
        return this.topology.atoms;
    },
    enumerable: true,
    configurable: true
});

PolyTop.StructureTop.prototype.setVisibility = function (value) {
    var self = this;
    this.stage.compList.forEach(function (comp) {
        comp.setVisibility(false)
    })

    return this.loadBlob(self.toPDB()).then(this.autoViewTo())
    
    
};

PolyTop.StructureTop.prototype.autoViewTo = function () {
    if (this.component) {
        this.stage.animationControls.zoomMove(
            this.component.getCenter(),
            this.stage.getZoom(),
            3
        )
    }
    console.log('AUTOVIEWIG')
}