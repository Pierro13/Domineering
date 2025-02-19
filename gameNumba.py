import numpy as np
import random
import time
import numba
import math
from numba import jit  # jit convertit une fonction python => fonction C

# MCTS parameters
c = 2 
nSimulations = 1000

def UCT(node):
    if node.visits == 0 : return math.inf
    return node.mean + c * np.sqrt(np.log(node.parent.visits) / node.visits)

class Node:
    def __init__(self, parent, idMove):
        self.parent = parent
        self.idMove = idMove
        self.children = []
        self.visits = 0
        self.wins = 0
        self.mean = 0
    
    def add_child(self, childNode):
        self.children.append(childNode)

    def update(self, result):
        self.visits += 1
        self.wins += result
        self.mean = self.wins / self.visits



###################################################################

# PLayer 0 => Vertical    Player
# PLayer 1 => Horizontal  Player

# IdMove : code servant à identifier un coup particulier sur le jeu
# P   : id player 0/1
# x,y : coordonnées de la tuile, Player0 joue sur (x,y)+(x,y+1) et Player1 sur (x,y)+(x+1,y)

# convert: player,x,y <=> IDmove

# IDmove=123 <=> player 1 plays at position x = 2 and y = 3
# ce codage tient sur 8 bits !

@jit(nopython=True)
def GetIDmove(player,x,y):
    return player * 100 + x * 10 + y

@jit(nopython=True)
def DecodeIDmove(IDmove):
    y = IDmove % 10
    x = int(IDmove/10) % 10
    player = int(IDmove / 100)
    return player,x,y

###################################################################

# Numba requiert des numpy array pour fonctionner

# toutes les données du jeu sont donc stockées dans 1 seul array numpy

# Data Structure  - numpy array de taille 144 uint8 :
# B[ 0- 63] List of possibles moves
# B[64-127] Gameboard (x,y) => 64 + x + 8*y
# B[-1] : number of possible moves
# B[-2] : reserved
# B[-3] : current player


StartingBoard  = np.zeros(144,dtype=np.uint8)

@jit(nopython=True)   # pour x,y donné => retourne indice dans le tableau B
def iPxy(x,y):
    return 64 + 8 * y + x

@jit(nopython=True)
def _PossibleMoves(idPlayer,B):   # analyse B => liste des coups possibles par ordre croissant
    nb = 0

    #player V
    if idPlayer == 0 :
        for x in range(8):
            for y in range(7):
                p = iPxy(x,y)
                if B[p] == 0 and B[p+8] == 0 :
                    B[nb] = GetIDmove(0,x,y)
                    nb+=1
    # player H
    if idPlayer == 1 :
        for x in range(7):
            for y in range(8):
                p = iPxy(x,y)
                if B[p] == 0 and B[p+1] == 0 :
                    B[nb] = GetIDmove(1,x,y)
                    nb+=1

    B[-1] = nb

_PossibleMoves(0,StartingBoard)   # prépare le gameboard de démarrage


###################################################################

# Numba ne gère pas les classes...

# fonctions de gestion d'une partie
# les fonctions sans @jit ne sont pas accélérées

# Player 0 win => Score :  1
# Player 1 win => Score : -1


# def CreateNewGame()   => StartingBoard.copy()
# def CopyGame(B)       => return B.copy()

@jit(nopython=True)
def Terminated(B):
    return B[-1] == 0

@jit(nopython=True)
def GetScore(B):
    if B[-2] == 10 : return  1
    if B[-2] == 20 : return -1
    return 0


@jit(nopython=True)
def Play(B,idMove):
    player,x,y = DecodeIDmove(idMove)
    p = iPxy(x,y)

    B[p]   = 1
    if player == 0 : B[p+8] = 1
    else :           B[p+1] = 1

    nextPlayer = 1 - player

    _PossibleMoves(nextPlayer,B)
    B[-3] = nextPlayer

    if B[-1] == 0  :             # gameover
        B[-2] = (player+1)*10    # player 0 win => 10  / player 1 win => 20


@jit(nopython=True)
def Playout(B):
    while B[-1] != 0:                   # tant qu'il reste des coups possibles
        id = random.randint(0,B[-1]-1)  # select random move
        idMove = B[id]
        Play(B,idMove)


##################################################################
#
#   for demo only - do not use for computation

def Print(B):
    for yy in range(8):
        y = 7 - yy
        s = str(y)
        for x in range(8):
            if     B[iPxy(x,y)] == 1 : s += '::'
            else:                      s += '[]'
        print(s)
    s = ' '
    for x in range(8): s += str(x)+str(x)
    print(s)


    nbMoves = B[-1]
    print("Possible moves :", nbMoves)
    s = ''
    for i in range(nbMoves):
        s += str(B[i]) + ' '
    print(s)



def PlayoutDebug(B,idMove):
    Print(B)
    while not Terminated(B):
    
        player,x,y = DecodeIDmove(idMove)
        print("Playing : ",idMove, " -  Player: ",player, "  X:",x," Y:",y)
        Play(B,idMove)
        Print(B)
        print("---------------------------------------")

def MCTS(node, B, player, simulations):
    if Terminated(B) or simulations == 0:
        return GetScore(B)

    if node.visits == 0:
        # si le noeud n'a pas été visité, on calcule tous les moves possibles
        for i in range(B[-1]):
            idMove = B[i]
            childB = B.copy()
            Play(childB, idMove)
            childNode = Node(node, idMove)
            node.add_child(childNode)
    
    nextNode = sorted(node.children, key=UCT, reverse=True)[0]
    nextB = B.copy()
    Play(nextB, nextNode.idMove)

    # joueur suivant
    result = -MCTS(nextNode, nextB, 1-player, simulations-1)

    node.update(result)

    return result

def PlayMCTS(B, player):
    root = Node(None, None)
    for i in range(nSimulations):
        result = MCTS(root, B, player, 100)

    # Choix du meilleur noeud
    bestNode = sorted(root.children, key=lambda x: x.visits, reverse=True)[0]
    bestMove = bestNode.idMove
    return bestMove

B = StartingBoard.copy()

while not Terminated(B):
    idMove = PlayMCTS(B, B[-3])
    Play(B, idMove)
    Print(B)
    print("---------------------------------------")

print("le joueur gagnant est : ",B[-3])