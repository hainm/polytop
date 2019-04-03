/**
 * @author mrdoob / http://mrdoob.com/
 * The MIT License, Copyright &copy; 2010-2016 three.js authors
 * 
 * Modified by Alexander S. Rose
 * 
 * Modified by Lily Wang
 */


var UI = {}

UI.Element = function () {}

UI.Element.prototype = {

  setId: function (id) {
    this.dom.id = id

    return this
  },

  setClass: function (name) {
    this.dom.className = name

    return this
  },

  setStyle: function (style, array) {
    for (var i = 0; i < array.length; i++) {
      this.dom.style[ style ] = array[ i ]
    }
  },

  getStyle: function (style) {
    return this.dom.style[ style ]
  },

  getBox: function () {
    return this.dom.getBoundingClientRect()
  },

  setDisabled: function (value) {
    this.dom.disabled = value

    return this
  },

  dispose: function () {
    this.dom.parentNode.removeChild(this.dom)
  },

  render: function () {
    $(this.box).empty()
    $(this.box).append(this.dom)
  }

}

// properties

var properties = [
  'position', 'left', 'top', 'right', 'bottom', 'width', 'height', 'border',
  'borderLeft', 'borderTop', 'borderRight', 'borderBottom', 'borderColor',
  'display', 'overflow', 'overflowX', 'overflowY', 'margin', 'marginLeft',
  'marginTop', 'marginRight', 'alignSelf', 'alignItems', 'justifyContent',
  'marginBottom', 'padding', 'paddingLeft', 'paddingTop', 'paddingRight',
  'paddingBottom', 'color', 'backgroundColor', 'opacity', 'fontSize',
  'fontWeight', 'fontStyle', 'fontFamily', 'textTransform', 'cursor',
  'verticalAlign', 'clear', 'float', 'zIndex', 'minHeight', 'maxHeight',
  'minWidth', 'maxWidth', 'wordBreak', 'wordWrap', 'spellcheck',
  'lineHeight', 'whiteSpace', 'textOverflow', 'textAlign', 'pointerEvents',
  'webkitTransform', 'webkitTransformOrigin'
]

properties.forEach(function (property) {
  var methodSuffix = property.substr(0, 1).toUpperCase() +
                        property.substr(1, property.length)

  UI.Element.prototype[ 'set' + methodSuffix ] = function () {
    this.setStyle(property, arguments)
    return this
  }

  UI.Element.prototype[ 'get' + methodSuffix ] = function () {
    return this.getStyle(property)
  }
})

// events

var events = [
  'KeyUp', 'KeyDown', 'KeyPress',
  'MouseOver', 'MouseOut', 'MouseDown', 'MouseUp', 'MouseMove',
  'Click', 'Change', 'Input', 'Scroll'
]

events.forEach(function (event) {
  var method = 'on' + event
  var mouseEvent = event.toLowerCase()

  UI.Element.prototype[ method ] = function (callback) {
    this.dom.addEventListener(mouseEvent, callback.bind(this), false)
    return this
  }

  UI.Element.prototype[mouseEvent] = function () {
    this.dom.dispatchEvent(new Event(mouseEvent))
  }
})

// Break

UI.Break = function () {
  UI.Element.call(this)

  var dom = document.createElement('br')
  dom.className = 'Break'

  this.dom = dom

  return this
}

UI.Break.prototype = Object.create(UI.Element.prototype)


// Panel

UI.Panel = function () {
  UI.Element.call(this)

  var dom = document.createElement('div')
  dom.className = 'Panel'

  this.dom = dom
  this.children = []

  return this
}

UI.Panel.prototype = Object.create(UI.Element.prototype)

UI.Panel.prototype.add = function () {
  for (var i = 0; i < arguments.length; i++) {
    this.dom.appendChild(arguments[ i ].dom)
    this.children.push(arguments[ i ])
  }

  return this
}

UI.Panel.prototype.remove = function () {
  for (var i = 0; i < arguments.length; i++) {
    this.dom.removeChild(arguments[ i ].dom)

    var idx = this.children.indexOf(arguments[ i ])
    if (idx !== -1) this.children.splice(idx, 1)
  }

  return this
}

UI.Panel.prototype.clear = function () {
  while (this.dom.children.length) {
    this.dom.removeChild(this.dom.lastChild)
  }

  this.children.length = 0

  return this
}

UI.Panel.prototype.addEntry = function (label, entry) {
  var container = new UI.Panel().setClass('AlignedEntry')
  entry.setWidth('65%')
  var heading = new UI.Text(label).setWidth('25%').setTextAlign('right')
  container.add(heading, entry)
  this.add(container)
  return this
}

UI.Panel.prototype.setTextContent = function (value) {
  this.dom.textContent = value
  return this
}


UI.OverlayPanel = function () {
  UI.Panel.call(this)

  this.dom.className = 'Panel OverlayPanel'
  this.dom.tabIndex = '-1'
  this.dom.style.outline = 'none'

  return this
}

UI.OverlayPanel.prototype = Object.create(UI.Panel.prototype)

UI.OverlayPanel.prototype.attach = function (node) {
  node = node || document.body

  node.appendChild(this.dom)

  return this
}

UI.OverlayPanel.prototype.addHeading = function (heading) {

  var self = this;
  this.icon = new UI.Icon('times')
    .onClick(function () {
      self.setDisplay('none')
    })

  this.headingPanel = new UI.Panel().setClass('heading')
    .add(new UI.Text(heading), this.icon)
  this.add(this.headingPanel)
  return this
}


// Text

UI.Text = function (text) {
  UI.Element.call(this)

  var dom = document.createElement('span')
  dom.className = 'Text'

  this.dom = dom
  this.setValue(text)
  return this
}

UI.Text.prototype = Object.create(UI.Element.prototype)

UI.Text.prototype.setValue = function (value) {
  if (value !== undefined) {
    this.dom.textContent = value
  }

  return this
}

UI.Text.prototype.rotateLeft = function () {
  this.unrotate()
  this.dom.classList.add('rotateLeft')
}

UI.Text.prototype.rotateRight = function () {
  this.unrotate()
  this.dom.classList.add('rotateRight')
}

UI.Text.prototype.unrotate = function () {
  this.dom.classList.remove('rotateLeft')
  this.dom.classList.remove('rotateRight')
}

// TextArea

UI.TextArea = function () {
  UI.Element.call(this)

  var dom = document.createElement('textarea')
  dom.className = 'TextArea'
  dom.style.padding = '2px'
  dom.style.border = '1px solid #ccc'

  dom.addEventListener('keydown', function (event) {
    event.stopPropagation()
  }, false)

  this.dom = dom

  return this
}

UI.TextArea.prototype = Object.create(UI.Element.prototype)

UI.TextArea.prototype.getValue = function () {
  return this.dom.value
}

UI.TextArea.prototype.setValue = function (value) {
  this.dom.value = value

  return this
}


// Number

UI.Number = function (number) {
  UI.Element.call(this)

  var scope = this

  var dom = document.createElement('input')
  dom.className = 'Number'
  dom.value = '0.00'

  dom.addEventListener('keydown', function (event) {
    event.stopPropagation()

    if (event.keyCode === 13) dom.blur()
  }, false)

  this.min = -Infinity
  this.max = Infinity

  this.precision = 2
  this.step = 1

  this.dom = dom
  this.setValue(number)

  var changeEvent = document.createEvent('HTMLEvents')
  changeEvent.initEvent('change', true, true)

  var distance = 0
  var onMouseDownValue = 0

  var pointer = [ 0, 0 ]
  var prevPointer = [ 0, 0 ]

  var onMouseDown = function (event) {
    event.preventDefault()

    distance = 0

    onMouseDownValue = parseFloat(dom.value)

    prevPointer = [ event.clientX, event.clientY ]

    document.addEventListener('mousemove', onMouseMove, false)
    document.addEventListener('mouseup', onMouseUp, false)
  }

  var onMouseMove = function (event) {
    var currentValue = dom.value

    pointer = [ event.clientX, event.clientY ]

    distance += (pointer[ 0 ] - prevPointer[ 0 ]) - (pointer[ 1 ] - prevPointer[ 1 ])

    var modifier = 50
    if (event.shiftKey) modifier = 5
    if (event.ctrlKey) modifier = 500

    var number = onMouseDownValue + (distance / modifier) * scope.step

    dom.value = Math.min(scope.max, Math.max(scope.min, number)).toFixed(scope.precision)

    if (currentValue !== dom.value) dom.dispatchEvent(changeEvent)

    prevPointer = [ event.clientX, event.clientY ]
  }

  var onMouseUp = function (event) {
    document.removeEventListener('mousemove', onMouseMove, false)
    document.removeEventListener('mouseup', onMouseUp, false)

    if (Math.abs(distance) < 2) {
      dom.focus()
      dom.select()
    }
  }

  var onChange = function (event) {
    var number = parseFloat(dom.value)

    dom.value = isNaN(number) === false ? number : 0
  }

  var onFocus = function (event) {
    dom.style.backgroundColor = ''
    dom.style.borderColor = '#ccc'
    dom.style.cursor = ''
  }

  var onBlur = function (event) {
    dom.style.backgroundColor = 'transparent'
    dom.style.borderColor = 'transparent'
    dom.style.cursor = 'col-resize'
  }

  dom.addEventListener('mousedown', onMouseDown, false)
  dom.addEventListener('change', onChange, false)
  dom.addEventListener('focus', onFocus, false)
  dom.addEventListener('blur', onBlur, false)

  return this
}

UI.Number.prototype = Object.create(UI.Element.prototype)

UI.Number.prototype.getValue = function () {
  return parseFloat(this.dom.value)
}

UI.Number.prototype.setValue = function (value) {
  if (isNaN(value)) {
    this.dom.value = NaN
  } else if (value !== undefined) {
    this.dom.value = value.toFixed(this.precision)
  }

  return this
}

UI.Number.prototype.setRange = function (min, max) {
  this.min = min
  this.max = max

  return this
}

UI.Number.prototype.setPrecision = function (precision) {
  this.precision = precision
  this.setValue(parseFloat(this.dom.value))

  return this
}

UI.Number.prototype.setName = function (value) {
  this.dom.name = value

  return this
}


//

UI.Select = function () {
  UI.Element.call(this)

  var dom = document.createElement('select')
  dom.className = 'FancySelect'
  // dom.style.width = '64px'
  // dom.style.height = '16px'
  // dom.style.border = '0px'
  // dom.style.padding = '0px'

  this.dom = dom

  return this
}

UI.Select.prototype = Object.create(UI.Element.prototype)

UI.Select.prototype.setMultiple = function (boolean) {
  this.dom.multiple = boolean

  return this
}

UI.Select.prototype.setSize = function (value) {
  this.dom.size = value
  return this
}

UI.Select.prototype.setOptions = function (options) {
  var selected = this.dom.value

  while (this.dom.children.length > 0) {
    this.dom.removeChild(this.dom.firstChild)
  }

  for (var key in options) {
    var option = document.createElement('option')
    option.value = key
    option.innerHTML = key
    
    this.dom.appendChild(option)
  }

  this.dom.value = selected

  return this
}



UI.Select.prototype.getValue = function () {
  return this.dom.value
}

UI.Select.prototype.setValue = function (value) {
  this.dom.value = value
  return this
}

UI.Select.prototype.setName = function (value) {
  this.dom.name = value

  return this
}


UI.Option = function (args) {
  UI.Element.call(this)
  var dom = document.createElement('option')
  for (var name in args) {
    dom[name] = args[name]
  }
  this.dom = dom
  return this
}

UI.Option.prototype = Object.create(UI.Element.prototype)

// Selectize

UI.Selectize = function (idName) {
  UI.Element.call(this)

  this.dom = document.createElement('select')
  this.dom.className = 'selectize-control'
  this.dom.display = 'inline-block'
  this.dom.id = idName;
  
  this.selectizeArguments = {};
  this.options = [];
  this.optgroups = [];
  this.optgroupValueField = undefined;

  var container = new UI.Panel().setDisplay('inline-block');
  container.dom.overflow = 'scroll'
  container.dom.margin = '0px'
  container.dom.padding = '0px'
  container.dom.style['z-index'] = 10000

  container.add(this)
  this.container = container

  return this
}

UI.Selectize.prototype = Object.create(UI.Element.prototype)

UI.Selectize.prototype.clearValue = function () {
  var self = this;
}

UI.Selectize.prototype.setMultiple = function (boolean) {
  this.dom.multiple = boolean

  return this
}

UI.Selectize.prototype.setArguments = function (arg) {
  this.selectizeArguments = arg
  // this.init()
  return this
}

UI.Selectize.prototype.addTo = function (parent, label) {
  
  if (label) {
    parent.addEntry(label, this.container)
  } else {
    parent.add(this.container)
  }
    
  
  this.init()
  return this;

}

UI.Selectize.prototype.setWidth = function (value) {
  this.container.setWidth(value)
  return this;
}

UI.Selectize.prototype.init = function () {
  var self = this;
  self.createSelectize(self.selectizeArguments);
  self.setOptions(self.options)
  self.selectize.close();
  self.selectize.blur();
}

UI.Selectize.prototype.createSelectize = function (selectizeArguments) {

  var defaults = {
    plugins: [],
    maxItems: null,
    optgroupValueField: 'value',
    labelField: 'value',
    valueField: 'value', 
    delimiter: ',',
    create: false, 
    sortField: ['value'],
    searchField: ['value']
  }
  
  for (var name in selectizeArguments) {
    defaults[name] = selectizeArguments[name]
  }

  this.optgroupValueField = defaults.optgroupValueField

  var $select = $(this.dom).selectize(defaults)
  this.selectize = $select[0].selectize;
  return this;
}

UI.Selectize.prototype.setMultiple = function (boolean) {
  this.dom.multiple = boolean
  return this
}

UI.Selectize.prototype.setPlaceholder = function (value) {
  this.dom.placeholder = value;
  return this;
}

UI.Selectize.prototype.setValue = function (value, silent) {
  this.selectize.setValue(value, silent)
  return this;
}

UI.Selectize.prototype.getValue = function () {
  return this.selectize.getValue()
}

UI.Selectize.prototype.setOptions = function (options) {
  var self = this;
  this.selectize.clearOptions()
  this.selectize.addOption(options)
  this.selectize.refreshOptions(false)
  return this;
}

UI.Selectize.prototype.setOptGroups = function (options) {
  var self = this;
  this.selectize.clearOptionGroups()
  options.forEach(function (optgroup) {
    self.selectize.addOptionGroup(optgroup[self.optgroupValueField], optgroup)
  })
  this.selectize.refreshOptions(false)
  return this;
}

// Checkbox

UI.Checkbox = function (boolean) {
  UI.Element.call(this)

  var scope = this

  var dom = document.createElement('input')
  dom.className = 'Checkbox'
  dom.type = 'checkbox'

  this.dom = dom
  this.setValue(boolean)

  return this
}

UI.Checkbox.prototype = Object.create(UI.Element.prototype)

UI.Checkbox.prototype.getValue = function () {
  return this.dom.checked
}

UI.Checkbox.prototype.setValue = function (value) {
  if (value !== undefined) {
    this.dom.checked = value
  }

  return this
}

UI.Checkbox.prototype.setName = function (value) {
  this.dom.name = value

  return this
}

// Color

UI.Color = function () {
  UI.Element.call(this)

  var scope = this

  var dom = document.createElement('input')
  dom.className = 'Color'
  dom.style.width = '64px'
  dom.style.height = '16px'
  dom.style.border = '0px'
  dom.style.padding = '0px'
  dom.style.backgroundColor = 'transparent'

  try {
    dom.type = 'color'
    dom.value = '#ffffff'
  } catch (exception) {}

  this.dom = dom

  return this
}

UI.Color.prototype = Object.create(UI.Element.prototype)

UI.Color.prototype.getValue = function () {
  return this.dom.value
}

UI.Color.prototype.getHexValue = function () {
  return parseInt(this.dom.value.substr(1), 16)
}

UI.Color.prototype.setValue = function (value) {
  this.dom.value = value

  return this
}

UI.Color.prototype.setHexValue = function (hex) {
  this.dom.value = '#' + ('000000' + hex.toString(16)).slice(-6)

  return this
}

// Button

UI.Button = function (value) {
  UI.Element.call(this)

  var dom = document.createElement('button')
  dom.className = 'Button'

  this.dom = dom
  this.dom.textContent = value

  return this
}

UI.Button.prototype = Object.create(UI.Element.prototype)



UI.Icon = function (value) {
  UI.Panel.call(this)

  var dom = document.createElement('span')
  dom.className = 'Icon fa'

  this.dom = dom

  if (value) this.addClass.apply(this, arguments)

  return this
}

UI.Icon.prototype = Object.create(UI.Panel.prototype)

UI.Icon.prototype.hasClass = function (value) {
  return this.dom.classList.contains('fa-' + value)
}

UI.Icon.prototype.addClass = function (value) {
  for (var i = 0; i < arguments.length; i++) {
    this.dom.classList.add('fa-' + arguments[ i ])
  }

  return this
}

UI.Icon.prototype.setClass = function (value) {
  this.dom.className = 'Icon fa'

  for (var i = 0; i < arguments.length; i++) {
    this.dom.classList.add('fa-' + arguments[ i ])
  }

  return this
}

UI.Icon.prototype.removeClass = function (value) {
  for (var i = 0; i < arguments.length; i++) {
    this.dom.classList.remove('fa-' + arguments[ i ])
  }

  return this
}

UI.Icon.prototype.switchClass = function (newValue, oldValue) {
  this.removeClass(oldValue, newValue)
  this.addClass(newValue)

  return this
}


// LabelFor
UI.Labeled = function (faIcon, item) {
  UI.Panel.call(this)
  item.setDisplay('none').setClass('hidden')
  this.item = item;
  this.label = document.createElement('label')
  this.label.setAttribute('for', item.dom.id)
  this.icon = new UI.Icon(faIcon)
  this.labelName = new UI.Text(item.dom.id)

  var container = new UI.Panel()

  container.add(this.item)
  container.dom.appendChild(this.label)
  this.label.appendChild(this.labelName.dom)
  this.label.appendChild(this.icon.dom)
  


  this.dom = container.dom
  return this;

}

UI.Labeled.prototype = Object.create(UI.Panel.prototype)

UI.Labeled.prototype.setDisabled = function (value) {
  this.item.setDisabled(value)
}



// IconButton

UI.IconButton = function (value, faIcon) {
  var button = new UI.Button(value).setId(value)
  var labeled = new UI.Labeled(faIcon, button)
  // labeled.dom.className = 'menu'
  // labeled.label.className = 'title'
  return labeled
}


// Input

UI.Input = function (value) {
  UI.Element.call(this)

  var dom = document.createElement('input')
  dom.className = 'Input'
  dom.style.padding = '2px'
  dom.style.border = '1px solid #ccc'

  dom.addEventListener('keydown', function (event) {
    event.stopPropagation()
  }, false)

  this.dom = dom
  this.setValue(value || '')

  return this
}

UI.Input.prototype = Object.create(UI.Element.prototype)

UI.Input.prototype.getValue = function () {
  return this.dom.value
}

UI.Input.prototype.setValue = function (value) {
  this.dom.value = value

  return this
}

UI.Input.prototype.setName = function (value) {
  this.dom.name = value

  return this
}

UI.Progress = function (max, value) {
  UI.Element.call(this)

  var dom = document.createElement('progress')
  dom.className = 'Progress'

  dom.max = max || 1.0
  if (value !== undefined) dom.value = value

  this.dom = dom

  return this
}

UI.Progress.prototype = Object.create(UI.Element.prototype)

UI.Progress.prototype.getValue = function () {
  return this.dom.value
}

UI.Progress.prototype.setValue = function (value) {
  this.dom.value = value

  return this
}

UI.Progress.prototype.setMax = function (value) {
  this.dom.max = value

  return this
}

UI.Progress.prototype.setIndeterminate = function () {
  this.dom.removeAttribute('value')

  return this
}


// File

UI.File = function (value, faIcon) {
  var fileInput = new UI.Input()
  fileInput.setId(value)
  fileInput.dom.type = 'file'
  fileInput.dom.multiple = false
  

  UI.Labeled.call(this, faIcon, fileInput)
  return this
}

UI.File.prototype.setMultiple = function (value) {
  this.item.dom.multiple = value
  return this
}

UI.File.prototype.getFiles = function (value) {
  return this.item.dom.files
}

UI.File.prototype.getValue = function () {
  return this.item.getValue()
}

UI.File.prototype.setAccept = function (allowed) {
  this.item.dom.accept = allowed
  return this
}

UI.File.prototype.setWidth = function (value) {
  this.label.width = value
  this.labelName.dom.width = value;
  this.icon.width = value
  return this;
}

UI.File.prototype.setDisabled = function (value) {
  this.item.dom.disabled = value;
  return this;
}

UI.File.prototype.onChange = function (callback) {
  var self = this;
  self.item.onChange(function () {
    var files = self.getFiles()
    if (files) {
      callback(files)
    }
    self.item.setValue('')
  })
}

UI.Spacer = function () {
  var container = new UI.Panel().setClass('spacer-container')
  this.panel = new UI.Panel().setClass('or-spacer')
  

  var mask = new UI.Panel().setClass('mask')
  this.panel.add(mask)
  container.add(this.panel)
  this.dom = container.dom
  return this
}

UI.Spacer.prototype = Object.create(UI.Element.prototype)


UI.LeftSpacer = function () {
  UI.Spacer.call(this)
  this.dom.className = 'spacer-container-vertical'
  this.panel.dom.className = 'or-spacer-vertical'
  this.panel.dom.classList.add('left')
  return this
}

UI.LeftSpacer.prototype = Object.create(UI.Element.prototype)


UI.RightSpacer = function () {
  UI.Spacer.call(this)
  this.dom.className = 'spacer-container-vertical'
  this.panel.dom.className = 'or-spacer-vertical'
  this.panel.dom.classList.add('right')
  console.log(this.dom)
  return this
}

UI.RightSpacer.prototype = Object.create(UI.Element.prototype)



UI.MenuOption = function (name, callback, icon) {
  var option = new UI.Panel()
  option.setClass('option')

  if (icon) {
    
    option.add(new UI.Text(name))
    option.add(new UI.Icon(icon).setWidth('20px'))
    option.setDisplay('flex')
    option.setJustifyContent('space-between')
    
  } else {
    option.setTextContent(name)
  }

  option.onClick(callback)
  return option
}



UI.Menu = function (value) {
  UI.Panel.call(this)
  var title = new UI.Panel()
  title.setClass('title').setTextContent(value)
  title.setMargin('0px').setPadding('8px')
  this.title = title
  var container = new UI.Panel().setClass('menu')
  this.panel = new UI.Panel().setClass('options')
  container.add(this.title, this.panel)
  this.dom = container.dom

  return this
}

UI.Menu.prototype = Object.create(UI.Panel.prototype)

UI.Menu.prototype.addOption = function (name, callback, icon) {
  var option = new UI.MenuOption(name, callback, icon)
  this.panel.add(option)
  return this
}

UI.Menu.prototype.add = function (item) {
  item.setClass('option')
  this.panel.add(item)
}

UI.Menu.prototype.addLabeled = function (labeled) {
  var container = new UI.Panel().setClass('option')
  container.add(labeled)
  labeled.icon.setWidth('20px')
  labeled.label.style['display'] = 'flex'
  labeled.label.style['justify-content'] = 'space-between'
  this.panel.add(container)
  return this;
}

UI.Menu.prototype.addButton = function (button) {
  this.panel.add(button)
  return this;
}
