'''
Created on Jul 25, 2014
@author: Mohammed Hamdy
'''
from PySide.QtGui import QTreeView, QStyledItemDelegate, QWidget, \
  QGridLayout, QApplication,  QDialog, QItemSelection, QMainWindow,\
  QHBoxLayout
from PySide.QtCore import QAbstractItemModel, Qt, QModelIndex, Signal
from lib.widgets import PointEditor, BoardComboCompound, StackSizeCompound, DoFPCompound, TreeSaveDialog,\
                    TreeLoadDialog, DoFPParametersDialog
from lib.notebook import Tree, DecPt, pe, doFP, Range
from lib.menus import PokerTreeMenu, FileMenuBar
from lib.chart import ChartTableView
from lib.util import TreeLoadSaveHandler
import sys, copy

class DecisionPointTreeItem(object):
  
  def __init__(self, pointIndex, player='', sbChips=0, bbChips=0, board=None, action='', 
               parentDec=None, newCardFreq=1.0):
    self._index = pointIndex
    self._player = player
    self._sb_chips = sbChips
    self._bb_chips = bbChips
    self._board = board
    self._action = action
    self._parent = parentDec
    self._new_card_freq = newCardFreq
    self._children = []
    if not parentDec:
      self._children.append(RootDecisionPoint(-1, parentDec=self)) 
    self._dec_pt = None
    self._updateDecPt()
    
  def columnCount(self):
    return 1
  
  def rowCount(self):
    return len(self._children)
  
  def child(self, index):
    if index < len(self._children):
      return self._children[index]
    
  def appendChild(self, child):
    self._children.append(child)
    
  def removeChild(self, child):
    self._children.remove(child)
    
  def childNumber(self):
    # returns the index of self within parent
    if self._parent:
      return self._parent._children.index(self)
    else: return 0
    
  def data(self):
    display_string = "{} {} ({}, {}) {}".format(self._player, self._action, 
                                                self._sb_chips, self._bb_chips, str(self._board))
    return display_string
  
  def setData(self, player='', sbChips=0, bbChips=0, board=None, action=''):
    if player: self._player = player
    if sbChips: self._sb_chips = sbChips
    if bbChips: self._bb_chips = bbChips
    if board: self._board = board
    if action: self._action = action
    self._updateDecPt()
  
  def parent(self):
    return self._parent
  
  def children(self):
    return self._children
  
  def player(self):
    return self._player
  
  def sbChips(self):
    return self._sb_chips
  
  def bbChips(self):
    return self._bb_chips
  
  def action(self):
    return self._action
  
  def board(self):
    return self._board
  
  def index(self):
    return self._index
  
  def decPt(self):
    return self._dec_pt
  
  def _updateDecPt(self):
    self._dec_pt = DecPt(self._player, self._sb_chips, self._bb_chips, self._board,
                         self._action.lower(), self._new_card_freq)
  
  def __str__(self):
    return "<DecisionPointTreeItem %s at {:0x}>".format(self.data(), id(self))
  
class RootDecisionPoint(DecisionPointTreeItem):
  
  def data(self):
    return "Game Root"
  
class DecisionTreeModel(QAbstractItemModel):
  
  point_edited = Signal(DecisionPointTreeItem, DecisionPointTreeItem) # point before and after being edited
  
  def __init__(self, rootItem=None, parent=None):
    super(DecisionTreeModel, self).__init__(parent)
    self._point_count = 0
    if rootItem: self._root_item = rootItem
    else:
      self._root_item = DecisionPointTreeItem(-1)
    self._board = []
  
  def headerData(self, section, orientation, role):
    if role == Qt.DisplayRole:
      if orientation == Qt.Vertical:
        return "Round #{}".format(section)
      
  def rowCount(self, parentIndex):
    item = self._getItemAt(parentIndex)
    return item.rowCount()
  
  def columnCount(self, parentIndex):
    return self._root_item.columnCount()
  
  def data(self, index, role):
    if role == Qt.DisplayRole:
      item = self._getItemAt(index)
      return item.data()
    
  def setData(self, index, value, role):
    if role == Qt.EditRole:
      item = index.internalPointer()
      item_copy = copy.copy(item) # to keep track of the original
      # check if boards differ between old and new items. if so, propagate the change to children
      original_board = item.board()
      new_board = value["board"]
      if original_board != new_board:
        self._propagateBoardToChildrenOf(item, new_board)
      item.setData(value["player"], value["sbchips"], 
                   value["bbchips"], value["board"], action=value["action"])
      self.dataChanged.emit(index, index)
      self.point_edited.emit(item_copy, item)
      return True
    return False
  
  def index(self, row, column, parentIndex):
    # I think this method is here to pack data into different indexes
    if not self.hasIndex(row, column, parentIndex):
      return QModelIndex()
    # get the parent item from the index. 
    if not parentIndex.isValid(): 
      parent_item = self._root_item
    else:
      parent_item = parentIndex.internalPointer()
    child = parent_item.child(row)
    if child:
      return self.createIndex(row, column, child)
    else:
      return QModelIndex()
    
  def parent(self, index):
    # this method is the reverse of index(). It returns indexes to parents, not to children
    if not index.isValid():
      return QModelIndex()
    item = self._getItemAt(index)
    parent = item.parent()
    if parent is self._root_item:
      return QModelIndex()
    else:
      return self.createIndex(parent.childNumber(), 0, parent)
    
  def flags(self, index):
    if index.isValid():
      return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
    
  def addPoint(self, index, pointDict):
    # add a new point at the same level as index
    selected_item = index.internalPointer()
    if isinstance(selected_item, RootDecisionPoint): # cannot add points at the same level to root
      return
    parent = selected_item.parent()
    child_count = parent.rowCount()
    self.beginInsertRows(index.parent(), child_count, child_count)
    parent.appendChild(self._decisionPointFromDict(pointDict, parent))
    self.endInsertRows()
  
  def addNestedPoint(self, index, pointDict):
    # add a new point as a child to index
    selected_item = index.internalPointer()
    child_count = selected_item.rowCount()
    self.beginInsertRows(index, child_count, child_count)
    selected_item.appendChild(self._decisionPointFromDict(pointDict, selected_item))
    self.endInsertRows()
    
  def deletePoint(self, pointIndex):
    item = pointIndex.internalPointer()
    parent = item.parent()
    child_row = item.childNumber()
    self.beginRemoveRows(pointIndex.parent(), child_row, child_row)
    parent.removeChild(item)
    self.endRemoveRows()
    
  def _getItemAt(self, index):
    if index.isValid():
      item = index.internalPointer()
      if item:
        return item
    else:
      return self._root_item
    
  def _decisionPointFromDict(self, pointDict, parent):
    dec_pt = DecisionPointTreeItem(self._point_count, pointDict["player"], pointDict["sbchips"], 
                                             pointDict["bbchips"], action=pointDict["action"],
                                             board=pointDict["board"], parentDec=parent)
    self._point_count += 1
    return dec_pt
  
  def _propagateBoardToChildrenOf(self, item, newBoard):
    item_children = item.children()
    if len(item_children) == 0:
      return
    else:
      for child in item_children:
        child_copy = copy.copy(child)
        child.setData(board=newBoard)
        self.point_edited.emit(child_copy, child)
        self._propagateBoardToChildrenOf(child, newBoard)
    
class PointEditorItemDelegate(QStyledItemDelegate):
  
  def __init__(self, boardCombo, parent=None):
    super(PointEditorItemDelegate, self).__init__(parent)
    self._board_combo = boardCombo
  
  def createEditor(self, parentWidget, styleOption, index):
    editor = PointEditor(editMode=True, boardCombo=self._board_combo, parent=self.parent())
    return editor
  
  def setEditorData(self, editor, index):
    item_in_edit = index.internalPointer()
    editor.setPlayerName(item_in_edit.player())
    editor.setSbChips(item_in_edit.sbChips())
    editor.setBbChips(item_in_edit.bbChips())
    editor.setPlayAction(item_in_edit.action())
    editor.setBoard(item_in_edit.board())
    return True
  
  def setModelData(self, editor, model, index):
    point_dict = {}
    point_dict["player"] = editor.playerName()
    point_dict["sbchips"] = editor.sbChips()
    point_dict["bbchips"] = editor.bbChips()
    point_dict["action"] = editor.playAction()
    point_dict["board"] = editor.board()
    model.setData(index, point_dict, Qt.EditRole)
    self.commitData.emit(editor)
  
  def updateEditorGeometry(self, editor, styleOption, index):
    return None
    
class GameTreeView(QTreeView):
  """
  Represents the decision tree and updates a Tree object internally
  """
  
  tree_updated = Signal()
  
  def __init__(self, boardCombo, treeStackSize=500, parent=None):
    super(GameTreeView, self).__init__(parent)
    self.setModel(DecisionTreeModel())
    self._stacksize = treeStackSize
    self._tree = None
    self._connectModel()
    item_delegate = PointEditorItemDelegate(boardCombo)
    self.setItemDelegate(item_delegate)
    
  def _connectModel(self):
    self.model().rowsInserted.connect(self._updateTreeInsert)
    self.model().rowsRemoved.connect(self._updateTreeRemove)
    self.model().point_edited.connect(self._updateTreeEdit)
    
  def setStackSize(self, stackSize):
    self._stacksize = stackSize
    
  def treeObject(self):
    return self._tree
    
  def setTreeObject(self, treeObject):
    self._tree = treeObject
    
  def rootItem(self):
    return self.model()._root_item
    
  def setRootItem(self, rootItem):
    model = DecisionTreeModel(rootItem)
    self.setModel(model)
    self._connectModel()
    
  def _updateTreeInsert(self, parentIndex, start, end):
    # start should be the same as end because we are inserting single rows
    self.setExpanded(parentIndex, True)
    parent_item = parentIndex.internalPointer()
    inserted_item = parent_item.child(start)
    if not isinstance(parent_item, RootDecisionPoint):
      parent_decpt = parent_item.decPt()
    decpt = inserted_item.decPt()
    if self._tree is None:
      self._tree = Tree(self._stacksize, decpt)
    else:
      self._tree.addDecPt(decpt, parent_decpt)
    self.tree_updated.emit()
    
  def _updateTreeRemove(self, parentIndex, start, end):
    parent_item = parentIndex.internalPointer()
    removed_item = parent_item.child(start)
    decpt = removed_item.decPt()
    self._tree.removeDecPt(decpt)
    self.tree_updated.emit()
    
  def _updateTreeEdit(self, oldPoint, newPoint):
    old_decpt = oldPoint.decPt()
    new_decpt = newPoint.decPt()
    self._tree.updateDecPt(old_decpt, new_decpt)
    self.tree_updated.emit()
    
class TreeContainer(QWidget):
  
  range_changed = Signal(Range)
  tree_loaded = Signal()
  
  def __init__(self, parent=None):
    super(TreeContainer, self).__init__(parent)
    self._soln = None
    self.tree_loaded.connect(self._handleTreeLoaded)
    self._stacksize_compound = StackSizeCompound()
    self.combobox_compound = BoardComboCompound()
    self.dofp_compound = DoFPCompound()
    self.treeview_game = GameTreeView(self.combobox_compound.combobox_board)
    self.treeview_game.tree_updated.connect(self._handleTreeUpdated)
    self._stacksize_compound.spinbox_stacksize.setValue(500)
    self._stacksize_compound.spinbox_stacksize.valueChanged.connect(self._handleSpinboxChange)
    self.dofp_compound.button_execute.setEnabled(False)
    self.dofp_compound.button_execute.clicked.connect(self._executeFP)
    selection_model = self.treeview_game.selectionModel()
    selection_model.selectionChanged.connect(self._handleSelectionChanged)
    layout = QGridLayout()
    control_layout = QHBoxLayout()
    control_layout.addWidget(self._stacksize_compound)
    control_layout.addWidget(self.combobox_compound)
    control_layout.addWidget(self.dofp_compound)
    control_layout.addStretch()
    row = 0; col = 0;
    layout.addLayout(control_layout, row, col, 1, 2)
    row += 1; col = 0
    layout.addWidget(self.treeview_game, row, col, 1, 2)
    self.setLayout(layout)
    self.setWindowTitle("Game Tree Viewer")
    self._setupContextMenu()
    
  def _setupContextMenu(self):
    self._context_menu = PokerTreeMenu(self)
    self._context_menu.action_add_point.triggered.connect(self._addPoint)
    self._context_menu.action_add_nested_point.triggered.connect(self._addNestedPoint)
    self._context_menu.action_delete_point.triggered.connect(self._deletePoint)
    
  def contextMenuEvent(self, cme):
    mouse_pos = cme.globalPos()
    self._context_menu.popup(mouse_pos)
    
  def _handleSelectionChanged(self, selectedIndexes, deselectedIndexes):
    if isinstance(selectedIndexes, QItemSelection):
      selectedIndexes = selectedIndexes.indexes()
    if len(selectedIndexes) > 0:
      selected = selectedIndexes[0]
      item = selected.internalPointer()
      if isinstance(item, RootDecisionPoint):
        self._context_menu.action_add_point.setEnabled(False)
      else:
        self._context_menu.action_add_point.setEnabled(True)
      self._context_menu.action_add_nested_point.setEnabled(True)
      if self._soln is not None:
        selected_range = self._soln.ranges[item.index()]
        self.range_changed.emit(selected_range)
    else:
      self._context_menu.action_add_point.setEnabled(False)
      self._context_menu.action_add_nested_point.setEnabled(False)
      self._context_menu.action_delete_point.setEnabled(False)
    
      
  def _getPointParams(self):
    # prepopulate the editor from the currently selected index
    selected_indexes = self._getSelectedIndexes()
    selected_index = selected_indexes[0]
    selected_item = selected_index.internalPointer()
    point_dialog = PointEditor(selected_item.player(), selected_item.sbChips(),
                               selected_item.bbChips(), selected_item.action(),
                               selected_item.board(),
                               boardCombo=self.combobox_compound.combobox_board, parent=self)
    result = point_dialog.exec_()
    if result == QDialog.Accepted:
      result_dict = {}
      result_dict["player"] = point_dialog.playerName()
      result_dict["sbchips"] = point_dialog.sbChips()
      result_dict["bbchips"] = point_dialog.bbChips()
      result_dict["action"] = point_dialog.playAction()
      result_dict["board"] = point_dialog.board()
      return result_dict
    else:
      return None
    
  def _addPoint(self):
    point_params = self._getPointParams()
    selected_indexes = self._getSelectedIndexes()
    selected_point_index = selected_indexes[0]
    if point_params is None:
      return
    model = self.treeview_game.model()
    model.addPoint(selected_point_index, point_params)
    self._recheckMenus() # it seems pyside has a bug when updating the tree the deselection is not detected, invalidating the buttons
    
  def _addNestedPoint(self):
    point_params = self._getPointParams()
    selected_indexes = self._getSelectedIndexes()
    if point_params is None:
      return
    model = self.treeview_game.model()
    model.addNestedPoint(selected_indexes[0], point_params)
    
  def _deletePoint(self):
    selected_point_index = self._getSelectedIndexes()[0]
    model = self.treeview_game.model()
    model.deletePoint(selected_point_index)
    
  def _getSelectedIndexes(self):
    selection_model = self.treeview_game.selectionModel()
    selected_indexes = selection_model.selectedIndexes()
    return selected_indexes
  
  def _recheckMenus(self):
    selected_indexes = self._getSelectedIndexes()
    self._handleSelectionChanged(selected_indexes, [])
    
  def _handleSpinboxChange(self):
    self.treeview_game.setStackSize(self._stacksize_compound.spinbox_stacksize.value())
    
  def _executeFP(self):
    tree = self.treeview_game._tree
    dialog_titles = ["Enter first range arguments", "Enter second range arguments"]
    dialogs = []
    for i in range(2):
      fp_params_dialog = DoFPParametersDialog(boardCombo=self.combobox_compound.combobox_board, 
                                              title=dialog_titles[i])
      dialogs.append(fp_params_dialog)
      accepted = fp_params_dialog.exec_()
      if not accepted:
        break
    else: # both accepted
      range1 = dialogs[0].getRange()
      range2 = dialogs[1].getRange()
      self._soln = doFP(tree, self.dofp_compound.spinbox_iterations.value(), range1, range2)
      self.dofp_compound.button_execute.setEnabled(False)
    
  def _handleTreeUpdated(self):
    self.dofp_compound.button_execute.setEnabled(True)
    
  def _handleTreeLoaded(self):
    # the tree loading with its model recreation seems to break the selection model
    selection_model = self.treeview_game.selectionModel()
    selection_model.selectionChanged.connect(self._handleSelectionChanged)
    self.treeview_game.expandAll()
    
   
class MainWindow(QMainWindow):
  def __init__(self):
    super(MainWindow, self).__init__()
    self._tree_container = TreeContainer()
    self._tableview_chart = ChartTableView()
    self._tree_container.range_changed.connect(self._tableview_chart.selected_range_changed)
    central_widget = QWidget()
    layout = QGridLayout()
    row = 0; col = 0
    layout.addWidget(self._tree_container, row, col, 1, 5)
    row += 1
    layout.addWidget(self._tableview_chart, row, col, 1, 5)
    central_widget.setLayout(layout)
    self.setCentralWidget(central_widget)
    self._setupMenuBar()
    self.statusBar()
    self.setWindowTitle("Poker Viewer")
    
  def _setupMenuBar(self):
    self._menubar = FileMenuBar()
    self.setMenuBar(self._menubar)
    self._menubar.file_menu.action_save_tree.triggered.connect(self._saveTree)
    self._menubar.file_menu.action_load_tree.triggered.connect(self._loadTree)
    
  def _saveTree(self):
    save_dialog = TreeSaveDialog(self)
    accepted = save_dialog.exec_()
    if accepted:
      filename = save_dialog.selectedFiles()[0]
      root_item = self._tree_container.treeview_game.rootItem()
      tree_object = self._tree_container.treeview_game.treeObject()
      TreeLoadSaveHandler.saveTree(filename, root_item, tree_object)
      self.statusBar().showMessage("Tree saved successfully", 5000)
  
  def _loadTree(self):
    load_dialog = TreeLoadDialog(self)
    accepted = load_dialog.exec_()
    if accepted:
      filename = load_dialog.selectedFiles()[0]
      root_item, tree_object = TreeLoadSaveHandler.loadTree(filename)
      self._tree_container.treeview_game.setRootItem(root_item)
      self._tree_container.treeview_game.setTreeObject(tree_object)
      self._tree_container.dofp_compound.button_execute.setEnabled(True)
      self._tree_container.tree_loaded.emit()
      self.statusBar().showMessage("Tree loaded", 5000)
  
if __name__ == "__main__":
  app = QApplication(sys.argv)
  main = MainWindow()
  main.show()
  sys.exit(app.exec_())
