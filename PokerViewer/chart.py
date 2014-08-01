'''
Created on Jul 28, 2014
@author: Mohammed Hamdy
'''

from PySide.QtGui import QTableView, QBrush, QColor
from PySide.QtCore import QAbstractTableModel, Qt, Signal
from notebook import Range

class ChartTableModel(QAbstractTableModel):
  
  selected_range_changed = Signal(Range)
  
  def __init__(self, parent=None):
    super(ChartTableModel, self).__init__(parent)
    r = Range()
    chart_list, _ = r.getChart()
    # convert the chart to a 2-d list of 13x13 elements
    chart = [[] for i in range(13)]
    row_being_filled = 0
    for (i, elem) in enumerate(chart_list):
      chart[row_being_filled].append(elem)
      if (i + 1) % 13  == 0:
        row_being_filled += 1
    # the chart is a list of lists where the second value indicate a chart cell background color
    self._chart = [[[chart_value, "#ffffff"] for chart_value in chart_row] for chart_row in chart]
    self.selected_range_changed.connect(self._handleRangeChanged)
    
  def rowCount(self, index):
    return 13
  
  def columnCount(self, index):
    return 13
  
  def data(self, index, role):
    row, col = index.row(), index.column()
    chart_list = self._chart[row][col]
    if role == Qt.DisplayRole:
      return chart_list[0]
    elif role == Qt.BackgroundRole:
      color = chart_list[1]
      color = QColor(color)
      brush = QBrush(color)
      return brush
    elif role == Qt.TextAlignmentRole:
      return Qt.AlignmentFlag.AlignCenter
    
  def headerData(self, section, orientation, role):
    if role == Qt.DisplayRole:
      return str(section + 1)
  
  def _handleRangeChanged(self, selectedRange):
    _, chart_colors = selectedRange.getChart()
    for (i, chart_row) in enumerate(self._chart):
      for (j, chart_column) in enumerate(chart_row):
        chart_list = chart_column
        chart_list[1] = chart_colors[i * 12 + j]
    self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(13, 13))
  
class ChartTableView(QTableView):
  
  selected_range_changed = Signal(Range)
  
  def __init__(self, parent=None):
    super(ChartTableView, self).__init__(parent)
    model = ChartTableModel()
    self.selected_range_changed.connect(model.selected_range_changed)
    self.setModel(model)
    