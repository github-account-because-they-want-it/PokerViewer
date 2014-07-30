'''
Created on Jul 29, 2014
@author: Mohammed Hamdy
'''
import cPickle as pickle, os

def getScriptDirectory():
  return os.path.abspath(os.path.join(__file__, os.path.pardir))

class TreeLoadSaveHandler(object):
  
  @staticmethod
  def saveTree(filename, rootItem, treeObject):
    filename = filename + ".tree"
    f = open(filename, "wb")
    pickle.dump(rootItem, f)
    pickle.dump(treeObject, f)
    f.close()
    
  @staticmethod
  def loadTree(filename):
    # returns a tuple of the root item and tree object
    f = open(filename, "rb")
    root_item = pickle.load(f)
    tree_object = pickle.load(f)
    f.close()
    return (root_item, tree_object)