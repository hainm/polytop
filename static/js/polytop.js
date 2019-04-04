
// Viewport
// handles mouse events for webGL
NGL.ViewportWidget = function (stage) {
  var viewer = stage.viewer

  var container = new UI.Panel()
  container.dom = viewer.container

  var fileTypesOpen = NGL.flatten([
    NGL.ParserRegistry.getStructureExtensions(),
    NGL.ParserRegistry.getVolumeExtensions(),
    NGL.ParserRegistry.getSurfaceExtensions(),
    NGL.DecompressorRegistry.names
  ])

  // event handlers

  container.dom.addEventListener('dragover', function (e) {
    e.stopPropagation()
    e.preventDefault()
    e.dataTransfer.dropEffect = 'copy'
  }, false)

  container.dom.addEventListener('drop', function (e) {
    e.stopPropagation()
    e.preventDefault()

    var fn = function (file, callback) {
      var ext = file.name.split('.').pop().toLowerCase()
      if (NGL.ScriptExtensions.includes(ext)) {
        stage.loadScript(file).then(callback)
      } else if (fileTypesOpen.includes(ext)) {
        stage.loadFile(file, { defaultRepresentation: true }).then(callback)
      } else {
        console.error('unknown filetype: ' + ext)
        callback()
      }
    }
    var queue = new NGL.Queue(fn, e.dataTransfer.files)
  }, false)

  stage.handleResize()
  setTimeout(function () { stage.handleResize() }, 500)

  container.setClass('viewport')
  return container
}

// State widget
// Keeps track of the current state
// of the GUI

PolyTop.GuiBackend = function () {
  
  // INIT

  var self = this;
  self.selectedAtomProxies = []
  self.selectedAtomIndices = []
  self.currentFragment = undefined
  self.currentMolecule = undefined
  self.currentAlignment = undefined;
  self.moleculeCharge = new UI.Number(0).setDisabled(true)
  self.moleculeNAtoms = new UI.Number(0).setDisabled(true)
  self.moleculeNResidues = new UI.Number(0).setDisabled(true)
  self.moleculeNChargeGroups = new UI.Number(0).setDisabled(true)
  self.alignmentPanel = new UI.Panel().setId('alignmentPanel')


  //
  // STAGES
  //

  self.stage = new NGL.Stage()
  self.view = new NGL.ViewportWidget(self.stage)

  self.sideStage = new NGL.Stage()
  var sideView = new NGL.ViewportWidget(self.sideStage)
  self.sideView = new UI.Panel().setId('sideViewport')
  self.sideView.add(sideView)

  // UNIVERSE, STATES, UNDO/REDO

  self.universe = new PolyTop.Universe(self.stage)

  self.states = []
  self.currentStateIndex = -1

  self.undoButton = new UI.IconButton('Undo', 'undo')
    .onClick(function (e) {
      e.preventDefault()
      if (self.currentStateIndex > 0) {
        self.currentStateIndex = self.currentStateIndex - 1
        self.setState()
      }
    })
  self.undoButton.setDisabled(true)

  self.redoButton = new UI.IconButton('Redo', 'redo')
    .onClick(function (e) {
      e.preventDefault()
      if (self.currentStateIndex < self.states.length-1) {
        self.currentStateIndex = self.currentStateIndex + 1
        self.setState()
      }
    })
  self.redoButton.setDisabled(true)

  self.saveState()

  // BUTTONS

  self.universeLoadButton = new UI.File('Load universe', 'cloud-upload-alt').setAccept('.json')
  self.universeLoadButton.onChange(function (files) {
    if (files.length > 0) {
      self.universe.addFromFile(files[0]).then(function (result) {
        self.updateUniverse()
      })
    }
  })

  self.universeSaveButton = new UI.IconButton('Save universe', 'cloud-download-alt')
    .onClick(function () {self.downloadUniverse()})

  self.pdbLoadButton = new UI.File('Load PDB', 'file-upload').setAccept('.pdb')
  self.pdbLoadButton.onChange(function (files) {
    if (files.length > 0) {
      self.loadPDB(files[0])
    }
  })

  self.itpLoadButton = new UI.File('Load ITP', 'file-import').setAccept('.itp')
  self.itpLoadButton.onChange(function (files) {
    if (files.length > 0) {
      self.loadITP(files[0])
    }
  })
  self.itpLoadButton.setDisabled(true)

  // MOLECULE-RELATED INTERFACE

  self.molSelect = new UI.Selectize('molecule')
    .setArguments({
      valueField: 'name',
      labelField: 'name',
      maxItems: 1,
      onChange: function (value) {self.setCurrentMoleculeName(value)},
      create: false
    })
  
  self.molName = new UI.Input()
    .onInput(function () {self.renameMolecule()})
  
  self.unitSelect = new UI.Selectize('unit')
    .setArguments({
        maxItems:1,
        labelField: 'name',
        valueField: 'name',
        sortField: ['name'],
        searchField: ['name'],
        onChange: function (e) {
          self.createAlignment(e)
        }
      }
    )

  self.createMoleculeButton = new UI.Button('Add new polymer')
    .onClick(function () {
      var mol = self.universe.createNewMolecule()
      self.updateUniverse(mol.name)
    })

  self.saveMonomerButton = new UI.Button('Save as monomer')
    .onClick(function () {self.currentMoleculeToMonomer()})
  
  self.downloadFilesButton = new UI.Button('Download files')
    .onClick( function () {self.downloadFiles()} )

  self.duplicateMoleculeButton = new UI.Button('Duplicate polymer')
    .onClick(function () {self.duplicateCurrentMolecule()})
  
  self.addUnitButton = new UI.Button('Add')
    .onClick(function () {
      self.finishAlignment()
    })
  
  self.deleteAtomsButton = new UI.Button('Delete')
    .onClick(function () {
      self.deleteFragmentAtoms()
    })
  
  self.moveToResidueButton = new UI.Button('Move')
    .onClick(function (e) {
      e.preventDefault();
      self.moveToResidue()
    })

  self.moveToResidueSelect = new UI.Selectize()
    .setArguments({
      maxItems: 1,
      valueField: 'index',
      labelField: 'label',
      onChange: function (value) {
        if (value) {
          self.moveToResidueButton.setDisabled(false)
          self.highlightResidueIndex(value)
        } else {
          self.moveToResidueButton.setDisabled(true)
          self.removeHighlighted()
        }
      }
    })
  
  

  self.pdbText = new UI.TextArea()
  self.itpText = new UI.TextArea()


  // FRAGMENTS
  //

  self.addFragment = new UI.Button('Add fragment')
    .onClick(function () {self.addFragmentToMolecule()})

  self.fragmentName = new UI.Input('')
    .onChange(function () {
      var name = self.fragmentName.getValue()
      self.currentMolecule.currentFragment.rename(name)
      self.updateUniverse()
    })

  self.fragmentAtoms = new UI.Selectize('fragment-atoms')
    .setMultiple(true)
    .setArguments({
        plugins: ['drag_drop', 'remove_button'],
        labelField: 'label',
        valueField: 'index',
        sortField: ['serial'],
        searchField: ['serial', 'name'],
        onChange: function (e) {
          self.updateSelectedProxies(e)
        },
      }
    )

  self.fragmentColor = new UI.Color('#ffffff').setId('fragmentColor')
    .onChange(function () {
      if (self.currentFragment) {
        self.currentFragment.color = self.fragmentColor.getValue()
        self.drawFragment(self.currentFragment)
      }
    })

  self.fragmentColorContainer = new UI.Panel().setId('fragmentColorContainer')
    .add(self.fragmentColor, self.addFragment)

  self.deleteFragment = new UI.Button('Delete').onClick(function () {
    if (self.fragmentSelect.getValue()) {
      var name = self.fragmentSelect.getValue()
      self.currentMolecule.deleteFragmentByLabel(name)
      self.setCurrentFragment(self.currentMolecule.currentFragment)
      self.updateUniverse()
    }
  })

  self.fragmentSelect = new UI.Select()
    .setSize(12)
    .onChange( function () {
      var fragName = self.fragmentSelect.getValue()
      if (fragName) {
        var fragment = self.currentMolecule.fragmentLabels[fragName]
        self.setCurrentFragment(fragment)
      } else {
        self.setCurrentFragment(self.currentMolecule.currentFragment)
      }
      
    })

  self.fragmentPanel = new UI.Panel().setId('fragmentSelectPanel')
    .addEntry('Fragments', self.fragmentSelect)
    .addEntry('', self.deleteFragment)
    .onClick(function (e) {
      e.preventDefault()
      self.fragmentSelect.setValue()
    })
  
  // toggle selection
  self.stage.signals.clicked.add( function (pickingProxy) {
    self.togglePick(pickingProxy)
  })


  return this;
}

PolyTop.GuiBackend.prototype.currentMoleculeToMonomer = function () {
  var self = this;
  if (self.currentMolecule) {
    self.currentMolecule.toMonomer()
      .then(function (monomer) {
        self.universe.addMolecule(monomer)
          .then( function (monomer) {
            self.updateUniverse(monomer.name)
          }
        )
      })
    
  }
}

PolyTop.GuiBackend.prototype.duplicateCurrentMolecule = function () {
  var self = this;
  if (self.currentMolecule) {
    self.universe.duplicateMolecule(self.currentMolecule).then(function (molCopy) {
      self.updateUniverse(molCopy.name)
    })
  }
}

PolyTop.GuiBackend.prototype.loadPDB = function (files) {
  var self = this;
  var name = NGL.getFileInfo(self.pdbLoadButton.getValue()).base
  self.universe.loadCoordinates(files, name)
    .then(function (mol) {
      self.updateUniverse(mol.name)
    })
}

PolyTop.GuiBackend.prototype.loadITP = function (files) {
  var self = this;
  this.universe.loadTopology(files, this.currentMolecule)
    .then(function () {self.updateUniverse()})
}

PolyTop.GuiBackend.prototype.setState = function () {

  // set GUI state to self.states[self.currentStateIndex]

  var self = this;
  var obj = self.states[self.currentStateIndex]
  // self.currentMolecule = undefined;
  self.universe.clear()
  self.universe.addFromObject(obj.universe).then(function () {
    self.updateUniverse(obj.currentMoleculeName, true)
  })

  if (self.currentStateIndex < 1) {
    self.undoButton.setDisabled(true)
  } else {
    self.undoButton.setDisabled(false)
  }

  if (self.currentStateIndex >= self.states.length-1) {
    self.redoButton.setDisabled(true)
  } else {
    self.redoButton.setDisabled(false)
  }
}

PolyTop.GuiBackend.prototype.saveState = function () {

  // save current universe state to self.states

  var self = this;
  self.states = self.states.slice(0, self.currentStateIndex+1)

  var molName
  if (self.currentMolecule) {molName = self.currentMolecule.name}
  var universe = self.universe.toObject()
  var obj = {
    universe: universe,
    currentMoleculeName: molName,
  }

  self.states.push(obj)
  self.currentStateIndex += 1
  self.undoButton.setDisabled(false)
  self.redoButton.setDisabled(true)
}

PolyTop.GuiBackend.prototype.updateUniverse = function (molName, silent) {

  // Update GUI with universe molecules and update molecule
  // Save state unless silent

  var self = this;
  
  var molOptions = []
  for (var name in self.universe.molecules) {
    molOptions.push({name: name, value: self.universe.molecules[name]})
  }
  this.molSelect.setOptions(molOptions);
  this.unitSelect.setOptions(molOptions);
  if (molName === undefined) {
    molName = self.currentMolecule.name
  }
  this.setCurrentMoleculeName(molName)
  if (!silent) {
    self.saveState()
  }
  
}

PolyTop.GuiBackend.prototype.downloadUniverse = function () {

  // save universe state to file

  var universe = this.universe.toString()
  this.saveBlob(universe, 'polytop.json')
}


PolyTop.GuiBackend.prototype.saveBlob = function (str, fileName) {

  // Create hidden <a> and click it to download file

  setTimeout( function () {
    var blob = new Blob([str], {type: 'text/plain'})
    var a = document.createElement('a')
    
    a.style = "display: none"
    var url = window.URL.createObjectURL(blob);
    a.href = url
    a.download = fileName
    document.body.appendChild(a)
    a.click();
    window.URL.revokeObjectURL(url)
    a.parentNode.removeChild(a)
  }, 500)
}

PolyTop.GuiBackend.prototype.downloadFiles = function () {
    var self = this;
    var pdbName = self.currentMolecule.name + '.pdb'
    var itpName = self.currentMolecule.name + '.itp'
    self.saveBlob(self.pdbText.getValue(), pdbName)
    self.saveBlob(self.itpText.getValue(), itpName)
  }
  

PolyTop.GuiBackend.prototype.createAlignment = function (molName) {

  // create Alignment Panel and draw the target molecule (name molName)

  var self = this;
  var mol = self.universe.molecules[molName]
  self.alignmentPanel.clear()
  self.sideStage.removeAllComponents()
  if (self.currentMolecule) {
    if (self.currentAlignment) {
      self.currentMolecule.removeAlignments()
    }
    self.currentAlignment = new UI.UnitAlignmentPanel(self.currentMolecule, mol)
    self.currentAlignment.add(self.addUnitButton)
    self.alignmentPanel.add(self.currentAlignment)
  }
  mol.copy(self.sideStage).then(function (molCopy) {molCopy.draw()})
    
}

PolyTop.GuiBackend.prototype.deleteFragmentAtoms = function () {
  var self = this;
  if (self.currentMolecule) {
    
    var atoms = self.selectedAtomProxies
    self.currentMolecule.deleteAtoms(atoms)
  }
  self.updateUniverse()
}

PolyTop.GuiBackend.prototype.moveToResidue = function () {
  var self = this;
  if (self.currentMolecule) {
    var resIndex = self.moveToResidueSelect.getValue()
    if (resIndex >= 0) {
      if (self.currentFragment) {
        self.currentMolecule.moveAtomsToResidueIndex(self.selectedAtomProxies, resIndex)
      }
    }
    self.setCurrentFragment(self.currentMolecule.newFragment())
    self.updateUniverse()
  }
  
}

PolyTop.GuiBackend.prototype.finishAlignment = function () {

  // finish molecule alignment and clear the side viewport

  var self = this;
  if (self.currentMolecule) {
    self.currentMolecule.finishTransitions()
  }
  self.unitSelect.setValue('', true)
  self.sideStage.removeAllComponents()
  self.updateUniverse()
}


PolyTop.GuiBackend.prototype.togglePick = function (pickingProxy) {

  // Pick atoms and toggle transparent highlight

  var self = this;
  if (pickingProxy && (pickingProxy.atom || pickingProxy.bond)) {
    var atom = pickingProxy.atom || pickingProxy.closestBondAtom
    if (!self.selectedAtomIndices) {self.selectedAtomIndices = []}
    if (self.selectedAtomIndices.includes(atom.index)) {
      var index = self.selectedAtomIndices.indexOf(atom.index)
      self.selectedAtomIndices.splice(index, 1)
    } else {
      self.selectedAtomIndices.push(atom.index)
    }
    self.currentFragment.setAtomIndices(self.selectedAtomIndices)
    self.setCurrentFragment(self.currentFragment)
  }
}


PolyTop.GuiBackend.prototype.setCurrentFragment = function (fragment) {
  var self = this;
  self.currentFragment = fragment
  self.selectedAtomProxies = fragment.atomProxies
  self.fragmentName.setValue(fragment.name)
  self.fragmentColor.setValue(fragment.color)
  self.fragmentAtoms.setValue(fragment.atomIndices, true)
  
  if (self.currentFragment) {
    self.drawFragment(self.currentFragment)
  }
  
}

PolyTop.GuiBackend.prototype.updateSelectedProxies = function (value) {

  // update selected fragment proxies

  var self = this;
  if (self.currentFragment) {
    self.selectedAtomIndices = value;
    self.currentFragment.setAtomIndices(value)
    self.setSelectedIndices = value;
    self.drawFragment(self.currentFragment)
  }
}


PolyTop.GuiBackend.prototype.renameMolecule = function () {
  var self = this;
  if (self.currentMolecule) {
    var oldName = self.currentMolecule.name
    var newName = self.molName.getValue()

    if (newName) {
      self.universe.renameMolecule(oldName, newName)
      self.setCurrentMoleculeName(newName)
      self.updateUniverse()
    } 
  }
  
}


PolyTop.GuiBackend.prototype.setSelectedIndices = function (indices) {
  this.selectedAtomIndices = indices
}

PolyTop.GuiBackend.prototype.setCurrentMoleculeName = function (name) {
  var mol = this.universe.molecules[name]
  this.setCurrentMolecule(mol)
}

PolyTop.GuiBackend.prototype.setCurrentMolecule = function (molecule) {
var self = this;
if (molecule) {
  self.currentMolecule = molecule
  self.currentMolecule.setVisibility(true)

  self.itpLoadButton.setDisabled(false)

  self.setCurrentFragment(molecule.newFragment())
  self.fragmentAtoms.setOptions(molecule.atomsToOptions())
  self.fragmentSelect.setOptions(molecule.fragments)

  self.molSelect.setValue(molecule.name, true)
  self.molName.setValue(molecule.name)
  self.moleculeCharge.setValue(molecule.totalCharge)
  self.moleculeNAtoms.setValue(molecule.topology.atoms.length)
  self.moleculeNResidues.setValue(molecule.topology.residues.length)
  self.moleculeNChargeGroups.setValue(molecule.topology.chargeGroups.length)

  var resOptions = []
  self.currentMolecule.topology.residues.forEach(function (res) {
    resOptions.push({'label': res.getLabel(), 'index': res.index})
  })
  self.moveToResidueSelect.setOptions(resOptions)

  self.pdbText.setValue(self.currentMolecule.toPDB())
  self.itpText.setValue(self.currentMolecule.toITP())

  self.alignmentPanel.clear()
  self.unitSelect.setValue()
  self.sideStage.removeAllComponents()
  
} else {
  if (self.currentMolecule) {
    self.currentMolecule.setVisibility(false)
  } 
  self.currentMolecule = undefined

  self.itpLoadButton.setDisabled(true)

  self.fragmentSelect.setOptions([])
  self.fragmentName.setValue('')

  self.molSelect.setValue('', true)
  self.molName.setValue('')
  self.moleculeCharge.setValue(0)
  self.moleculeNAtoms.setValue(0)
  self.moleculeNResidues.setValue(0)
  self.moleculeNChargeGroups.setValue(0)

  self.moveToResidueSelect.setOptions([])

  self.pdbText.setValue('')
  self.itpText.setValue('')

  self.alignmentPanel.clear()
  self.unitSelect.setValue()
  self.sideStage.removeAllComponents()
  }
}

PolyTop.GuiBackend.prototype.resetView = function () {
  var self = this;
  if (self.currentMolecule) {
    self.currentMolecule.autoViewTo()
  }
}

PolyTop.GuiBackend.prototype.resizeStages = function () {
  var self = this;
  setTimeout(function () { self.stage.handleResize() }, 5)
  setTimeout(function () { self.sideStage.handleResize() }, 5)
}

PolyTop.GuiBackend.prototype.addFragmentToMolecule = function () {
  var self = this;
  self.currentMolecule.addFragment()
  self.updateUniverse()
  self.selectedAtomIndices = []
  return
}


PolyTop.GuiBackend.prototype.drawFragment = function (fragment) {
  var self = this;
  var comp = self.currentMolecule.component
  self.removeDrawnFragment()
  if (comp) {
    self.baseDrawFragment(comp, fragment.getSeleString(), fragment.color)
    .setName('selectedFragment')
    .setVisibility(true)
    self.labelAtoms(fragment)
  }
}



hexToArray = function (hex){
    hex = hex.replace('#','');
    r = parseInt(hex.substring(0,2), 16);
    g = parseInt(hex.substring(2,4), 16);
    b = parseInt(hex.substring(4,6), 16);
    return [0.1+r/255, 0.1+g/255, 0.1+b/255];
}

PolyTop.GuiBackend.prototype.labelAtoms = function (fragment) {
  
  // label fragment atoms on main stage in order

    var self = this;
    self.stage.compList.forEach(function(comp) {
        if (comp.name==='atomIndices') {
            self.stage.removeComponent(comp)
        }
    })

    var positions = fragment.getPositionVectors()
    if (positions) {
        var color = hexToArray(fragment.color)
        var shape = new NGL.Shape('atomIndices', {disableImpostor: true});
        for (let i = 0; i < positions.length; i++) {
            let vec = positions[i]
            let textIdx = (i+1).toString()
            shape.addText(vec, color, 2, textIdx)
        }
        var newComp = self.stage.addComponentFromObject(shape).setName('atomIndices')
        newComp.addRepresentation('buffer');
    }

}

PolyTop.GuiBackend.prototype.highlightResidueIndex = function (index) {
  var self = this;
  if (self.currentMolecule) {
    var res = self.currentMolecule.topology.residues[index]
    if (res) {
      self.highlightSelection(res.atoms)
    }
  }
}

PolyTop.GuiBackend.prototype.highlightSelection = function (proxyList, color) {
  var self = this;
  if (self.currentMolecule) {
    self.removeHighlighted()
    var indices = []
    proxyList.forEach(function (proxy) {
      indices.push(proxy.index)
    })
    if (indices.length > 0) {
      var sele = '@' + indices.toString()
      self.baseDrawFragment(self.currentMolecule.component, sele, color)
      .setName('highlighted')
    }
    }
}

PolyTop.GuiBackend.prototype.removeHighlighted = function () {
  var self = this;
  this.stage.compList.forEach(function (comp) {
    comp.reprList.forEach(function (repr) {
      if (repr.name === 'highlighted') {
        comp.removeRepresentation(repr)
      }
    })
  })
}

PolyTop.GuiBackend.prototype.baseDrawFragment = function (comp, sele, color) {
  if (!color) {color = '#ffffff'}
  return comp.addRepresentation('ball+stick', {
    sele: sele,
    opacity: 0.5,
    bondScale: 1.4,
    radiusScale: 1.4,
    colorScheme: 'uniform',
    atomColor:color,
    bondColor:color,
    valueColor:color,
    colorValue: color})
}

PolyTop.GuiBackend.prototype.removeDrawnFragment = function() {
  var comp = this.currentMolecule.component
  if (comp) {
    comp.reprList.forEach(function (repr) {
        if (repr.name === 'selectedFragment') {
          comp.removeRepresentation(repr)
        }
      })
  }
  
}

PolyTop.GuiBackend.prototype.exportImage = function (factorValue, antialiasValue, trimValue, transparentValue, progress) {
  var self = this;
  var onProgress = function (i, n, finished) {
    if (i === 1) {
      progress.setMax(n)
    }
    
    if (i >= n) {
      progress.setIndeterminate()
    } else {
      progress.setValue(i)
    }

    if (finished) {
      progress.setDisplay('none')
    }
  }

  return self.stage.makeImage({
      factor: parseInt(factorValue),
      antialias: antialiasValue,
      trim: trimValue,
      transparent: transparentValue,
      onProgress: onProgress
    }).then(function (blob) {
      NGL.download(blob, 'screenshot.png')
    })
}