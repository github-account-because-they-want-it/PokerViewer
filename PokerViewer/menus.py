'''
Created on Jul 27, 2014
@author: Mohammed Hamdy
'''

from PySide.QtGui import QAction, QMenu

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
    
class PokerTreeMenu(QMenu):
  def __init__(self, parent=None):
    super(PokerTreeMenu, self).__init__(parent)
    self.action_add_point = AddPointAction()
    self.action_add_nested_point = AddNestedPointAction()
    self.action_delete_point = DeletePointAction()
    self.addAction(self.action_add_point)
    self.addAction(self.action_add_nested_point)
    self.addAction(self.action_delete_point)