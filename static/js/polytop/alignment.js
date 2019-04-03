PolyTop.Alignment = function (reference, target) {
    var self = this;
    return target.copy().then(
        function (targetCopy) {
            var comp;
            self.comp = comp
            self.reference = reference;
            self.target = targetCopy;
            self.init()
            return self;
        }
    )
}

PolyTop.Alignment.prototype.init = function () {
    this.refAtoms = [];
    this.tgAtoms = [];
    this.underAtoms = [];
    this.overAtoms = [];
    this.toDeleteAtoms = [];
    this.fragments = [];
};

PolyTop.Alignment.prototype.mapUnitSelect = function (unitList) {

    // Take a list of {refFragname, tgFragName, over}
    // and separate into atom lists based on 
    // min (refFrag.nAtoms, tgFrag.nAtoms)
    // and delete the remaining atoms

    var self = this;
    self.init();
    unitList.forEach(function (unitFields) {
        if (unitFields.refFragName) {
            var rfFrag = self.reference.fragments[unitFields.refFragName]
            var rfAtoms = rfFrag.atoms;
            var tgFrag = self.target.fragments[unitFields.tgFragName]
            var tgAtoms = tgFrag.atoms;
            self.fragments.push(rfFrag)
            self.fragments.push(tgFrag)
            var nAtoms = Math.min(rfAtoms.length, tgAtoms.length);
            self.refAtoms = self.refAtoms.concat(rfAtoms.slice(0, nAtoms));
            self.tgAtoms = self.tgAtoms.concat(tgAtoms.slice(0, nAtoms));
            if (unitFields.over == 0) {
                self.overAtoms = self.overAtoms.concat(rfAtoms.slice(0, nAtoms));
                self.underAtoms = self.underAtoms.concat(tgAtoms.slice(0, nAtoms));
                self.toDeleteAtoms = self.toDeleteAtoms.concat(tgAtoms.slice());
                self.toDeleteAtoms = self.toDeleteAtoms.concat(rfAtoms.slice(nAtoms,));
            }
            else {
                self.overAtoms = self.overAtoms.concat(tgAtoms.slice(0, nAtoms));
                self.underAtoms = self.underAtoms.concat(rfAtoms.slice(0, nAtoms));
                self.toDeleteAtoms = self.toDeleteAtoms.concat(rfAtoms.slice());
                self.toDeleteAtoms = self.toDeleteAtoms.concat(tgAtoms.slice(nAtoms,));
            }
        }
    });
    return self;
};

PolyTop.Alignment.prototype.removeTransparent = function () {
    // remove transparent drawings on stage
    var self = this;
    if (self.comp) {
        self.reference.stage.removeComponent(self.comp);
        self.comp = undefined;
    }
}

PolyTop.Alignment.prototype.drawTransparent = function () {
    var self = this;
    self.removeTransparent()
    if (self.refAtoms.length > 0) {
        var pdbStr = self.target.toPDB()
        var pdbBlob = new Blob([pdbStr], {type: 'text/plain'})
        self.reference.stage.loadFile(pdbBlob, {ext: 'pdb'}).then(
            function (comp) {
                self.comp = comp
                comp.addRepresentation('ball+stick', {
                    opacity: 0.5,
                    bondScale: 1.4,
                    radiusScale: 1.4,
                }).setName('alignment')
            }
        )
    }
}

PolyTop.Alignment.prototype.superposeTarget = function () {
    // align the target molecule to the reference molecule 
    // using the sorted fragment atoms
    var self = this;
    if (self.refAtoms.length > 0) {
        self.target.superposeOnto(self.reference, self.tgAtomIndices, self.refAtomIndices);
    }
};


PolyTop.Alignment.prototype.finishTransition = function () {
    // The target molecule is already aligned but invisible.
    // Add target molecule atoms to reference molecule;
    // delete extra atoms;
    // remove bonds/angles/dihedrals that have had atoms deleted;
    // update NGL.Structure
    // Finally, add fragments from the target molecule.
    this.removeTransparent()
    this.reference.topology.addOther(this.target.topology);
    this.reference.replaceAtoms(this.underAtoms, this.overAtoms, this.toDeleteAtoms)
    this.reference.deleteAtoms(this.toDeleteAtoms);
    this.reference.getTotalCharge();
    this.reference.addFragmentsFromOther(this.target)
};
Object.defineProperty(PolyTop.Alignment.prototype, "refSele", {
    get: function () {
        return '@' + this.refAtomIndices.toString();
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.Alignment.prototype, "tgSele", {
    get: function () {
        return '@' + this.tgAtomIndices.toString();
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.Alignment.prototype, "refAtomIndices", {
    get: function () {
        var indices = [];
        this.refAtoms.forEach(function (atom) {
            indices.push(atom.index);
        });
        return indices;
    },
    enumerable: true,
    configurable: true
});
Object.defineProperty(PolyTop.Alignment.prototype, "tgAtomIndices", {
    get: function () {
        var indices = [];
        this.tgAtoms.forEach(function (atom) {
            indices.push(atom.index);
        });
        return indices;
    },
    enumerable: true,
    configurable: true
});