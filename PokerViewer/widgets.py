'''
Created on Jul 25, 2014
@author: Mohammed Hamdy
'''

from PySide.QtGui import QLabel, QComboBox, QDoubleSpinBox, QStringListModel,\
  QDialog, QGridLayout, QPushButton
from PySide.QtCore import Qt
from notebook import MyEquityArray

class PlayerNameComboBox(QComboBox):
  def __init__(self, parent=None):
    super(PlayerNameComboBox, self).__init__(parent)
    self.setModel(QStringListModel(['', "Nature", "Leaf", "SB", "BB"]))
    
class BoardComboBox(QComboBox):
  def __init__(self, parent=None):
    super(BoardComboBox, self).__init__(parent)
    self.setEditable(True)
    self._boards = []
    self._board_texts = []
    self.lineEdit().editingFinished.connect(self._createBoard)
    
  def _createBoard(self):
    board_text = self.lineEdit().text()
    if not board_text or board_text in self._board_texts: return
    self._board_texts.append(board_text)
    board_array = board_text.split(',')
    self._boards.append(MyEquityArray(board_array))
    
  def boards(self):
    return self._boards
  
  
class BetAmountSpinBox(QDoubleSpinBox):
  def __init__(self, previousBet=0, parent=None):
    super(BetAmountSpinBox, self).__init__(parent)
    self.setMaximum(999999999)
    
class ActionComboBox(QComboBox):
  def __init__(self, parent=None):
    super(ActionComboBox, self).__init__(parent)
    self.setModel(QStringListModel(['', "Bet", "Check", "Fold", "Call", "Raise"]))
    
class PointEditor(QDialog):
  
  def __init__(self, playerName='', sbChips=0, bbChips=0, action='', board=None, boardCombo=None,
               editMode=False, parent=None):
    super(PointEditor, self).__init__(parent)
    self._boards = boardCombo.boards() # boards is an array of EquityArray objects
    self._label_player = QLabel("Player")
    self._combobox_player = PlayerNameComboBox()
    if playerName:
      self._combobox_player.setCurrentIndex(self._getComboItems(self._combobox_player).index(playerName))
    self._label_sb_chips = QLabel("SB Chips")
    self._spinbox_sb_chips = BetAmountSpinBox()
    self._spinbox_sb_chips.setValue(sbChips)
    self._label_bb_chips = QLabel("BB Chips")
    self._spinbox_bb_chips = BetAmountSpinBox()
    self._spinbox_bb_chips.setValue(bbChips)
    label_board = QLabel("Choose board")
    self._combobox_board = QComboBox()
    self._combobox_board.setModel(boardCombo.model())
    if board is not None:
      self._combobox_board.setCurrentIndex(self._getComboItems(self._combobox_board).index(board.originalBoard()))
    self._action_label = QLabel("Parent action")
    if editMode:
      button_ok_text = "Edit point"
    else:
      button_ok_text = "Add point"
    button_ok = QPushButton(button_ok_text)
    button_cancel = QPushButton("Cancel")
    button_ok.clicked.connect(self.accept)
    button_cancel.clicked.connect(self.reject)
    self._combobox_action = ActionComboBox()
    if action:
      self._combobox_action.setCurrentIndex(self._getComboItems(self._combobox_action).index(action))
    layout = QGridLayout()
    row = 0; col = 0;
    layout.addWidget(self._label_player, row, col)
    col += 1
    layout.addWidget(self._combobox_player, row, col)
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
    layout.addWidget(self._combobox_board, row, col)
    row += 1; col = 0;
    layout.addWidget(self._action_label, row, col)
    col += 1
    layout.addWidget(self._combobox_action, row, col)
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
    return self._combobox_player.currentText()
  
  def setPlayerName(self, playerName):
    self._combobox_player.setCurrentIndex(self._getComboItems(self._combobox_player).index(playerName))
  
  def sbChips(self):
    return self._spinbox_sb_chips.value()
  
  def setSbChips(self, sbChips):
    self._spinbox_sb_chips.setValue(sbChips)
  
  def bbChips(self):
    return self._spinbox_bb_chips.value()
  
  def setBbChips(self, bbChips):
    self._spinbox_bb_chips.setValue(bbChips)
    
  def board(self):
    return self._boards[self._combobox_board.currentIndex()]
  
  def setBoard(self, board):
    self._combobox_board.setCurrentIndex(self._boards.index(board.originalBoard()))
    
  def playAction(self):
    return self._combobox_action.currentText()
  
  def setPlayAction(self, action):
    self._combobox_action.setCurrentIndex(self._getComboItems(self._combobox_action).index(action))
    
  def _getComboItems(self, combobox):
    items = []
    for item_i in range(combobox.count()):
      items.append(combobox.itemData(item_i, Qt.DisplayRole))
    return items