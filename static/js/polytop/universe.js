
function padZero (value, nChar) {
    var s = value.toString()
    while (s.length < nChar) {s = '0' + s}
    return s
}

PolyTop.Universe = function (stage) {
    this.molecules = {}
    this.stage = stage;
    this.molCounter = 1;
    return this
}

PolyTop.Universe.prototype.clear = function () {
    var self = this;
    this.molecules = {}
    this.molCounter = 1;
}


PolyTop.Universe.prototype.toObject = function () {
    var self = this;
    var obj = {molecules: {}, molCounter: this.molCounter}
    for (var name in self.molecules) {
        obj.molecules[name] = self.molecules[name].toObject()
    }
    return obj
}

PolyTop.Universe.prototype.toString = function () {
    var obj = this.toObject()
    return JSON.stringify(obj)
}

PolyTop.Universe.prototype.addFromObject = function (obj) {
    var self = this;
    if (obj.molecules !== undefined) {
        var promises = []
        for (var name in obj.molecules) {
            promises.push(self.addMoleculeFromObject(obj.molecules[name]))
        }
        return Promise.all(promises)
    }
}

PolyTop.Universe.prototype.addFromFile = function (file) {
    var self = this;
    return new Promise(function (resolve, reject) {
        var reader = new FileReader();
        reader.onload = function (e) {
            var obj = JSON.parse(e.target.result)
            resolve(self.addFromObject(obj))
        }

        reader.onerror = function (e) {
            reject(e);
        }

        reader.readAsText(file)
    })
    
}

PolyTop.Universe.prototype.addMoleculeFromObject = function (obj) {
    var self = this;
    return PolyTop.StructureTopFromObject(self.stage, obj).then(
        function (mol) {
            self.molecules[mol.name] = mol
            return mol
        }
    )
    
}


PolyTop.Universe.prototype.getNextPolymerName = function () {
    return 'polymer' + padZero(this.molCounter, 3)
}

PolyTop.Universe.prototype.molFromIndex = function (index) {
    var name = this.moleculeNames[index];
    return this.moleculeItems[name];
};
PolyTop.Universe.prototype.loadCoordinates = function (path, name) {
    var self = this;
    if (!name) {
        name = this.getNextPolymerName()
    }
    var newObj = new PolyTop.StructureTop(this.stage, this);
    return newObj.loadCoordinates(path, name)
        .then(function (mol) {
            self.molecules[newObj.name] = newObj;
            
            return newObj
        })
    
};

PolyTop.Universe.prototype.createNewMolecule = function (name) {
    var self = this;
    if (!name) {
        name = self.getNextPolymerName()
    }
    var newObj = new PolyTop.StructureTop(this.stage, name);
    this.molecules[name] = newObj;
    self.molCounter = self.molCounter + 1;
    return newObj
}

PolyTop.Universe.prototype.addMolecule = function (mol) {
    var self = this;
    return new Promise (function (resolve) {
        self.molecules[mol.name] = mol;
        resolve(mol);
    })
}

PolyTop.Universe.prototype.loadTopology = function (file, molecule) {
    if (molecule) {
        return molecule.loadITP(file)
    }
};
Object.defineProperty(PolyTop.Universe.prototype, "polymerNames", {
    get: function () {
        var polymers = this.moleculeNames.slice();
        polymers.push('Add new polymer');
        return polymers;
    },
    enumerable: true,
    configurable: true
});
PolyTop.Universe.prototype.renameMolecule = function (oldName, newName) {
    var self = this;
    if (self.molecules[oldName]) {
        self.molecules[newName] = self.molecules[oldName]
        self.molecules[newName].name = newName
        delete self.molecules[oldName]
    }
};

PolyTop.Universe.prototype.duplicateMolecule = function (mol) {
    var self = this;
    if (mol) {
        var name = mol.name + '_copy'
        return mol.copy().then(function (molCopy) {
            molCopy.name = name
            self.molecules[name] = molCopy;
            return molCopy
        })
    }
    
}