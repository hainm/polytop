/**
 * @file UI NGL
 * @author Alexander Rose <alexander.rose@weirdbyte.de>
 */

// Color

UI.ColorPopupMenu = function () {
  var scope = this

  UI.Panel.call(this)

  this.iconText = new UI.Text('')
    .setCursor('pointer')
    .setClass('fa-stack-1x')
    .setFontFamily('Arial, sans-serif')
    .setColor('#111')

  this.iconSquare = new UI.Icon('square', 'stack-1x')
  // .setMarginTop( "0.05em" );

  this.menu = new UI.PopupMenu('stack', 'Color')

  this.menu.icon
    .setTitle('color')
    .setWidth('1em').setHeight('1em').setLineHeight('1em')
    .add(this.iconSquare)
    .add(this.iconText)

  var changeEvent = document.createEvent('Event')
  changeEvent.initEvent('change', true, true)

  this.colorInput = new UI.Input()
    .onChange(function () {
      scope.setColor(scope.colorInput.getValue())
      scope.dom.dispatchEvent(changeEvent)
    })

  this.colorPicker = new UI.ColorPicker()
    .setDisplay('inline-block')
    .onChange(function (e) {
      scope.setColor(scope.colorPicker.getValue())
      scope.dom.dispatchEvent(changeEvent)
    })

  this.menu
    .addEntry('Input', this.colorInput)
    .addEntry('Picker', this.colorPicker)

  this.add(this.menu)

  this.setClass('')
    .setDisplay('inline')

  return this
}

UI.ColorPopupMenu.prototype = Object.create(UI.Panel.prototype)

UI.ColorPopupMenu.prototype.setColor = (function () {
  var c = new NGL.Color()

  return function (value) {
    c.set(value)
    value = '#' + c.getHexString()

    this.colorInput
      .setBackgroundColor(value)
      .setValue(value)

    this.colorPicker.setValue(value)

    this.iconSquare.setColor(value)

    // perceived brightness (http://alienryderflex.com/hsp.html)
    var brightness = Math.sqrt(
      c.r * 255 * c.r * 255 * 0.241 +
              c.g * 255 * c.g * 255 * 0.691 +
              c.b * 255 * c.b * 255 * 0.068
    )

    if (brightness > 130) {
      this.iconText.setColor('#000000')
      this.colorInput.setColor('#000000')
    } else {
      this.iconText.setColor('#FFFFFF')
      this.colorInput.setColor('#FFFFFF')
    }

    return this
  }
}())

UI.ColorPopupMenu.prototype.getColor = function () {
  return this.colorInput.getValue()
}

UI.ColorPopupMenu.prototype.getValue = function () {
  return this.getColor()
}

UI.ColorPopupMenu.prototype.setValue = function (value) {
  this.setColor(value)

  return this
}

UI.ColorPopupMenu.prototype.dispose = function () {
  this.menu.dispose()

  UI.Panel.prototype.dispose.call(this)
}

// Vector3

UI.Vector3 = function (value) {
  UI.Panel.call(this).setDisplay('inline-block')

  this.xNumber = new UI.Number(0).setWidth('40px')
  this.yNumber = new UI.Number(0).setWidth('40px')
  this.zNumber = new UI.Number(0).setWidth('40px')

  this.add(this.xNumber, this.yNumber, this.zNumber)
  this.setValue(value)

  var changeEvent = document.createEvent('Event')
  changeEvent.initEvent('change', true, true)

  this.xNumber.onChange(function () {
    this.dom.dispatchEvent(changeEvent)
  }.bind(this))
  this.yNumber.onChange(function () {
    this.dom.dispatchEvent(changeEvent)
  }.bind(this))
  this.zNumber.onChange(function () {
    this.dom.dispatchEvent(changeEvent)
  }.bind(this))

  return this
}

UI.Vector3.prototype = Object.create(UI.Panel.prototype)

UI.Vector3.prototype.getValue = function () {
  return {
    x: this.xNumber.getValue(),
    y: this.yNumber.getValue(),
    z: this.zNumber.getValue()
  }
}

UI.Vector3.prototype.setValue = function (value) {
  if (value) {
    this.xNumber.setValue(value.x)
    this.yNumber.setValue(value.y)
    this.zNumber.setValue(value.z)
  }

  return this
}

UI.Vector3.prototype.setPrecision = function (precision) {
  this.xNumber.setPrecision(precision)
  this.yNumber.setPrecision(precision)
  this.zNumber.setPrecision(precision)

  return this
}

UI.Vector3.prototype.setRange = function (min, max) {
  this.xNumber.setRange(min, max)
  this.yNumber.setRange(min, max)
  this.zNumber.setRange(min, max)

  return this
}

// Selection

UI.SelectionInput = function (selection) {
  UI.AdaptiveTextArea.call(this)

  this.setSpellcheck(false)

  if (!(selection.type === 'selection')) {
    NGL.error('UI.SelectionInput: not a selection', selection)

    return this
  }

  this.setValue(selection.string)

  this.selection = selection

  var scope = this

  var signals = selection.signals

  signals.stringChanged.add(function (string) {
    scope.setValue(string)
  })

  this.onEnter()

  return this
}

UI.SelectionInput.prototype = Object.create(UI.AdaptiveTextArea.prototype)

UI.SelectionInput.prototype.setValue = function (value) {
  UI.AdaptiveTextArea.prototype.setValue.call(this, value)

  return this
}

UI.SelectionInput.prototype.onEnter = function (callback) {
  // TODO more a private method

  var scope = this

  var check = function (string) {
    var selection = new NGL.Selection(string)

    return !selection.selection[ 'error' ]
  }

  this.onKeyPress(function (e) {
    var value = scope.getValue()
    var character = String.fromCharCode(e.which)

    if (e.keyCode === 13) {
      e.preventDefault()

      if (check(value)) {
        if (typeof callback === 'function') {
          callback(value)
        } else {
          scope.selection.setString(value)
        }

        scope.setBackgroundColor('white')
      } else {
        scope.setBackgroundColor('tomato')
      }
    } else if (scope.selection.string !== value + character) {
      scope.setBackgroundColor('skyblue')
    } else {
      scope.setBackgroundColor('white')
    }
  })

  this.onKeyUp(function (e) {
    var value = scope.getValue()

    if (!check(value)) {
      scope.setBackgroundColor('tomato')
    } else if (scope.selection.string === scope.getValue()) {
      scope.setBackgroundColor('white')
    } else {
      scope.setBackgroundColor('skyblue')
    }
  })

  return this
}

UI.SelectionPanel = function (selection) {
  UI.Panel.call(this)

  this.icon = new UI.Icon('filter')
    .setTitle('filter selection')
    .addClass('lg')
    .setMarginRight('10px')

  this.input = new UI.SelectionInput(selection)

  this.add(this.icon, this.input)

  return this
}

UI.SelectionPanel.prototype = Object.create(UI.Panel.prototype)

UI.SelectionPanel.prototype.setInputWidth = function (value) {
  this.input.setWidth(value)

  return this
}

// Component

UI.ComponentPanel = function (component) {
  UI.Panel.call(this)

  var stage = component.stage
  var signals = component.signals

  signals.nameChanged.add(function (value) {
    name.setValue(value)
  })

  signals.visibilityChanged.add(function (value) {
    toggle.setValue(value)
  })

  signals.disposed.add(function () {
    menu.dispose()
  })

  // Name

  var name = new UI.EllipsisText(component.name)
    .setWidth('100px')

    // Actions

  var toggle = new UI.ToggleIcon(component.visible, 'eye', 'eye-slash')
    .setTitle('hide/show')
    .setCursor('pointer')
    .setMarginLeft('25px')
    .onClick(function () {
      component.setVisibility(!component.visible)
    })

  var center = new UI.Icon('bullseye')
    .setTitle('center')
    .setCursor('pointer')
    .setMarginLeft('10px')
    .onClick(function () {
      component.autoView(1000)
    })

  var dispose = new UI.DisposeIcon()
    .setMarginLeft('10px')
    .setDisposeFunction(function () {
      stage.removeComponent(component)
    })

    // Menu

  var menu = new UI.PopupMenu('bars', component.type)
    .setMarginLeft('46px')
    .setEntryLabelWidth('110px')

    //

  this.add(name, toggle, center, dispose, menu)

  //

  this.menu = menu

  return this
}

UI.ComponentPanel.prototype = Object.create(UI.Panel.prototype)

UI.ComponentPanel.prototype.addMenuEntry = function (label, entry) {
  this.menu.addEntry(label, entry)

  return this
}

UI.ComponentPanel.prototype.setMenuDisplay = function (value) {
  this.menu.setMenuDisplay(value)

  return this
}

UI.ContentPanel = function () {
  UI.Panel.call(this)

  this.dom.className = 'Panel CollapsiblePanel'
  this.accordion = []

  iconClass1 = 'minus-square'
  iconClass2 = 'plus-square'
  

  this.button = new UI.Icon(iconClass1)
    .setTitle('expand/collapse')
    .setCursor('pointer')
    .setWidth('12px')
    .setMarginRight('6px')
  this.addStatic(this.button)

  var scope = this
  this.button.dom.addEventListener('click', function (event) {
    scope.toggle()
  }, false)

  var content = new UI.Panel()
  content.setMargin('10px')

  this.content = content.dom
  this.content.className = 'CollapsibleContent'
  this.dom.appendChild(this.content)

  this.isCollapsed = false

  this.iconClass1 = iconClass1
  this.iconClass2 = iconClass2

  return this
}

UI.ContentPanel.prototype = Object.create(UI.CollapsibleIconPanel.prototype)

UI.ContentPanel.prototype.add = function () {
  for (var i = 0; i < arguments.length; i++) {
    this.content.appendChild(arguments[ i ].dom)
  }

  return this
}


UI.ContentPanel.prototype.addHeading = function (text) {
  // headingPanel = new UI.Panel()
  //   // .setBorderTop('1px solid #555')
  //   .setBorderBottom('1px solid #555')
  //   .setHeight('25px')
  //   .setMarginTop('10px')
  //   .add(new UI.Text(text))
  
  this.addStatic(new UI.EllipsisText(text))

  return this
}

UI.AccordionPanel = function () {
  UI.Panel.call(this)

  this.dom.className = 'Panel CollapsiblePanel'
  this.accordion = []

  iconClass1 = 'chevron-down'
  iconClass2 = 'chevron-right'
  

  this.button = new UI.Icon(iconClass1)
    .setTitle('expand/collapse')
    .setCursor('pointer')
    .setWidth('12px')
    .setMarginRight('6px')
  this.addStatic(this.button)

  var scope = this
  this.button.dom.addEventListener('click', function (event) {
    scope.toggle()
  }, false)

  this.content = document.createElement('div')
  this.content.className = 'CollapsibleContent'
  this.dom.appendChild(this.content)

  this.isCollapsed = false

  this.iconClass1 = iconClass1
  this.iconClass2 = iconClass2

  return this
}

UI.AccordionPanel.prototype = Object.create(UI.CollapsiblePanel.prototype)

UI.AccordionPanel.prototype.setCollapsed = function (setCollapsed) {
  if (setCollapsed) {
    this.dom.classList.add('collapsed')

    if (this.iconClass2) {
      this.button.switchClass(this.iconClass2, this.iconClass1)
    } else {
      this.button.addClass('rotate-90')
    }
  } else {
    for (var i = 0; i < this.accordion.length; i++) {
      var panel = this.accordion[i]
      if (!panel.isCollapsed && panel !== this) {
        panel.collapse()
      }
    }
    this.dom.classList.remove('collapsed')

    if (this.iconClass2) {
      this.button.switchClass(this.iconClass1, this.iconClass2)
    } else {
      this.button.removeClass('rotate-90')
    }
  }

  this.isCollapsed = setCollapsed
}

UI.CollapsibleAccordion = function () {
  UI.Panel.call(this)
  this.panels = []
  return this
}

UI.CollapsibleAccordion.prototype = Object.create(UI.Panel.prototype)

UI.CollapsibleAccordion.prototype.addPanelEntry = function (label, entry) {
  var heading = new UI.EllipsisText(label)
  entry.addStatic(heading)
  this.add(entry)
  entry.accordion = this.panels
  this.panels.push(entry)

  return this
}

UI.Panel.prototype.addVertical = function () {
  for (var i = 0; i < arguments.length; i++) {
    this.add(new UI.Break())
    this.add(arguments[ i ])
    this.add(new UI.Break())
  }
  return this
}



UI.Panel.prototype.addEntries = function () {
  for (var i = 0; i < arguments.length; i++) {
    this.addEntry(arguments[i][0], arguments[i][1])
  }
  return this
}

UI.Input.prototype.setPlaceholder = function (value) {
  this.dom.setAttribute('placeholder', value)
  return this
}