'''
Created on Jul 27, 2014
@author: Mohammed Hamdy
'''

from PySide.QtGui import QAction, QMenu, QKeySequence, QMenuBar


class AddPointAction(QAction):
  def __init__(self, parent=None):
    super(AddPointAction, self).__init__(parent)
    self.setText("Add point")
    self.setToolTip("Adds a point at the same level as this point")
    
class AddNestedPointAction(QAction):
  def __init__(self, parent=None):
    super(AddNestedPointAction, self).__init__(parent)
    self.setText("Add nested point")
    self.setToolTip("Adds a point inside this point")
    
class DeletePointAction(QAction):
  def __init__(self, parent=None):
    super(DeletePointAction, self).__init__(parent)
    self.setText("Delete point")
    self.setToolTip("Deletes this point and all nested points")
    
class SaveTreeAction(QAction):
  def __init__(self, parent=None):
    super(SaveTreeAction, self).__init__(parent)
    self.setText("Save tree ...")
    self.setShortcut(QKeySequence.Save)
    
class LoadTreeAction(QAction):
  def __init__(self, parent=None):
    super(LoadTreeAction, self).__init__(parent)
    self.setText("Load tree ...")
    self.setShortcut("Ctrl+L")
  
class PokerTreeMenu(QMenu):
  def __init__(self, parent=None):
    super(PokerTreeMenu, self).__init__(parent)
    self.action_add_point = AddPointAction()
    self.action_add_nested_point = AddNestedPointAction()
    self.action_delete_point = DeletePointAction()
    self.addAction(self.action_add_point)
    self.addAction(self.action_add_nested_point)
    self.addAction(self.action_delete_point)
    
class FileMenu(QMenu):
  def __init__(self, parent=None):
    super(FileMenu, self).__init__("&File", parent)
    self.action_save_tree = SaveTreeAction()
    self.action_load_tree = LoadTreeAction()
    self.addAction(self.action_save_tree)
    self.addAction(self.action_load_tree)
    
class FileMenuBar(QMenuBar):
  def __init__(self, parent=None):
    super(FileMenuBar, self).__init__(parent)
    self.file_menu = FileMenu()
    self.addMenu(self.file_menu)