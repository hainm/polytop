var atomLetters = ['i', 'j', 'k', 'l'];
var paramFormats = {
    header: '[ %s ]',
    serial: '%-6d',
    nrexcl: '%-6d',
    resSeq: '%-6d',
    chargeGroupSeq: '%-6d',
    table_number: '%-6d',
    charge: '%-8.4f',
    mass: '%-8.4f',
    funct: '%-4d',
    float: '%-.7e',
    string: '%-8s',
    mult: '%-6d',
    phase: '%-6.2f',
    angle: '%-6.2f'
};
function formatParam(key, item) {
    var currentString = ''
    if (paramFormats.hasOwnProperty(key)) {
        currentString = currentString + sprintf(paramFormats[key], item);
    }
    else {
        if (typeof item === 'number') {
            currentString = currentString + sprintf(paramFormats.float, item);
        }
        else if (typeof item === 'string') {
            currentString = currentString + sprintf(paramFormats.string, item);
        }
    }

    if (typeof item === 'number') {
        if (item >= 0 ) {
            currentString = ' ' + currentString
        }
    }
    return currentString;
}

var safeName = function (text) {
    return text.replace(/[^a-z0-9]/gi, '_')
}

PolyTop.ItpWriter = function (structureTop) {
    NGL.PdbWriter.call(structureTop.structure, {})
    this.mimeType = 'text/plain';
    this.defaultName = 'structure';
    this.defaultExt = 'itp';
    this.structureTop = structureTop;
    this._records = [];
    return this
}

PolyTop.ItpWriter.prototype = Object.create(NGL.PdbWriter.prototype)

PolyTop.ItpWriter.prototype.constructor = PolyTop.ItpWriter

PolyTop.ItpWriter.prototype._writeRecords = function () {
    var self = this;
    this._records.length = 0;
    this._writePreamble();
    this._writeMoleculeType();
    var top = this.structureTop.topology
    this._writeAtoms(top.atoms);
    top.paramNames.forEach(function (name) {
        self._writeSection(name, top.paramItems[name])
    })
};
PolyTop.ItpWriter.prototype._writeMoleculeType = function () {
    this._writeHeader('moleculetype');
    this._records.push('; name        nrexcl');
    var nameStr = formatParam('name', safeName(this.structureTop.name));
    var nrexcl = formatParam('nrexcl', 3);
    this._records.push(nameStr + ' ' + nrexcl);
    this._records.push('')
};
PolyTop.ItpWriter.prototype._writePreamble = function () {
    this._records.push(';');
};
PolyTop.ItpWriter.prototype._writeAtoms = function (atoms) {
    var self = this;
    if (!atoms.length) {
        return;
    }
    
    if (atoms[0].keys) {
        this._writeHeader('atoms');
        this._writeAtomKeys(atoms[0]);
        atoms.forEach(function (atom) {
            self._writeAtom(atom);
    });
    }
    this._records.push('');
};
PolyTop.ItpWriter.prototype._writeAtom = function (entry) {
    var line = '';
    var items = entry.toObject();
    entry.keys.forEach(function (key) {
        line = line + ' ' + formatParam(key, items[key]);
    });
    this._records.push(line);
};
PolyTop.ItpWriter.prototype._writeSection = function (paramKey, paramList) {
    var self = this;
    if (!paramList.length) {
        return;
    }
    this._writeHeader(paramKey);
    this._writeKeys(paramList[0]);
    paramList.forEach(function (param) {
        self._writeParam(param);
    });
    this._records.push('');
};
PolyTop.ItpWriter.prototype._writeHeader = function (header) {
    this._records.push(formatParam('header', header));
};
PolyTop.ItpWriter.prototype._writeAtomKeys = function (entry) {
    var line = '; ';
    line = line + entry.keys.join('  ');
    this._records.push(line);
};
PolyTop.ItpWriter.prototype._writeKeys = function (entry) {
    var line = ';';
    for (var i = 0; i < entry.atomSerials.length; i++) {
        line = line + '  a' + atomLetters[i];
    }
    line = line + ' ' + entry.keys.join('  ');
    this._records.push(line);
};
PolyTop.ItpWriter.prototype._writeParam = function (entry) {
    var line = '';

    for (var i = 0; i < entry.atomSerials.length; i++) {
        var serial = entry.atomSerials[i]
        if (serial <= 0) {
            return;
        } else {
            line = line + formatParam('serial', serial);
        }
    }
    for (var j = 0; j < entry.keys.length ; j++) {
        var key = entry.keys[j];
        line = line + ' ' + formatParam(key, entry.items[key]);
    }
    this._records.push(line);
};
PolyTop.ItpWriter.prototype.getString = function () {
    console.warn('PolyTop.ItpWriter.getString() is deprecated, use .getData instead');
    return this.getData();
};
/**
 * Get string containing the PDB file data
 * @return {String} PDB file
 */
PolyTop.ItpWriter.prototype.getData = function () {
    this._writeRecords();
    return this._records.join('\n');
}
