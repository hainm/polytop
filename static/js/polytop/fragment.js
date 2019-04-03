PolyTop.Fragment = function (structureTop, name, color, atomIndices) {
    if (color === void 0) { color = '#ffffff'; }
    if (atomIndices === void 0) {atomIndices = []}
    this.structureTop = structureTop;
    this.color = color;
    this.name = name;
    this.ctr = undefined;
    this.atomProxies = [];
    atomIndices.forEach(function (index) {
        this.atomProxies.push(structureTop.atoms[index])
    })
}

PolyTop.Fragment.prototype.toObject = function () {
    return {
        color: this.color,
        name: this.name,
        atomSerials: this.atomSerials,
        atomIndices: this.atomIndices
    };
};
PolyTop.Fragment.prototype.fromObject = function (structureTop, jsonObj) {
    var newObj = new PolyTop.Fragment(structureTop, jsonObj.name, jsonObj.color, jsonObj.atomIndices.slice());
    return newObj;
};
PolyTop.Fragment.prototype.addAtomIndex = function (index) {
    this.atomProxies.push(this.structureTop.atoms[index])
};

PolyTop.Fragment.prototype.setAtomIndices = function (indexList) {
    var self = this;
    self.atomProxies = []
    if (indexList) {
        indexList.forEach(function(index) {
            self.addAtomIndex(index)
        })
    }
    
}


PolyTop.Fragment.prototype.getSeleString = function () {
    if (this.atomIndices.length) {
        return '@' + this.atomIndices.toString()
    } else {
        return 'none'
    }
    
}

PolyTop.Fragment.prototype.rename = function (name) {
    var self = this;
    this.dispose()
    self.name = name
    if (self.ctr !== undefined) { // if previously in molecule
        self.structureTop._addFragment(self)
    }
    
}

PolyTop.Fragment.prototype.dispose = function () {
    var self = this;
    if (self.ctr !== undefined) {
        delete self.structureTop.fragments[self.label]
    }
    
}

PolyTop.Fragment.prototype.getAtomProxies = function () {
    var self = this;
    let proxies = [];
    this.atomIndices.forEach(function (index) {
        proxies.push(self.structureTop.atoms[index])
    })
    self.atomProxies = proxies
}

PolyTop.Fragment.prototype.getPositionVectors = function () {
    var self = this;
    let vectors = [];
    this.atomIndices.forEach(function (index) {
        vectors.push(self.structure.getAtomProxy(index).positionToVector3())
    })
    return vectors
}


PolyTop.Fragment.prototype.getAtomText = function () {
    var self = this
    var text = []
    this.atomIndices.forEach(function (index) {
        var label = self.structure.getAtomProxy(index).qualifiedName()
        // var label = '[' + atom.resName + ']' + atom.resSeq.toString() + ':' + atom.index.toString() + '.' + atom.label
        text.push(label)
    })
    return text.join(',\n')
}

Object.defineProperty(PolyTop.Fragment.prototype, "label", {
    get: function () {
        return this.labelWithoutCounter() + this.ctr
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.Fragment.prototype, "structure", {
    get: function () {
        return this.structureTop.structure
    },
    enumerable: true,
    configurable: true
});

PolyTop.Fragment.prototype.notNegative = function () {
    var indices = this.atomIndices
    for (var i = 0; i < indices.length ; i ++) {
        var index = indices[i]
        if (index < 0) {
            return false
        }
    }
    return true;
}

PolyTop.Fragment.prototype.allInAtomList = function (atomList) {
    for (var i = 0; i < this.atoms.length; i++) {
        var atom = this.atomProxies[i]
        if (!atomList.includes(atom)) {
            return false;
        }
    }
    return true;
};

PolyTop.Fragment.prototype.replaceAtom = function (under, over) {
    var self = this;
    if (self.atomProxies.includes(under)) {
        var index = self.atomProxies.indexOf(under);
        self.atomProxies[index] = over;
    }
};

PolyTop.Fragment.prototype.replaceAtoms = function (underAtoms, overAtoms, underAtomList) {
    var self = this;
    if (!self.allInAtomList(underAtomList)) {
        for (var i = 0; i < underAtoms.length; i++) {
            self.replaceAtom(underAtoms[i], overAtoms[i]);
        }
    } 
    
};

PolyTop.Fragment.prototype.labelWithoutCounter = function () {
    var name;
    var self = this;
    if (self.atomProxies.length > 0) {
        var prefix = '[';
        var first = self.atomProxies[0];
        prefix = prefix + first.resName + ']';
        prefix = prefix + first.resSeq + ':';
        name = prefix + self.name;
    }
    else {
        name = self.name;
    }
    return name;
}
Object.defineProperty(PolyTop.Fragment.prototype, "atoms", {
    get: function () {
        var self = this;
        var atoms = [];
        this.atomIndices.forEach(function (index) {
            atoms.push(self.structureTop.atoms[index]);
        });
        return atoms;
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.Fragment.prototype, "atomSerials", {
    get: function () {
        var self = this;
        var serials = [];
        this.atomProxies.forEach(function (proxy) {
            serials.push(proxy.serial);
        });
        return serials;
    },
    enumerable: true,
    configurable: true
})

Object.defineProperty(PolyTop.Fragment.prototype, "atomIndices", {
    get: function () {
        var self = this;
        var serials = [];
        this.atomProxies.forEach(function (proxy) {
            serials.push(proxy.index);
        });
        return serials;
    },
    enumerable: true,
    configurable: true
})