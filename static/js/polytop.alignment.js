/**
 * @file gui.alignment
 * @author Lily Wang <lily.wang@anu.edu.au>
 * 
 */


// One fragment selection panel

UI.FragmentSelectPanel = function (parent) {
    UI.Panel.call(this)
    this.dom.className = 'fragmentselect'
    var self = this;
    self.parent = parent
    var text = new UI.Text('Align').setWidth('25%').setPaddingRight('5%')

    self.targetFragment = new UI.Selectize()
      .setWidth('65%')
      .setZIndex('100')
      .setArguments(
        {
            maxItems: 1,
            create: false,
            labelField: 'label',
            valueField: 'label',
            disabledField: 'disabled',
            sortField: ['label'],
            searchField: ['label'],
            onChange: function () {parent.updateAlignments()}
        }
      )

    self.over = new UI.Selectize()
      .setWidth('25%')
      .setArguments(
          {
            create: false,
            maxItems: 1,
            labelField: 'text',
            valueField: 'value',
            onChange: function () {parent.updateAlignments()},
            sortField: 'asc',
          }
      )
    
    self.refFragment = new UI.Selectize()
      .setWidth('65%')
      .setArguments(
          {   plugins: ['remove_button'],
              labelField: 'label',
              valueField: 'value',
              disabledField: 'disabled',
              sortField: ['fragmentIndex', 'label'],
              optgroupField: 'name',
              optgroupLabelField: 'name',
              optgroupValueField: 'name',
              searchField: ['label'],
              onChange: function (value) {
                  parent.updateAlignments()
              },
              onItemAdd: function (value, valueItem) {
                  self.selectAll(value)
              },
          }
      )
    self.button = new UI.Icon('times')
      .setCursor('pointer')
      .setMarginRight('6px')
      .setFloat('left')
      .onClick(function () {self.remove()})

    var topPanel = new UI.Panel().setZIndex('100')
    var bottomPanel = new UI.Panel().setZIndex('1')

    topPanel.add(self.button, text)
    self.targetFragment.addTo(topPanel)
    self.targetFragment.setOptions(parent.targetOptions)

    self.over.addTo(bottomPanel) 
    self.over.setOptions([
        {text: 'over', value: true},
        {text: 'under', value: false}])
    self.over.setValue(true)

    self.refFragment.addTo(bottomPanel)
    self.refFragment.setOptions(parent.referenceOptions)
    self.refFragment.setOptGroups(parent.referenceOptGroups)

    self.targetFragment.container.setZIndex('100')
    self.refFragment.container.setZIndex('1')

    this.add(topPanel, bottomPanel)
    return this;
}

UI.FragmentSelectPanel.prototype = Object.create(UI.Panel.prototype)

UI.FragmentSelectPanel.prototype.selectAll = function (value) {
    var self = this;
    var values = self.refFragment.getValue()
    if (self.parent.optGroups[value]) {
        self.parent.optGroups[value].options.forEach(function (fragment) {
            if (!values.includes(fragment.label)) {
                self.refFragment.selectize.addItem(fragment.label)
            }
            
        })
        self.refFragment.selectize.removeItem(value)
    }
}


UI.FragmentSelectPanel.prototype.remove = function () {
    var self = this;
    self.refFragment.selectize.setValue([])
    self.dispose()
}

UI.FragmentSelectPanel.prototype.getValue = function () {
    var self = this;
    var tgFragName = self.targetFragment.getValue()
    var over = self.over.getValue()
    var refValues = self.refFragment.getValue()
    var units = []
    refValues.forEach(function (ref) {
        units.push({tgFragName: tgFragName, refFragName: ref, over: over})
    }) 
    return units
}

// Collection of FragmentSelectPanels

UI.UnitAlignmentPanel = function (reference, target) {
    UI.Panel.call(this)
    var self = this;
    self.selectionPanel = new UI.Panel()
    self.unitChildren = []
    self.reference = reference
    self.reference.removeAlignments()
    self.target = target
    self.targetOptions = []
    self.targetOptionItems = {}
    self.referenceOptions = []
    self.referenceOptGroups = []
    self.optGroups = {}
    self.getTargetOptions()
    self.getReferenceOptions()

    self.buttonPanel = new UI.Panel()
    self.button = new UI.Button('+').setWidth('100%')
        .onClick(function () {self.addFragmentPanel()})
    self.buttonPanel.add(self.button)

    self.add(self.selectionPanel, self.buttonPanel)
    self.addFragmentPanel()
    return this;
}
  
UI.UnitAlignmentPanel.prototype = Object.create(UI.Panel.prototype)



UI.UnitAlignmentPanel.prototype.updateAlignments = function () {
    var self = this;
    var alignments = [[]]
    
    self.unitChildren.forEach(function (panel) {
        
        var entries = panel.getValue()
        for (var i = 0; i < entries.length; i++) {
            while (alignments[i] === undefined) {
                alignments.push([])
            }
            alignments[i].push(entries[i])
        }
    })

    self.createAlignments(alignments)
    
    
}

UI.UnitAlignmentPanel.prototype.getTargetOptions = function () {
    var self = this;
    self.targetOptions = []
    self.targetOptionItems = {}
    self.target.forFragment(function (fragment) {
        var tmp = {label: fragment.label, disabled: false}
        self.targetOptions.push(tmp)
        self.targetOptionItems[fragment.label] = tmp
    })
}

UI.UnitAlignmentPanel.prototype.getReferenceOptions = function () {
    var self = this;
    self.optGroups = {}
    self.referenceOptions = []
    self.referenceOptGroups = []

    for (var label in self.reference.fragments) {
        var fragment = self.reference.fragments[label]
        if (fragment) {
            if (!self.optGroups[fragment.name]) {
                self.referenceOptGroups.push({name: fragment.name})
                var allOption = {label: 'All', value: fragment.name, name: fragment.name, fragmentIndex: 1, disabled: false}
                self.optGroups[fragment.name] = {allOption: allOption, options: []}
                self.referenceOptions.push(allOption)
            }

            var option = {label: fragment.label, name: fragment.name, value: fragment.label, fragmentIndex: 1, disabled: false}
            self.referenceOptions.push(option)
            self.optGroups[fragment.name].options.push(option)
        }
    }

}

UI.UnitAlignmentPanel.prototype.createAlignments = function (alignments) {
    var self = this;
    self.reference.removeAlignments()
    alignments.forEach(function (unit) {
        new PolyTop.Alignment(self.reference, self.target).then(
            function (alignment) {
                alignment.mapUnitSelect(unit)
                alignment.superposeTarget()
                alignment.drawTransparent()
                self.reference.alignments.push(alignment)
            }
        )
        
    })
}

UI.UnitAlignmentPanel.prototype.addFragmentPanel = function () {
    var self = this;
    var panel = new UI.FragmentSelectPanel(self)
    self.unitChildren.push(panel)
    self.selectionPanel.add(panel)
    for (var i = 0; i < self.unitChildren.length; i++) {
        self.unitChildren[i].setZIndex(((i+1)*100).toString())
        // TODO: fix z-index stuff....
    }
}