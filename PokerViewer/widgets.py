'''
Created on Jul 25, 2014
@author: Mohammed Hamdy
'''

from PySide.QtGui import QLabel, QComboBox, QDoubleSpinBox, QStringListModel,\
  QDialog, QGridLayout, QPushButton, QWidget, QHBoxLayout, QRadioButton,\
  QSpinBox, QGroupBox
from PySide.QtCore import Qt
from notebook import MyEquityArray

class BoardComboBox(QComboBox):
  def __init__(self, parent=None):
    super(BoardComboBox, self).__init__(parent)
    self.setEditable(True)
    self.setInsertPolicy(self.InsertAtTop)
    self._boards = []
    self._board_texts = []
    
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
    self.combobox_board.setMinimumWidth(100)
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
    self.button_execute = QPushButton("Execute")
    self.spinbox_iterations = QSpinBox()
    self.spinbox_iterations.setMaximum(9999)
    self.spinbox_iterations.setValue(200)
    layout = QHBoxLayout()
    layout.addWidget(self.spinbox_iterations)
    layout.addWidget(self.button_execute)
    self.setLayout(layout)
  
class BetAmountSpinBox(QDoubleSpinBox):
  def __init__(self, previousBet=0, parent=None):
    super(BetAmountSpinBox, self).__init__(parent)
    self.setMaximum(999999999)
    
class HorizontalRadioGroup(QWidget):
  def __init__(self, radioStrings, checkedRadio='', parent=None):
    super(HorizontalRadioGroup, self).__init__(parent)
    self._radios = []
    layout = QHBoxLayout()
    for original_s in radioStrings:
      # radio buttons have have text for display and original text. they only differ for empty strings
      radiobutton = QRadioButton()
      radiobutton.setProperty("_original_value", original_s)
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
      return self._boards[self.combobox_board.currentIndex() - 1]
    else:
      return None
  
  def setBoard(self, board):
    self.combobox_board.setCurrentIndex(self._boards.index(board))
    
  def playAction(self):
    return self._radiogroup_action.getValue()
  
  def setPlayAction(self, action):
    self._radiogroup_action.setCheckedCombo(action)
    
  def _getComboItems(self, combobox):
    model = combobox.model()
    items = []
    for i in range(combobox.count()):
      items.append(model.item(i).data(Qt.DisplayRole))
      
    return items
    