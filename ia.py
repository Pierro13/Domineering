import math
import random
import numba
from numba import jit  # jit convertit une fonction python => fonction C
from numba import int32, float32    # import the types
from numba.experimental import jitclass


@jitclass()
class Node:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.visits = 0
        self.wins = 0

    def add_child(self, child_state):
        child = Node(child_state, self)
        self.children.append(child)
        return child

    def select_child(self):
        # maximiser mean(i) + c * sqrt( ln(n)/n(i) )
        c = max(self.children, key=lambda x: x.wins/x.visits +
                2*math.sqrt(math.log(self.visits)/x.visits))
        return c

    def update(self, result):
        self.visits += 1
        self.wins += result