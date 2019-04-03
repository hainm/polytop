var reField = /\[ (.+) \]/;
var reWhitespace = /\s+/;
var paramTypes = {
    // atoms
    serial: parseInt,
    atomType: String,
    resSeq: parseInt,
    resName: String,
    name: String,
    chargeGroupSeq: parseInt,
    charge: parseFloat,
    mass: parseFloat,
    // bonded interactions
    keq: parseFloat,
    fc: parseFloat,
    D: parseFloat,
    beta: parseFloat,
    C23: parseFloat,
    table_number: parseInt,
    k: parseFloat,
    low: parseFloat,
    up1: parseFloat,
    up2: parseFloat,
    kdr: parseFloat,
    phase: parseFloat,
    mult: parseInt,
    C0: parseFloat,
    C1: parseFloat,
    C2: parseFloat,
    C3: parseFloat,
    C4: parseFloat,
    C5: parseFloat
};
var atomParams = {
    nAtoms: 0,
    keys: ['serial', 'atomType', 'resSeq', 'resName', 'name', 'chargeGroupSeq', 'charge', 'mass'],
};
var bondParams = {
    nAtoms: 2,
    funct: {
        1: ['keq', 'fc'],
        2: ['keq', 'fc'],
        3: ['keq', 'D', 'beta'],
        4: ['keq', 'C23'],
        5: [],
        6: ['keq', 'fc'],
        7: ['keq', 'fc'],
        8: ['table_number', 'k'],
        9: ['table_number', 'k'],
        10: ['low', 'up1', 'up2', 'kdr']
    }
};

var pairParams = {
    nAtoms: 2,
    funct: {
        1: [],
    }
}

var exclusionParams = {
    nAtoms: 2,
    funct: {
        1: [],
    }
}

var angleParams = {
    nAtoms: 3,
    funct: {
        1: ['angle', 'fc'],
        2: ['angle', 'fc']
    }
};
var dihedralParams = {
    nAtoms: 4,
    funct: {
        1: ['phase', 'fc', 'mult'],
        2: ['keq', 'fc'],
        3: ['C0', 'C1', 'C2', 'C3', 'C4', 'C5'],
        4: ['phase', 'fc', 'mult'],
        9: ['phase', 'fc', 'mult'],
    }
};
var itpParams = {
    atoms: atomParams,
    bonds: bondParams,
    pairs: pairParams,
    angles: angleParams,
    dihedrals: dihedralParams,
    
    exclusions: exclusionParams,
};
function parseLineSplit(lineSplit, params) {
    var fields = {
        atomSerials: [],
        keys: [],
        items: {}
    };
    if (params.nAtoms === 0) {
        fields.keys = params.keys.slice();
    }
    else {
        var funct = parseInt(lineSplit[params.nAtoms]);
        var keys = params.funct[funct].slice();
        keys.unshift('funct');
        fields.keys = keys;
        for (var i = 0; i < params.nAtoms; i++) {
            fields.atomSerials.push(parseInt(lineSplit[i]));
        }
    }
    for (var i = 0; i < fields.keys.length; i++) {
        var keyName = fields.keys[i];
        var keyType = paramTypes[keyName];
        if (keyType === undefined) {
            keyType = parseFloat
        }
        fields.items[keyName] = keyType(lineSplit[i + params.nAtoms]);
    }
    return fields;
}
function isDefined(varName) {
    if (typeof varName === 'undefined') {
        return false;
    }
    else {
        return true;
    }
}

var StructureParser = NGL.ParserRegistry.get('top')

PolyTop.ItpParser = function (streamer, params) {
    StructureParser.call(this, streamer, params)
}

PolyTop.ItpParser.prototype = Object.create(StructureParser.prototype)

// PolyTop.ItpParser.prototype.constructor = PolyTop.ItpParser;

Object.defineProperty(PolyTop.ItpParser.prototype, "type", {
    get: function () { return 'itp'; },
    enumerable: true,
    configurable: true
});
PolyTop.ItpParser.prototype._parse = function () {
    var currentMolecule;
    var params;
    function _parseChunkOfLines(_i, _n, lines) {
        for (var i = _i; i < _n; ++i) {
            var line = lines[i];
            var lt = line.trim();
            if (!lt || lt[0] === '*' || lt[0] === ';') {
                continue;
            }
            if (lt.startsWith('#include')) {
                throw new Error('TopParser: #include statements not allowed');
            }
            var fieldMatch = line.match(reField);
            if (fieldMatch !== null) {
                var name = fieldMatch[1];
                if (name === 'moleculetype') {
                    currentMolecule = {
                        nrexcl: 3,
                        name: 'UNK',
                        atoms: [],
                        paramNames: [],
                        paramItems: {}
                    };
                }
                else if (itpParams.hasOwnProperty(name)) {
                    params = itpParams[name];
                }
                else {
                    params = undefined;
                }
                continue;
            }
            // trim comments from line
            var cIdx = lt.indexOf(';');
            if (cIdx !== -1) {
                lt = lt.substring(0, cIdx).trim();
            }
            var ls = lt.split(reWhitespace);
            if (name === 'moleculetype') {
                // ; Name   nrexcl
                currentMolecule.name = ls[0];
                currentMolecule.nrexcl = parseInt(ls[1]);
            }
            else if (name === 'atoms') {
                currentMolecule.atoms.push(parseLineSplit(ls, params))
            }
            else if (isDefined(params)) {
                if (!currentMolecule.paramNames.includes(name)) {
                    currentMolecule.paramNames.push(name)
                    currentMolecule.paramItems[name] = []
                }
                currentMolecule.paramItems[name].push(parseLineSplit(ls, params));
            }
        }
    }
    this.streamer.eachChunkOfLines(function (lines /*, chunkNo, chunkCount */) {
        _parseChunkOfLines(0, lines.length, lines);
    });
    var atomIdx = 0;
    var atom;
    var serials = {};
    var serialList = [];
    currentMolecule.atoms.forEach(function (atom) {
        serialList.push(atom.items.serial);
        serials[atom.items.serial] = atomIdx;
        ++atomIdx;
    });
    function maybeAddToList(param, destination) {
        param.atomIndices = [];
        param.atomSerials.forEach(function (serial) {
            if (serialList.includes(serial)) {
                param.atomIndices.push(serials[serial]);
            }
            else {
                return;
            }
        });
        destination.push(param);
    }
    
    var _paramItems = {};
    currentMolecule.paramNames.forEach(function (name) {
        var items = currentMolecule.paramItems[name]
        _paramItems[name] = []
        items.forEach(function (param) {
            maybeAddToList(param, _paramItems[name])
        })
    })


    currentMolecule.paramItems = _paramItems;
    this.structure = currentMolecule;
};

NGL.ParserRegistry.add('itp', PolyTop.ItpParser)