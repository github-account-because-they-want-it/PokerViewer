import os
import pokereval, numpy, scipy.misc, pydot
from matplotlib import pyplot as plot
import xml.etree.ElementTree as ET
numCards = 52
numRanks = 13
numSuits = 4
numHands = 1326 #nchoosek(52,2)
numVillainHands = 1225 #nchoosek(50,2)
# Make some lists
suits = ['h', 'd', 'c', 's']
ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
cards = ['2h', '3h', '4h', '5h', '6h', '7h', '8h', '9h', 'Th', 'Jh', 'Qh', 'Kh', 'Ah',
         '2d', '3d', '4d', '5d', '6d', '7d', '8d', '9d', 'Td', 'Jd', 'Qd', 'Kd', 'Ad',
         '2c', '3c', '4c', '5c', '6c', '7c', '8c', '9c', 'Tc', 'Jc', 'Qc', 'Kc', 'Ac',
         '2s', '3s', '4s', '5s', '6s', '7s', '8s', '9s', 'Ts', 'Js', 'Qs', 'Ks', 'As']


# In[5]:

# We can describe hands or the board as lists of strings where '__' represents an unknown card
handAsStrings = ['Ah', 'Jd']
boardAsStrings = ['8d', '6s', '3h', 'Kd', '__']
pe = pokereval.PokerEval()
hand = pe.string2card(handAsStrings)
board = pe.string2card(boardAsStrings)

def conflicts(cards1, cards2):
    for i in cards1:
        for j in cards2:
            if i == j and i < numCards:
                return True
    return False
villainHand = pe.string2card(['As', '4s'])
peresult = pe.poker_eval(game='holdem', pockets=[ hand, villainHand ], board = board)

def getEquityVsHand(hand, villainHand, b):
    if conflicts(hand,villainHand) or conflicts(hand,board) or conflicts(board, villainHand):
        return -1
    peresult = pe.poker_eval(game='holdem', pockets=[hand,villainHand], board = b)
    numWins = peresult['eval'][0]['winhi']
    numTies = peresult['eval'][0]['tiehi']
    numRunouts = peresult['info'][0]
    return (numWins + numTies/2.0) / numRunouts

# EquityArray class organises hand vs hand equities for a board
class EquityArray:
    
    # Constructor
    # Input:
    #  b - list of numbers representing a board
    def __init__(self, b):
        self.board = b
        self.eArray = numpy.zeros((numCards,numCards,numCards,numCards))
        if os.path.isfile(self.getFilename()):
            self.eArray = numpy.load(self.getFilename())
        else:           
            self.makeArray()
            
    def makeArray(self):
        for i in range(numCards):
            for j in range(numCards):
                for a in range(numCards):
                    for b in range(numCards):
                        hand = [i,j]
                        villainHand = [a,b]
                        self.eArray[i][j][a][b] = getEquityVsHand(hand, villainHand, self.board)                        
        numpy.save(self.getFilename(), self.eArray)
    
    # Output : filename built from self.board
    # For exmaple, if pe.card2string(self.board) == ['Ah', 'Jd', '2c', '__', '__']
    # then return 'AhJd2c.ea.npy'.
    def getFilename(self):
        boardStr = ''
        boardAsStrings = pe.card2string(self.board)
        for i in boardAsStrings:
            if i != '__':
                boardStr = boardStr + i
        if boardStr == '': #this is the case when we have the preflop board
            boardStr = 'preflop'
        boardStr = boardStr + '.ea.npy'
        return boardStr
      
    @staticmethod
    def loadDiskBoards(path=None, maxBoards=10):
      # load equity arrays from disk and return equity arrays 
      equity_list = []
      if path is None: # search is the script directory
        path = os.path.abspath(os.path.join(__file__, os.path.pardir))
      files_here = os.listdir(path)
      board_files = [f for f in files_here if f.endswith(".ea.npy")]
      board_files = board_files[:maxBoards]
      # get the board list of strings from the file name
      file_names = [bf.split(".ea.npy")[0] for bf in board_files]
      iterators = [iter(fname) for fname in file_names]
      for it, fname in zip(iterators, file_names):
        if fname == "preflop":
          equity_list.append(MyEquityArray(["__", "__", "__", "__", "__"]))
        else:
          board_list = []
          for _ in range(len(fname) / 2):
            board_list.append(''.join([next(it), next(it)]))
          board_len = len(board_list)
          if board_len < 5:
            [board_list.append("__") for _ in range(5 - board_len)]
          equity_list.append(MyEquityArray(board_list))
      return equity_list
      
class MyEquityArray(EquityArray):
  
  def __init__(self, boardArray):
    EquityArray.__init__(self, pe.string2card(boardArray))
    self._board_array = boardArray
    
  def boardArray(self):
    return self._board_array
    
  def originalBoard(self):
    return ','.join(self._board_array)
    
  def __str__(self):
    return ''.join(self._board_array)
  
  
def getEquityVsHandFast(hand, villainHand, ea):
    return ea.eArray[hand[0]][hand[1]][villainHand[0]][villainHand[1]]

def setHandsWithConflicts(handArray, cardslist, num):
    for c in cardslist:
        if c < numCards:
            handArray[c,:] = num
            handArray[:,c] = num

# Just a special case of setHandsWithConflicts = 0
def zeroHandsWithConflicts(handArray, cardslist):
    setHandsWithConflicts(handArray, cardslist, 0)

def getEquityVsRange(hand, r, ea):
    herocard1, herocard2 = hand
    eqs = ea.eArray[herocard1,herocard2, :, :]  #numCardsx numCards x numCards x numCards
    r.r                                   #numCards x numCards
    # avoid including in the calculation hands in r that conflict with the board
    villRange = numpy.copy(r.r)
    zeroHandsWithConflicts(villRange, hand + ea.board)
    return sum(numpy.multiply(eqs,villRange)) / sum(villRange)
    

class Range:
    def __init__(self, initFrac = None):
        self.r = numpy.zeros((numCards,numCards))
        if initFrac != None:
            self.setAllFracs(initFrac)
 
        
    # Input: a hand representted by a list of two numbers
    # Output: the fraction of the hand contained in the range
    # Side-effects: N/A
    def getFrac(self, hand):
        card1, card2 = hand
        if card1 > card2:
            card1,card2 = card2,card1
        return self.r[card1][card2]
    
    
    # Input: N/A
    # Output: total number of hand combinations in the range
    # Side-effects: N/A
    def getNumHands(self):
        return sum(self.r)
    
    
    
    #Input: cardslist - list of cards in numerical format
    #Output: the number of hand combos in the range which do not conflict with any of the
    #        cards in cardslist
    # Side-Effects : N/A
    def getNumHandsWithoutConflicts(self, cardslist):
        temp = numpy.copy(self.r)
        zeroHandsWithConflicts(temp, cardslist)
        return sum(temp)
    
    # Input: cardslist - a list of cards in numerical format
    # Output: N?A
    # Side-effect: removes hands from the range with conflict with cards in cardslist
    def removeHandsWithConflicts(self, cardslist):
        zeroHandsWithConflicts(self.r, cardslist)
    
    # Input: 
    #     hand - list of numbers describing a hand
    #     f - fraction
    # Output: N/A
    #Side-effect: sets the fraction of hand in the range to f
    def setFrac(self, hand, f):
        card1, card2 = hand
        if card1 > card2:
            card1,card2 = card2,card1
        self.r[card1][card2] = f
    
    
    #Input: num - fraction
    #Output: N/A
    #Side-effects: set the fraction of all hand combos to num
    def setAllFracs(self,num):
        for i in range(numCards):
            for j in range(i+1, numCards):
                self.r[i][j] = num
                
                
                
    #Input: num - fraction
    #Output: N/A
    #Side-effects: scale the fraction of every hand combo by num
    #NB: We haven't always performed great input validation. For exmaple, here it is up to the user
    #    of this function to ensure that the scaling does not change any of the fractions to be 
    #    less rgan 0 or greater than 1.
    def scaleFracs(self, num):
        self.r = self.r * num
    
    
    #Input: rangeString - string containing comma-separated terms of the form XX, XY, XYs, XYo, XaYb
    #       value - a fraction
    #Output: N/A
    #Side-effects: set the hand combos specified by the range string to values
    def setRangeString(self, rangeString, value):
        handStrs = rangeString.replace(' ', '').split(',')
        for hand in handStrs:
            if len(hand) == 2:
                rank1 = hand[0]
                rank2 = hand[1]
                for i in suits:
                    for j in suits:
                        if rank1 == rank2 and i == j : # avoid stuff like 2c2c
                            continue
                        self.setFrac(pe.string2card([rank1+i , rank2+j]), value)
            elif len(hand) == 3:
                rank1 = hand[0]
                rank2 = hand[1]
                if hand[2] == 's': #suited hands
                    for s in suits:
                        self.setFrac(pe.string2card([rank1+s, rank2+s]), value)         
                else: #unsuited hands
                    for i in range(numSuits):
                        for j in range(i+1, numSuits):
                            self.setFrac(pe.string2card([rank1+suits[i], rank2+suits[j]]), value)
            elif len(hand) == 4:
                card1 = hand[0:2]
                card2 = hand[2:4]
                self.setFrac(pe.string2card([card1, card2]), value)
            else:
                print("ERROR!")
        
    # Input:
    #      rank1 - a string specificying a rank ('2', '3', 'T')
    #      rank2 - similar
    #      suited - a boolean (True, False) indicating suitedness
    # Output: fraction of specificed ambiguous hand contained in the rank
    # Side-effects: N/A
    #
    # Ambiguous hands are e.g. AKo (which stands for 12 combos)
    #                         AKs (4 combos)
    #                          33 (6 combos)
    # So for exmaple is we call getAmbigFrac('A', 'k', True, but none of AKcc or AKdd
    # The result should be 0.5 (not 2)
    # Note: if we're interested in pocket pairs then rank1 == rank2 and suited == False
    def getAmbigFrac(self, rank1, rank2, suited):
        nHand = 0.0
        nFrac = 0.0        
        #look at every specific hand combo corresponding to rank1, rank2 and suited
        for i in suits:
            for j in suits:
                card1 = rank1 + i
                card2 = rank2 + j
                if (suited and i != j) or (not suited and i == j):
                    continue
                if (card1 == card2):
                    continue
                nHand += 1
                nFrac += self.getFrac(pe.string2card([card1,card2]))                       
        return nFrac / nHand
    
    def _repr_svg_(self):
        result = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="260" height="260">'
        for i in range(numRanks):
            for j in range(numRanks):
                frac = self.getAmbigFrac(ranks[i], ranks[j], i > j)
                hexcolor = '#%02x%02x%02x' % (255*(1-frac), 255, 255*(1-frac))
                result += '<rect x="' + str(i*20) + '" y="' + str(j*20) + '" width ="20" height="20" fill="'+ hexcolor+'"></rect>'
                result += '<text x="' + str(i*20)+'" y ="'+str((j+1)*20) + '" font-size="12" >' + ranks[i] + ranks[j] + '</text>'
        result += '</svg>'
        return result
   
    def getChart(self):
      # return a list of strings to represent the chart
      svg = self._repr_svg_()
      svg_tree = ET.fromstring(svg)
      chart_strings = []
      for child in svg_tree:
        child_text = child.text
        if child_text:
          chart_strings.append(child_text)
      return chart_strings
    
    
    # Input:
    #      villainRange - Range object
    #      board - a list of numbers representing a board
    # Output: list of tuples of the form
    #                  (hand, equity)
    #         where a hand is a list of integers and equity is equity is equity vs villainRange on baord
    #         This output will be sorted by equity (highest first)
    # Side-effects: N/A
    def getHandsSortedAndEquities(self, villainRange, board):
        ea = EquityArray(board)
        result = []
        for i in range(numCards):
            for j in range(i+1, numCards):
                hand = [i,j]
                if not conflicts(board, hand):
                    result.append((hand, getEquityVsRange(hand, villainRange, ea)))
        
        result.sort(key = lambda x: x[1], reverse = 1)
        return result
    
    
    
    # Input:
    #      fraction - a number describing fraction of all hands
    #      board - a list of numbers representing a board
    # Output: N/A
    # Side-effects: sets fraction of (approx.) the top fraction of hands (as rtanked by equity vs ATC)
    #on board to 1, and rest to 0. 
    def setToTop(self, fraction, board):
        rangeAllHands = Range()
        rangeAllHands.setAllFracs(1.0) #ATC Range
        handsSorted = self.getHandsSortedAndEquities(rangeAllHands, board)
        
        # 1326 == nchoosek(52,2)
        # nchoosek(49,2)  - on flop.
        
        numCardsLeft = numCards
        for c in board:
            if c < numCards:
                numCardsLeft -= 1
            
        self.setAllFracs(0)
        for i in range(int(fraction * scipy.misc.comb(numCardsLeft, 2))):
            self.setFrac(handsSorted[i][0],1.0)  #Setting top % fractions to 1.

def plotEqDistn(r1, r2, board):
    xs = []
    ys =[]
    
    handCount = 0.0
    
    for hand in r1.getHandsSortedAndEquities(r2, board):
        #plot hand at (handCount, equity) and (handCount + r1.getFrac(hand[0]), equity)
        xs.append(handCount)
        handCount += r1.getFrac(hand[0])
        xs.append(handCount)
        ys.append(hand[1])
        ys.append(hand[1])
        
    
    
    plot (xs, ys)
    
#Input:
#  r1 and r2 - ranges
#  n - positive integers
#Output: N/A
#Side-effects:
#   Modifies r1 to incorporate some amount of r2. In particular, the fraction of every hand in r1
#   at the end of the function will be (old amount) * (fraction) + (new amount) * (1-fraction)
#   where fraction becomes closer to 1 the higher n is.
def updateRange(r1, r2, n):
    fraction = 1 - 1 / (n + 2.0)
    for i in range(numCards):
        for j in range(i+1, numCards):
            hand = [i,j]
            r1.setFrac(hand, (r1.getFrac(hand)) * (fraction) + (r2.getFrac(hand)) * (1-fraction))

# Solving the shove/fold:
# SB can either shove or fold at his first decision
# SB's straegy is defined by his jamming range, and the BB's by his calling range.

# Fictitious play

# Input: N/A
# Output: N/A
# Side-Effects: display SB shoving range and BB calling range.
def doShoveFoldGame():
    nIter = 200 #number of iterations
    S = 10 #stack size in BBs
    ea = EquityArray(pe.string2card(['__', '__','__','__','__']))
    
    # guess some initial ranges
    sbJamRange = Range()
    sbJamRange.setAllFracs(0.5)
    bbCallRange = Range()
    bbCallRange.setAllFracs(0.5)
    

    for n in range(nIter):
        # solve for SB max expl strategy
        bestSBJamRange = Range()
        for i in range(numCards):
            for j in range(i+1, numCards):
                hand = [i,j]
                bb_call_freq = bbCallRange.getNumHandsWithoutConflicts(hand) / numVillainHands
                equity = getEquityVsRange(hand, bbCallRange, ea)
                evJam = (1 - bb_call_freq) * (S+1) + (bb_call_freq) * equity * 2*S
                evFold = S - 0.5
                if (evJam > evFold):
                    bestSBJamRange.setFrac(hand, 1)
                else:
                    bestSBJamRange.setFrac(hand, 0) 
                    
        # udate SB strategy
        updateRange(sbJamRange, bestSBJamRange, n)
        
        # solve for BB max expl strategy
        bestBBCallRange = Range()
        for i in range(numCards):
            for j in range(i+1, numCards):
                hand = [i,j]
                equity = getEquityVsRange(hand, sbJamRange, ea)
                evCall = 2 * S * equity
                evFold = S - 1
                if (evCall > evFold):
                    bestBBCallRange.setFrac(hand,1)
                else:
                    bestBBCallRange.setFrac(hand,0)
                    
        #update BB strategy
        
        updateRange(bbCallRange, bestBBCallRange, n)

class DecPt:
    def __init__(self, player, initial_sb_cip, initial_bb_cip, eArray, parentAction, newCardFreq = 1.0):
        self.player = player
        self.initial_sb_cip = initial_sb_cip
        self.initial_bb_cip = initial_bb_cip
        self.eArray = eArray
        self.parentAction = parentAction
        self.newCardFreq = newCardFreq
        
        
    # Input: player: string that is either "SB" or "BB"
    # Output: CIP of player at the beginning of the decision point
    def getPlayerCIP(self, player):
        if (player == "SB"):
            return self.initial_sb_cip
        elif (player == "BB"):
            return self.initial_bb_cip
        else:
            print "ERROR: DecPt.getPlayerCIP given player: " + player
            
    def __eq__(self, other):
      if isinstance(other, DecPt):
        return self.player == other.player and \
               self.initial_sb_cip == other.initial_sb_cip and \
               self.initial_bb_cip == other.initial_bb_cip and \
               self.parentAction == other.parentAction
        return NotImplemented

# A simple approach to a tree structure:
# Put all our decision points in a list (this implicitly numbers them):
#    decPts
# Then, we need to keep track of parent and child relationship -- use a couple other arrays to do that
#  parent: the i^th element of this array contain the number of the point which is the i^th's point's parent
#  So, if we want to know point i's parents, we look at parent[i]
#  children: the i^th entry in this list contains a list of the numbers of points are the i^th's point's children
# And if we want to know point i's children, we can find a list of them in children[i]
# Example: 
#             0      1       2        3      4
# decPts: [pointA, pointB, pointC, pointD, pointE]
# children: [ [], [], [], [1,2], [0,3]]
# parents: [4, 3, 3, 4, None]
# When we make a new tree, we'll just give it effective stack S, and a first decision point (root)
# Later, we will add new decision points
class Tree:
    def __init__(self, S, root):
        self.effStack = S
        self.decPts = []  # list of all decision points in the tree
        self.children = []
        self.parents = []
        self.addDecPt(root,None)
    
    #Input: N/A
    # Output: number of decision points in tree
    # Side-effects: N/A
    def getNumPoints(self):
        return len(self.decPts)
    
    
    # Input: N/A
    #Output: Effective stack at beginning of decision tree
    #      corresponds to beggining of hands, CIP is 0.
    # Side-effects: N/A
    def getEffStack(self):
        return self.effStack
    
    
    # Adds a new decision point to the tree
    #Inputs:
    #  point - the new point (not previously in tree)
    #  parent - a decision point already in the tree
    # Output: N/A
    # Side-effect - Adds new decision point to tree
    def addDecPt(self, point, parent):
        self.decPts.append(point)
        self.children.append([])
        if (parent == None): #only true for the root node
            self.parents.append(None)
        else:
            parentIndex = self.decPts.index(parent)
            self.children[parentIndex].append(self.getNumPoints() - 1)
            self.parents.append(parentIndex)
    
    
    def removeDecPt(self, decPt):
        """
        We need to find if that decision point is a parent for any points
        """
        parent_index = self.decPts.index(decPt)
        self.children.pop(parent_index)
    
    #Inputs: N/A
    #Outputs: returns a PNG file displaying a tree
    #Side-effects: N/A
    def _repr_png_(self):
        g = pydot.Dot(graph_type ="digraph")
        for i in range(self.getNumPoints()):
            node_label = str(i) + ': ' + self.decPts[i].player             + ' (' + str(self.decPts[i].initial_sb_cip) + ','                          + str(self.decPts[i].initial_bb_cip) + ')'
            g.add_node(pydot.Node('node%d'%i, label=node_label))
        
        for i in range(self.getNumPoints()):
            for j in self.children[i]:
                g.add_edge(pydot.Edge('node%d'%i, 'node%d'%j, label=self.decPts[j].parentAction))
        
        return g.create(g.prog, 'png')

# StrategyPair
# Strategy: a range for every action a player can take
#Strategy Pair is a pair of strategy -- one for each player
# So basically, a strategy pair will contain a range for every player action in the game. 
#  Also, since there's an action for every decision point in the game (the Ppoint's parent action) (except the root)
#  we can essentially keep track of all the range by associating one range with each decision point.
#  (i.e. we'll make  the ranges the same way we number decision points)
# So our StrategyPair class will:
# - hold a tree, called tree, and keep track of the tree's size
# - hold starting ranges for both players
# - hold a list of ranges, called ranges, such that range[i] is the range of hands that takes the parent action of tree.decPts[i]
# - when we make a new strategy pair, we'll need to set these ranges intelligently.
# - find the range that either player holds at any decision points
# - be able to display itself
# - be able to update itself (given a max exploitative strategy and a mixing fraction)
# - store the EVs of having any hand at any decision point for each player
#   - there will be two 3-D arrays, one for each player, of dimensions
#         num-decision-points by numCards by numCards
#      the first of those dimensions specifies a decision point and the last two specify hole cards
#      and the arrays hold the EVs of having that hand at that decision point.

class StrategyPair:
    def __init__(self, tree, sbStartingRange = None, bbStartingRange = None):
        self.tree = tree
        self.size = self.tree.getNumPoints()
        self.ranges = [Range() for i in range(self.size)]
        self.evs = dict()
        self.evs['SB'] = numpy.zeros((self.size, numCards, numCards))
        self.evs['BB'] = numpy.zeros((self.size, numCards, numCards))
        self.sbStartingRange = sbStartingRange
        if sbStartingRange == None:
            self.sbStartingRange = Range(1.0)
        self.bbStartingRange = bbStartingRange
        if bbStartingRange == None:
            self.bbStartingRange = Range(1.0)
        #initialize the ranges
        self.initialize()
        
    #Input:
    #  player - "SB" or "BB"
    #  maxExplStrat - a dict that maps decision points numbers to ranges for all player's decision pts
    #  n - a positive integer (the iteration number)   
    def updateRanges(self, player, maxExplStrat, n):
        for i in range(self.size):
            if (self.tree.decPts[i].player == player):
                for j in self.tree.children[i]:
                    updateRange(self.ranges[j], maxExplStrat[j], n)
                    
    #Inputs:
    #  player: "SB" or "BB"
    # iDecPt: the number(index) of the decision point we're interested in
    #Outputs: the range the player holds at the beginning of play at the decision point
    #Side-effects: N/A
    def getMostRecentRangeOf(self, player, iDecPt):
        iCurrDecPt = iDecPt
        while (iCurrDecPt != 0 and self.tree.decPts[self.tree.parents[iCurrDecPt]].player != player):
            iCurrDecPt = self.tree.parents[iCurrDecPt]
        if iCurrDecPt == 0:  #we made it to the root
                return self.getStartingRangeOf(player)
        else:     
            return self.ranges[iCurrDecPt]

    
    #Inputs: player - "SB" or "BB"
    #Outputs: the starting range of player
    #Side-Effects: N.A
    def getStartingRangeOf(self, player):
        if player == "SB":
            return self.sbStartingRange
        elif player == "BB":
            return self.bbStartingRange
        else:
            print("ERROR in StrategyPair.getStartingRangeOf: passed player: " + player)
            return None
        
    
    #Inputs: n - a number
    #Outputs: the range associated with the parent action of decision point n
    #Side-effects: N/A
    def getRange(self, n):
        return self.range[n]
    
    
    #Input - N/A
    #Output - N/A
    #Side-effect - display all the ranges and action in our tree and our solution
    def dump(self):
        for i in range(1, self.size):
            parentActor = self.tree.decPts[self.tree.parents[i]].player
            action = self.tree.decPts[i].parentAction
            print str(i) + ": " + parentActor + " " + action
            if parentActor != "Nature":
                print(self.ranges[i])
    
    #Recursive approach to working on trees:
    # When we want to something for every node in a tree, we can write a function f(),
    # does whatever we want for one node, and then calls itself on all the children of that node.
    # Then to do the thing for all the nodes, we just call f() on the root node.
    
    #Input - N/A
    #Output - N/A
    #Side-Effect - set all the ranges in the strategy pair, assuuming the players start out with 
    #             their starting ranges and randomly (uniformly) select an action at each dec pt.
    def initialize(self):
        self.initializeHelper(0, 1.0, 1.0)
        
    #Inputs:
    #  iCurrDecPt - index of the current decision point
    #  sbScale and bbScale - numbers between 0 and 1 -- the fraction of the starting ranges that the players
    #                        bein to this decision point.
    #Outputs: N.A
    #Side-Effects: set the range corresponding to the current decsion point's children, and call itself 
    #              on all of the point's children (so as to do the right thing for them too)
    def initializeHelper(self, iCurrDecPt, sbScale, bbScale):
        children = self.tree.children[iCurrDecPt]
        numChildren = len(children)
        
        if self.tree.decPts[iCurrDecPt].player == 'SB':
            sbScale /= numChildren
            for iChild in children:
                self.ranges[iChild].r = self.sbStartingRange.r.copy()
                self.ranges[iChild].scaleFracs(sbScale)
                self.ranges[iChild].removeHandsWithConflicts(self.tree.decPts[iCurrDecPt].eArray.board)
        elif self.tree.decPts[iCurrDecPt].player == 'BB':
            bbScale /= numChildren
            for iChild in children:
                self.ranges[iChild].r = self.bbStartingRange.r.copy()
                self.ranges[iChild].scaleFracs(bbScale)
                self.ranges[iChild].removeHandsWithConflicts(self.tree.decPts[iCurrDecPt].eArray.board)
        
        for iChild in children:
            self.initializeHelper(iChild, sbScale, bbScale)

#Inputs:
# tree: a decision tree object
# strats: a StrategyPair
# hero: "SB" or "BB" -- the player whose EVs we're calculating
# villain: "SB" or "BB" -- the other guy
# Outputs: N/A
# Side-effects: set all the evs in strats.ev[hero] to be the max expl EVs
def setMaxExplEVs(tree, strats, hero, villain):
    setMaxExplEVsHelper(tree, 0, strats, hero, villain)
    
#Inputs:
# tree: a decision tree object
# iDecPt: the index of a decision point in the tree
# strats: a StrategyPair
# hero: "SB" or "BB" -- the player whose EVs we're calculating
# villain: "SB" or "BB" -- the other guy
# Outputs: N/A
# Side-effects: set all the evs in strats.ev[hero] in the subtree starting at iDecPt to be the max expl EVs
def setMaxExplEVsHelper(tree, iDecPt, strats, hero, villain):
    currDecPt = tree.decPts[iDecPt]
    if (currDecPt.player == 'Leaf'):
        setMaxExplEVsAtLeaf(tree, iDecPt, strats, hero, villain)
    elif (currDecPt.player == hero):
        setMaxExplEVsAtHeroDP(tree, iDecPt, strats, hero, villain)
    elif (currDecPt.player == villain):
        setMaxExplEVsAtVillainDP(tree, iDecPt, strats, hero, villain)
    else: #it must be the that player is nature.
        setMaxExplEVsAtNatureDP(tree, iDecPt, strats, hero, villain)
    
    
# Signature is the same as for setMaxExplHelper, but now we know the current DP is a leaf.
def setMaxExplEVsAtLeaf(tree, iDecPt, strats, hero, villain):
    currDecPt = tree.decPts[iDecPt]
    if (currDecPt.parentAction == "fold"):
        if (tree.decPts[tree.parents[iDecPt]].player == hero): #hero folded
            strats.evs[hero][iDecPt] = numpy.ones_like(strats.evs[hero][iDecPt])*(tree.effStack - currDecPt.getPlayerCIP(hero))
        else: # villain folded
            strats.evs[hero][iDecPt] = numpy.ones_like(strats.evs[hero][iDecPt])*(tree.effStack + currDecPt.getPlayerCIP(villain))
    else: # we are seeing a showdown -- Hero's EVs are all (S-hero cip) + ((hero cip + vill cip) * equity)
        for i in range(0,numCards):
            for j in range(i+1,numCards):
                strats.evs[hero][iDecPt][i,j] = (tree.effStack - currDecPt.getPlayerCIP(hero)) + \
                  (currDecPt.getPlayerCIP(hero)+currDecPt.getPlayerCIP(villain))* \
                 getEquityVsRange([i,j],strats.getMostRecentRangeOf(villain,iDecPt),currDecPt.eArray)
    
    setHandsWithConflicts(strats.evs[hero][iDecPt], currDecPt.eArray.board, -1)
    
    
# Signature is the same as for setMaxExplHelper, but now we know the current DP is Hero's
def setMaxExplEVsAtHeroDP(tree, iDecPt, strats, hero, villain):
    strats.evs[hero][iDecPt] = -1 * numpy.zeros_like(strats.evs[hero][iDecPt])
    for iChild in tree.children[iDecPt]:
        setMaxExplEVsHelper(tree, iChild, strats, hero, villain)
        strats.evs[hero][iDecPt] = numpy.maximum(strats.evs[hero][iDecPt], strats.evs[hero][iChild])
        
    
    
    
# Signature is the same as for setMaxExplHelper, but now we know the current DP is Villain's     
def setMaxExplEVsAtVillainDP(tree, iDecPt, strats, hero, villain):
    # for every hand, our EV is (how often Villain takes each ) * (our EV when he takes that action)
    for iChild in tree.children[iDecPt]:
        setMaxExplEVsHelper(tree, iChild, strats, hero, villain)
    for i in range(0,numHands):
        for j in range(i+1, numCards):
            
            comboCounts = {}
            totalNumHandsInRange = 0
            for iChild in tree.children[iDecPt]:
                comboCounts[iChild] =  strats.ranges[iChild].getNumHandsWithoutConflicts([i,j])
                totalNumHandsInRange += comboCounts[iChild]
                        
            strats.evs[hero][iDecPt][i][j] = 0
            for iChild in tree.children[iDecPt]:
                strats.evs[hero][iDecPt][i][j] += strats.evs[hero][iChild][i][j] * (comboCounts[iChild] / totalNumHandsInRange)

def setMaxExplEVsAtNatureDP(tree, iDecPt, strats, hero, villain):
    for iChild in tree.children[iDecPt]:
        setMaxExplEVsHelper(tree, iChild, strats, hero, villain)
    villainRange = strats.getMostRecentRangeOf(villain, iDecPt)
    for i in range(0,numHands):
        for j in range(i+1, numCards):
            if conflicts([i,j], tree.decPts[iDecPt].eArray.board):
                strats.evs[hero][iDecPt][i][j] = -2 # Mark EV as -1 to indicate impossible situation.
            else:
                comboCounts = {} # number of combo's in villain's range that don't conflict with the new card or hero's hand.
                comboSum = 0.0  # ssum of comboCounts for all the children
                for iChild in tree.children[iDecPt]:
                    newBoard = tree.decPts[iChild].eArray.board
                    if (conflicts(newBoard, [i,j])):
                        comboCounts[iChild] = 0
                    else:
                        comboCounts[iChild] = villainRange.getNumHandsWithoutConflicts([i,j]) * tree.decPts[iChild].newCardFreq
                    comboSum += comboCounts[iChild] # TODO: mark
            strats.evs[hero][iDecPt][i][j] = 0
            if (comboSum == 0.0):
                strats.evs[hero][iDecPt][i][j] = -1
            else:
                for iChild in tree.children[iDecPt]:
                    strats.evs[hero][iDecPt][i][j] += strats.evs[hero][iChild][i][j] * (comboCounts[iChild] / comboSum)

# Inputs: 
#  tree: a decision tree
#  hero: "SB" or "BB"
#  stratpair: a StrategyPair object containing the EVs
#Output: result: a dict that maps decision point numbers to (maximally exploitative) ranges

def getMaxEVStrat(tree, hero, stratpair):
    result = {}
    if hero == "SB":
        getMaxEVStratHelper(tree, hero, stratpair, 0, stratpair.sbStartingRange, result)
    elif hero == "BB":
        getMaxEVStratHelper(tree, hero, stratpair, 0, stratpair.bbStartingRange, result)
    else:
        print "ERROR in getMaxEVStrat()"
    return result
  
#Inputs:
#  rtee: decision tree
#  hero: "Sb" or "BB"
#  stratpair: a StrategyPair containing the max expl EVs
#  iCurrDecPt: index of the currently-under-consideration decision point
#  currRange: the range hero got to the spot with
#  result: the dict mapping dec pt indices to ranges that we use to return our result.
# Outputs: N/A (result input is kind of an output)



def getMaxEVStratHelper(tree, hero, stratpair, iCurrDecPt, currRange, result):
    currDecPt = tree.decPts[iCurrDecPt]
    if currDecPt.player == hero:
        # initialize child action ranges
        for iChild in tree.children[iCurrDecPt]:
            result[iChild] = Range()
        # the, for wach hand we could have, find the max ev way to play it
        for i in range(0,numCards):
            for j in range(i+1,numCards):
                if currRange.r[i][j] > 0:
                    #look at every way we could play it and keep track of the best we've seen and how good that is
                    iMaxEV = 0 #index of max ev child action
                    maxEV = -1 # best EV we've seen so far
                    for k in tree.children[iCurrDecPt]:
                        if (stratpair.evs[hero][k][i][j] > maxEV):
                            maxEV = stratpair.evs[hero][k][i][j]
                            iMaxEV = k
                    # and play any of that hand in the range we got here with in the max ev way.
                    if (maxEV >= 0):
                        result[iMaxEV].setFrac([i,j], currRange.r[i][j])
        for iChild in tree.children[iCurrDecPt]:
            getMaxEVStratHelper(tree, hero, stratpair, iChild, result[iChild], result)
    else: # if this is not a hero decision point
        for iChild in tree.children[iCurrDecPt]:
            getMaxEVStratHelper(tree, hero, stratpair, iChild, currRange, result)

#Inputs:
#  strats- a StrategyPair
#  player - "SB" or "BB"
#  index- index or number of an action. (index is 0 at the top of the tree)
#Output: the average EV, over all hands,of player at index using strats.
def getAvgEV(strats, player, index):
    numCombos = 0.0;
    summedEV = 0.0;
    playerRange = strats.getMostRecentRangeOf(player,index)
    for i in range(numCards):
        for j in range(i+1, numCards):
            ev = strats.evs[player][index][i][j]  #ev of hands ij at this point
            frac = playerRange.r[i][j]     # fraction in player's range of hand ij at this point
            if ev >= 0:
                summedEV += ev * frac
                numCombos += frac
    return summedEV / numCombos


# Inputs:
#  tree: a tree that we're going to solve
#  nIter: number of iterations to run for
#  sbStartingRange and bbStartingRange: optional, Range objects
def doFP(tree, nIter, sbStartingRange = None, bbStartingRange = None):
    #initialize guess at strategies for both players
    strats = StrategyPair(tree, sbStartingRange, bbStartingRange)
    
    for i in range(1, nIter+1):
        print i
        
        setMaxExplEVs(tree, strats, "SB", "BB")
        sbMaxEVStrat = getMaxEVStrat(tree, "SB", strats)
        strats.updateRanges("SB", sbMaxEVStrat, i)
        print "SB average EV: " + str(getAvgEV(strats, 'SB', 0))
        
        setMaxExplEVs(tree, strats, "BB", "SB")
        bbMaxEVStrat = getMaxEVStrat(tree, "BB", strats)
        strats.updateRanges("BB", bbMaxEVStrat, i)
        print "BB average EV: " + str(getAvgEV(strats, 'BB', 0))
        
    return strats

if __name__ == "__main__":
  """
  S = 20
  preflopEArray = EquityArray(pe.string2card(['__','__','__','__','__']))
  point0 = DecPt('SB', 0.5, 1.0, preflopEArray, "")
  point1 = DecPt('Leaf', 0.5, 1.0, preflopEArray, "fold")
  point2 = DecPt('BB', 2.0, 1.0, preflopEArray, "bet")
  point3 = DecPt('Leaf', 2.0, 1.0, preflopEArray, "fold")
  point4 = DecPt('SB', 2.0, 20.0, preflopEArray, "bet")
  point5 = DecPt('Leaf', 2.0, 20.0, preflopEArray, "fold")
  point6 = DecPt('Leaf', 20.0, 20.0, preflopEArray, "call")
  
  minrShoveTree = Tree(S, point0)
  minrShoveTree.addDecPt(point1,point0)
  minrShoveTree.addDecPt(point2,point0)
  minrShoveTree.addDecPt(point3,point2)
  minrShoveTree.addDecPt(point4,point2)
  minrShoveTree.addDecPt(point5,point4)
  minrShoveTree.addDecPt(point6,point4)
  minrShoveTree
  """
  r = Range()
  print(r._repr_svg_())