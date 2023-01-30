import numpy as np
import tkinter as tk
from numba import jit

StartingBoard = np.zeros(144, dtype=np.uint8)

@jit(nopython=True)
def iPxy(x, y):
    return 64 + 8 * y + x

@jit(nopython=True)
def GetIDmove(player, x, y):
    return player * 100 + x * 10 + y

@jit(nopython=True)
def DecodeIDmove(IDmove):
    y = IDmove % 10
    x = IDmove // 10 % 10
    player = IDmove // 100
    return player, x, y

@jit(nopython=True)
def _PossibleMoves(idPlayer, B):
    nb = 0
    if idPlayer == 0:
        for x in range(8):
            for y in range(7):
                p = iPxy(x, y)
                if B[p] == 0 and B[p+8] == 0:
                    B[nb] = GetIDmove(0, x, y)
                    nb += 1
    elif idPlayer == 1:
        for x in range(7):
            for y in range(8):
                p = iPxy(x, y)
                if B[p] == 0 and B[p+1] == 0:
                    B[nb] = GetIDmove(1, x, y)
                    nb += 1
    B[-1] = nb

_PossibleMoves(0, StartingBoard)

@jit(nopython=True)
def Terminated(B):
    return B[-1] == 0

@jit(nopython=True)
def GetScore(B):
    if B[-2] == 10:
        return 1
    elif B[-2] == 20:
        return -1
    else:
        return 0

@jit(nopython=True)
def Play(B, idMove):
    player, x, y = DecodeIDmove(idMove)
    p = iPxy(x, y)
    B[p] = 1
    if player == 0:
        B[p+8] = 1
    else:
        B[p+1] = 1
    nextPlayer = 1 - player
    _PossibleMoves(nextPlayer, B)
    B[-3] = nextPlayer

    

class GameWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.board = StartingBoard.copy()
        self.title("Domineering")

        self.canvas = tk.Canvas(self, width=400, height=400)
        self.canvas.pack()

        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        for x in range(8):
            for y in range(8):
                if self.board[iPxy(x, y)] == 1:
                    self.canvas.create_rectangle(x*50, y*50, (x+1)*50, (y+2)*50,
                                                fill="lightgray")
                elif self.board[iPxy(x, y)] == 0:
                    self.canvas.create_rectangle(x*50, y*50, (x+1)*50, (y+1)*50,
                                                fill="white")
    def on_canvas_click(self, event):
        x = event.x // 50
        y = event.y // 50
        id_move = GetIDmove(self.board[-3], x, y)
        Play(self.board, id_move)
        self.draw_board()

    def run(self):
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.mainloop()

if __name__ == '__main__':
    window = GameWindow()
    window.run()
