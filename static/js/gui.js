PolyTop.Gui = function () {
  var backend = new PolyTop.GuiBackend()
  var molInfo = new PolyTop.MoleculeInformation(backend)
  var molEdit = new PolyTop.MoleculeEditor(backend)
  var layout = new PolyTop.Layout('layout', backend, molInfo, molEdit)
  var menubar = new PolyTop.Menubar(backend, molInfo, molEdit)
  document.body.appendChild(menubar.dom)
  


}

PolyTop.StageWidget = function (backend, molInfo, molEdit) {
  

  var topRight = new UI.Panel().setId('moleculeButtons')
  topRight.add(
    backend.createMoleculeButton, 
    backend.saveMonomerButton, 
    backend.duplicateMoleculeButton,
    backend.downloadFilesButton)
  

  var topLeft = new UI.Panel().setWidth('400px')
  backend.molSelect.addTo(topLeft, 'Molecule')
  topLeft.addEntry('Name', backend.molName)

  
  
  var molContainer = new UI.Panel().setClass('moleculeInterface')
  molContainer.add(topLeft, topRight)

  var allContainer = new UI.Panel()
  var infoContainer = new UI.Panel().setId('molOverlayContainer')
    .add(molInfo, molEdit)
  allContainer.add(molContainer, infoContainer)

  var container = new UI.Panel()
  container.add(backend.view, allContainer)
  return container
}

PolyTop.Menubar = function (backend, molInfo, molEdit) {
  var container = new UI.Panel().setId('menubar')
  
  var viewWidget = new PolyTop.ViewMenu(backend.stage, molInfo, molEdit)
  var fileWidget = new PolyTop.FileMenu(backend)
  var editWidget = new PolyTop.EditMenu(backend)
  var polyTop = new UI.Text('PolyTop v0.00').setFloat('right')
  var polyTopPanel = new UI.Panel().setMargin('8px').setFontWeight('600').add(polyTop)
  

  container.add(
    fileWidget,
    editWidget,
    viewWidget,
    polyTopPanel
  )
  return container
}

PolyTop.EditMenu = function (backend) {
  var container = new UI.Menu('Edit')
    .addLabeled(backend.undoButton)
    .addLabeled(backend.redoButton)
  return container
}

PolyTop.ViewMenu = function (stage, molInfo, molEdit) {


  function onPerspectiveCameraOptionClick () {
    stage.setParameters({ cameraType: 'perspective' })
  }

  function onOrthographicCameraOptionClick () {
    stage.setParameters({ cameraType: 'orthographic' })
  }

  function onStereoCameraOptionClick () {
    stage.setParameters({ cameraType: 'stereo' })
  }

  function onToggleSpinClick () {
    stage.toggleSpin()
  }

  function onToggleRockClick () {
    stage.toggleRock()
  }

  var menu = new UI.Menu('View')
    .addOption('Show molecule information', function () {molInfo.setDisplay('block')})
    .addOption('Show molecule editor', function () {molEdit.setDisplay('block')})
    .addOption('Perspective', onPerspectiveCameraOptionClick)
    .addOption('Orthographic', onOrthographicCameraOptionClick)
    .addOption('Stereo', onStereoCameraOptionClick)
    .addOption('Toggle spin', onToggleSpinClick)
    .addOption('Toggle rock', onToggleRockClick)

  
  return menu
}

PolyTop.FileMenu = function (backend) {
  var exportPanel = new PolyTop.ExportImageWidget(backend)
  var menu = new UI.Menu('File')
  
    .addLabeled(backend.pdbLoadButton)
    .addLabeled(backend.itpLoadButton)
    .addLabeled(backend.universeLoadButton)
    .addLabeled(backend.universeSaveButton)
    .addOption('Export image', function () {exportPanel.setDisplay('block')})
  return menu
}


PolyTop.Layout = function (idName, backend, molInfo, molEdit) {
  var self = this;
  var headingSize = 64;

  var fileTitle = new UI.Panel().setId('fileTitle')
  fileTitle.add(new UI.Text('Files').setWidth('100%'))

  
  // var top = new PolyTop.IOTopBar(backend)
  var bottom = new PolyTop.FileBottomBar(backend, fileTitle)
  var right = new PolyTop.UnitRightBar(backend)
  var left = new PolyTop.FragmentLeftBar(backend)
  var main = new PolyTop.StageWidget(backend, molInfo, molEdit)

  var bottomSize = 200;

  this.dom = new UI.Panel().setId(idName).dom
  document.body.appendChild(this.dom)
  

  var pstyle = 'padding: 5px;'

  $('#'+idName).w2layout({
    name: idName,
    padding: 4,
    panels: [
      { type: 'left', size: 300, minSize: headingSize, resizable: true, style: pstyle,  content: left, title: 'Fragment editor'},
      { type: 'main', content: main, overflow: 'hidden', resizeable:true, },
      { type: 'right', size: 300, minSize: headingSize, resizable: true, style: pstyle, content: right, title: 'Add units'},
      { type: 'bottom', size: bottomSize, minSize: headingSize, resizable: true, style: pstyle, content: bottom }
    ],
    onResize: function () {
      backend.resizeStages()
    }
  })
  
  fileTitle.onClick(function () {
    if (w2ui[idName].panels[3].height === headingSize) {
      w2ui[idName].sizeTo('bottom', bottomSize)
    } else {
      w2ui[idName].sizeTo('bottom', headingSize)
    }
  })

  this.ui = w2ui[idName]
  return this
}




PolyTop.FragmentLeftBar = function (backend) {
  var container = new UI.Panel().setId('fragmentPanel')
  var top = new UI.Panel()
  backend.fragmentAtoms.addTo(top, 'Atoms')
  top.addEntry('Name', backend.fragmentName)
  top.addEntry('Colour', backend.fragmentColorContainer)
  var spacer = new UI.Spacer().setWidth('100%')

  container.add(top, spacer, backend.fragmentPanel)
  return container

}

PolyTop.FileBottomBar = function (backend, fileTitle) {
  var name = 'fileBottomBar'

  $().w2layout({
    name: name,
    padding: 4,
    panels: [
      { type: 'top',  size: 24, resizeable: false, content: fileTitle, overflow: 'hidden',},
      { type: 'left', size: '50%', resizable: true, content: backend.pdbText, title: 'PDB', overflow: 'visible'},
      { type: 'main', size: '50%', resizable: true, content: backend.itpText, title: 'ITP', overflow: 'visible'},
        ]
  })

  return w2ui[name]
}

PolyTop.UnitRightBar = function (backend) {
  var container = new UI.Panel().setMarginTop('20px')
  backend.unitSelect.addTo(container, 'Unit')
  container.add(backend.sideView, backend.alignmentPanel)
  return container
}

PolyTop.ExportImageWidget = function (backend) {
  
  var factorSelect = new UI.Select()
    .setOptions({
      '1': '1x',
      '2': '2x',
      '3': '3x',
      '4': '4x',
      '5': '5x',
      '6': '6x',
      '7': '7x',
      '8': '8x',
      '9': '9x',
      '10': '10x'
    })
    .setValue('4')
  
  var antialiasCheckbox = new UI.Checkbox()
    .setValue(true)

  var trimCheckbox = new UI.Checkbox()
    .setValue(false)

  var transparentCheckbox = new UI.Checkbox()
    .setValue(false)
  
  var progress = new UI.Progress().setClass('progressBar')
    .setDisplay('none')
  
  var exportButton = new UI.Button('Export')
  exportButton.onClick(function (e) {
      e.preventDefault();
      exportButton.setDisplay('none')
      progress.setDisplay('inline-block')
      backend.exportImage(
        factorSelect.getValue(), 
        antialiasCheckbox.getValue(),
        trimCheckbox.getValue(),
        transparentCheckbox.getValue(),
        progress
      ).then(function () {exportButton.setDisplay('inline-block')})
    })
  
  
  

  var container = new UI.OverlayPanel().setId('exportImagePanel')
    .addHeading('Export image')
    .addEntry('Scale', factorSelect)
    .addEntry('Antialias', antialiasCheckbox)
    .addEntry('Trim', trimCheckbox)
    .addEntry('Transparent', transparentCheckbox)
    .add(new UI.Break(), exportButton, progress)
    .attach()
  
  return container

}

PolyTop.MoleculeInformation = function (backend) {
  var container = new UI.OverlayPanel().setId('moleculeInformation').setClass('Panel OverlayPanel moleculeOverlay')
    .addHeading('Molecule details')
    .addEntry('Charge', backend.moleculeCharge)
    .addEntry('# atoms', backend.moleculeNAtoms)
    .addEntry('# residues', backend.moleculeNResidues)
    .addEntry('# charge groups', backend.moleculeNChargeGroups)
  return container

}

PolyTop.MoleculeEditor = function (backend) {
  var container = new UI.OverlayPanel().setId('moleculeEditor').setClass('Panel OverlayPanel moleculeOverlay')
    .addHeading('Molecule editor')
    .addEntry('', backend.deleteAtomsButton)
  backend.moveToResidueSelect.addTo(container, 'Move to')
  container.addEntry('', backend.moveToResidueButton)
  
  return container
}