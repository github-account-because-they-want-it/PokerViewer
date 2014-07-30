'''
Created on Jul 25, 2014
@author: Mohammed Hamdy
'''

from PySide.QtGui import QLabel, QComboBox, QDoubleSpinBox, QStringListModel,\
  QDialog, QGridLayout, QPushButton, QWidget, QHBoxLayout, QRadioButton,\
  QSpinBox, QGroupBox, QFileDialog, QLineEdit
from PySide.QtCore import Qt, Signal
from notebook import MyEquityArray, Range
from util import getScriptDirectory

class BoardComboBox(QComboBox):
  def __init__(self, loadDiskBoards=True, parent=None):
    super(BoardComboBox, self).__init__(parent)
    self.setEditable(True)
    self.setInsertPolicy(self.InsertAtTop)
    self._boards = []
    self._board_texts = []
    if loadDiskBoards:
      board_objects = MyEquityArray.loadDiskBoards()
      self._boards = board_objects
      board_lists = [board.boardArray() for board in board_objects]
      board_texts = [','.join(board_list) for board_list in board_lists]
      self._board_texts = board_texts
      self.setModel(QStringListModel(board_texts))
    
  def createBoard(self):
    board_text = self.lineEdit().text()
    if not board_text or board_text in self._board_texts: return
    self.insertItem(0, board_text)
    self._board_texts.append(board_text)
    board_array = board_text.split(',')
    self._boards.append(MyEquityArray(board_array))
    
  def boards(self):
    return self._boards
  
class BoardComboCompound(QGroupBox):
  def __init__(self, parent=None):
    super(BoardComboCompound, self).__init__(parent)
    self.setTitle("Board")
    button_add_board = QPushButton("Add board")
    button_add_board.setMinimumWidth(100)
    button_add_board.clicked.connect(self._addBoard)
    self.combobox_board = BoardComboBox()
    self.combobox_board.setMinimumWidth(120)
    layout = QHBoxLayout()
    layout.addWidget(self.combobox_board)
    layout.addWidget(button_add_board)
    self.setLayout(layout)
    
  def _addBoard(self):
    self.combobox_board.createBoard()
  
class StackSizeCompound(QGroupBox):
  def __init__(self, parent=None):
    super(StackSizeCompound, self).__init__(parent)
    self.setTitle("Stack size")
    self.spinbox_stacksize = QSpinBox()
    self.spinbox_stacksize.setMaximum(9999)
    self.spinbox_stacksize.setMinimumWidth(100)
    layout = QHBoxLayout()
    layout.addWidget(self.spinbox_stacksize)
    self.setLayout(layout)
    
class DoFPCompound(QGroupBox):
  def __init__(self, parent=None):
    super(DoFPCompound, self).__init__(parent)
    self.setTitle("doFP")
    self.button_execute = QPushButton("Execute ...")
    self.spinbox_iterations = QSpinBox()
    self.spinbox_iterations.setMaximum(9999)
    self.spinbox_iterations.setValue(200)
    self.spinbox_iterations.setToolTip("No. iterations")
    layout = QHBoxLayout()
    layout.addWidget(self.spinbox_iterations)
    layout.addWidget(self.button_execute)
    self.setLayout(layout)
  
class BetAmountSpinBox(QDoubleSpinBox):
  def __init__(self, previousBet=0, parent=None):
    super(BetAmountSpinBox, self).__init__(parent)
    self.setMaximum(999999999)
    
class HorizontalRadioGroup(QWidget):
  
  radio_checked = Signal(unicode)
  
  def __init__(self, radioStrings, checkedRadio='', parent=None):
    super(HorizontalRadioGroup, self).__init__(parent)
    self._radios = []
    layout = QHBoxLayout()
    for original_s in radioStrings:
      # radio buttons have have text for display and original text. they only differ for empty strings
      radiobutton = QRadioButton()
      radiobutton.setProperty("_original_value", original_s)
      radiobutton.clicked.connect(self._handleRadioClicked)
      display_s = original_s if original_s else "(empty)"
      radiobutton.setText(display_s)
      if original_s == checkedRadio:
        radiobutton.setChecked(True)
      self._radios.append(radiobutton)
      layout.addWidget(radiobutton)
    self.setLayout(layout)
      
  def getValue(self):
    for radiobtn in self._radios:
      if radiobtn.isChecked():
        return radiobtn.property("_original_value")
      
  def setCheckedCombo(self, comboValue):
    for radio in self._radios:
      if radio.property("_original_value") == comboValue:
        radio.setChecked(True)
        return
      
  def _handleRadioClicked(self, checked=False):
    # get the checked radio button and emit it
    for radio in self._radios:
      if radio.isChecked():
        self.radio_checked.emit(radio.text())
        return
      
class ActionRadioGroup(HorizontalRadioGroup):
  def __init__(self, checkedRadio='', parent=None):
    super(ActionRadioGroup, self).__init__(['', "Bet", "Check", "Fold", "Call", "Raise"], checkedRadio)
    
class PlayerRadioGroup(HorizontalRadioGroup):
  def __init__(self, checkedRadio='', parent=None):
    super(PlayerRadioGroup, self).__init__(['', "Nature", "Leaf", "SB", "BB"], checkedRadio)

class PointEditor(QDialog):
  
  def __init__(self, playerName='', sbChips=0, bbChips=0, action='', board=None, boardCombo=None,
               editMode=False, parent=None):
    super(PointEditor, self).__init__(parent)
    self._boards = boardCombo.boards() # boards is an array of MyEquityArray objects
    self._label_player = QLabel("Player")
    self._radiogroup_player = PlayerRadioGroup(playerName)
    self._label_sb_chips = QLabel("SB Chips")
    self._spinbox_sb_chips = BetAmountSpinBox()
    self._spinbox_sb_chips.setValue(sbChips)
    self._label_bb_chips = QLabel("BB Chips")
    self._spinbox_bb_chips = BetAmountSpinBox()
    self._spinbox_bb_chips.setValue(bbChips)
    label_board = QLabel("Choose board")
    self.combobox_board = QComboBox()
    self.combobox_board.setModel(boardCombo.model())
    if board is not None:
      self.combobox_board.setCurrentIndex(self._getComboItems(self.combobox_board).index(board.originalBoard()))
    self._action_label = QLabel("Parent action")
    if editMode:
      button_ok_text = "Edit point"
    else:
      button_ok_text = "Add point"
    button_ok = QPushButton(button_ok_text)
    button_cancel = QPushButton("Cancel")
    button_ok.clicked.connect(self.accept)
    button_cancel.clicked.connect(self.reject)
    self._radiogroup_action = ActionRadioGroup(action)
    layout = QGridLayout()
    row = 0; col = 0;
    layout.addWidget(self._label_player, row, col)
    col += 1
    layout.addWidget(self._radiogroup_player, row, col)
    row += 1; col = 0;
    layout.addWidget(self._action_label, row, col)
    col += 1
    layout.addWidget(self._radiogroup_action, row, col)
    row += 1; col = 0;
    layout.addWidget(self._label_sb_chips, row, col)
    col += 1
    layout.addWidget(self._spinbox_sb_chips, row, col)
    row += 1; col = 0;
    layout.addWidget(self._label_bb_chips, row, col)
    col += 1;
    layout.addWidget(self._spinbox_bb_chips, row, col)
    row += 1; col = 0;
    layout.addWidget(label_board, row, col)
    col += 1
    layout.addWidget(self.combobox_board, row, col)
    row += 1; col = 0;
    layout.addWidget(button_ok, row, col)
    col += 1
    layout.addWidget(button_cancel, row, col)
    self.setModal(True)
    self.setMinimumWidth(300)
    if editMode:
      title = "Edit Point Information"
    else:
      title = "Enter Point Information"
    self.setWindowTitle(title)
    self.setLayout(layout)
    
  def playerName(self):
    return self._radiogroup_player.getValue()
  
  def setPlayerName(self, playerName):
    self._radiogroup_player.setCheckedCombo(playerName)
  
  def sbChips(self):
    return self._spinbox_sb_chips.value()
  
  def setSbChips(self, sbChips):
    self._spinbox_sb_chips.setValue(sbChips)
  
  def bbChips(self):
    return self._spinbox_bb_chips.value()
  
  def setBbChips(self, bbChips):
    self._spinbox_bb_chips.setValue(bbChips)
    
  def board(self):
    if len(self._boards):
      return self._boards[self.combobox_board.currentIndex()]
    else:
      return None
  
  def setBoard(self, board):
    self.combobox_board.setCurrentIndex(self._boards.index(board))
    
  def playAction(self):
    return self._radiogroup_action.getValue()
  
  def setPlayAction(self, action):
    self._radiogroup_action.setCheckedCombo(action)
    
  def _getComboItems(self, combobox):
    items = []
    for i in range(combobox.count()):
      items.append(combobox.itemData(i, Qt.DisplayRole))
      
    return items
    
class TreeSaveDialog(QFileDialog):
  def __init__(self, parent=None):
    super(TreeSaveDialog, self).__init__(parent)
    self.setFileMode(QFileDialog.AnyFile)
    self.setDirectory(getScriptDirectory())
    self.setNameFilter("Tree Files (*.tree)")
    self.setWindowTitle("Select save location")
    
class TreeLoadDialog(QFileDialog):
  def __init__(self, parent=None):
    super(TreeLoadDialog, self).__init__(parent)
    self.setDirectory(getScriptDirectory())
    self.setNameFilter("Tree files (*.tree)")
    self.setFileMode(QFileDialog.ExistingFile)
    self.setWindowTitle("Select a tree to load")
    
class SetAllFracsSpinBox(QDoubleSpinBox):
  """A normal spinbox. created for consistency"""
  def __init__(self, default=1.0, parent=None):
    super(SetAllFracsSpinBox, self).__init__(parent)
    self.setMaximum(9999)
    self.setValue(default)
    
class SetRangeStringCompound(QWidget):
  def __init__(self, parent=None):
    super(SetRangeStringCompound, self).__init__(parent)
    label_string = QLabel("Range string")
    self.lineedit_string = QLineEdit()
    self.lineedit_string.setMinimumWidth(100)
    label_value = QLabel("Value")
    self.spinbox_value = QDoubleSpinBox()
    self.spinbox_value.setMaximum(9999)
    self.spinbox_value.setValue(1.0)
    row = 0 ; col = 0;
    layout = QGridLayout()
    layout.addWidget(label_string, row, col)
    col += 1
    layout.addWidget(self.lineedit_string, row, col)
    row += 1; col = 0;
    layout.addWidget(label_value, row, col)
    col += 1
    layout.addWidget(self.spinbox_value, row, col)
    self.setLayout(layout)
    
class SetToTopCompound(QWidget):
  def __init__(self, boardCombo=None, parent=None):
    super(SetToTopCompound, self).__init__(parent)
    label_fraction = QLabel("Fraction")
    self.spinbox_fraction = QDoubleSpinBox()
    label_board = QLabel("Board")
    self.combobox_board = QComboBox()
    self._boards = []
    if boardCombo is not None:
      self.combobox_board.setModel(boardCombo.model())
      self._boards = boardCombo.boards()
    layout = QGridLayout()
    row = 0; col = 0
    layout.addWidget(label_fraction, row, col)
    col += 1
    layout.addWidget(self.spinbox_fraction, row, col)
    row += 1; col = 0;
    layout.addWidget(label_board, row, col)
    col += 1
    layout.addWidget(self.combobox_board, row, col)
    self.setLayout(layout)
  
class DoFPParametersDialog(QDialog):
  
  AFTER_CONSTRUCTION_ALLFRAC = 1
  AFTER_CONSTRUCTION_RANGESTRING = 2
  AFTER_CONSTRUCTION_TOTOP = 3
  
  def __init__(self, rangeConstructor=1.0,  boardCombo=None, title="Enter first range arguments", parent=None):
    super(DoFPParametersDialog, self).__init__(parent)
    self._after_method = 2
    self._board_combo = boardCombo
    label_constructor = QLabel("Constructor argument <b>(initFrac)</b>")
    self._spinbox_constructor = QSpinBox()
    self._spinbox_constructor.setMaximum(9999)
    self._spinbox_constructor.setValue(rangeConstructor)
    label_after_construction = QLabel("After construction method")
    self._radiogroup_methods = HorizontalRadioGroup(["setRangeString()", "setAllFracs()", "setToTop()"])
    self._radiogroup_methods.radio_checked.connect(self._updateLayout)
    self._radiogroup_methods._radios[0].setChecked(True) # dunno why it's not checked by default
    label_method_args = QLabel("Method arguments")
    self._widget_method_args = SetRangeStringCompound()
    button_ok = QPushButton("Ok")
    button_ok.clicked.connect(self.accept)
    button_cancel = QPushButton("Cancel")
    button_cancel.clicked.connect(self.reject)
    layout = QGridLayout()
    row = 0; col = 0;
    layout.addWidget(label_constructor, row, col)
    col += 1
    layout.addWidget(self._spinbox_constructor, row, col)
    row += 1; col = 0;
    layout.addWidget(label_after_construction, row, col)
    col += 1
    layout.addWidget(self._radiogroup_methods)
    row += 1; col = 0;
    layout.addWidget(label_method_args, row, col)
    col += 1
    self._update_pos = (row, col)
    layout.addWidget(self._widget_method_args, row, col)
    row += 1; col = 0
    layout.addWidget(button_ok, row, col)
    col += 1
    layout.addWidget(button_cancel, row, col)
    self.setLayout(layout)
    self.setWindowTitle(title)
    
  def _updateLayout(self, radioString):
    self._widget_method_args.setParent(None)
    self.layout().removeWidget(self._widget_method_args)
    if radioString == "setRangeString()":
      self._after_method = self.AFTER_CONSTRUCTION_RANGESTRING
      self._widget_method_args = SetRangeStringCompound()
    elif radioString == "setAllFracs()":
      self._after_method = self.AFTER_CONSTRUCTION_ALLFRAC
      self._widget_method_args = SetAllFracsSpinBox()
    elif radioString == "setToTop()":
      self._after_method = self.AFTER_CONSTRUCTION_TOTOP
      self._widget_method_args = SetToTopCompound(self._board_combo)
    self.layout().update()
    self.layout().addWidget(self._widget_method_args, self._update_pos[0], self._update_pos[1])
    
  def getRange(self):
    # construct a range object and return it
    r = Range(self._spinbox_constructor.value())
    if self._after_method == self.AFTER_CONSTRUCTION_ALLFRAC:
      r.setAllFracs(self._widget_method_args.value())
    elif self._after_method == self.AFTER_CONSTRUCTION_RANGESTRING:
      r.setRangeString(self._widget_method_args.lineedit_string.text(), 
                       self._widget_method_args.spinbox_value.value())
    elif self._after_method == self.AFTER_CONSTRUCTION_TOTOP:
      r.setToTop(self._widget_method_args.spinbox_fraction.value(), 
                 self._board_combo.boards()[self._widget_method_args.combobox_board.currentIndex()])
    return r