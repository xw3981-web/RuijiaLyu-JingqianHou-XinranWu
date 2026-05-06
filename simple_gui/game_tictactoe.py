import tkinter as tk

class TicTacToeGame(tk.Toplevel):
    def __init__(self, parent, is_my_turn, my_symbol, on_move):
        super().__init__(parent)
        self.title(f"Tic Tac Toe - You are {my_symbol}")
        self.geometry("300x300")
        self.is_my_turn = is_my_turn
        self.my_symbol = my_symbol
        self.on_move = on_move
        self.board = [""] * 9
        self.buttons = []
        
        self.status_label = tk.Label(self, text="Your turn!" if is_my_turn else "Waiting for opponent...", font=("Helvetica", 12))
        self.status_label.pack(pady=5)
        
        frame = tk.Frame(self)
        frame.pack()
        for i in range(9):
            btn = tk.Button(frame, text="", width=5, height=2, font=("Helvetica", 24),
                            command=lambda idx=i: self.make_move(idx))
            btn.grid(row=i//3, column=i%3)
            self.buttons.append(btn)

    def make_move(self, index):
        if self.is_my_turn and self.board[index] == "":
            self.board[index] = self.my_symbol
            self.buttons[index].config(text=self.my_symbol, state="disabled")
            self.is_my_turn = False
            self.status_label.config(text="Waiting for opponent...")
            self.on_move(index) 
            self.check_win()

    def apply_opponent_move(self, index):
        opp_symbol = "O" if self.my_symbol == "X" else "X"
        self.board[index] = opp_symbol
        self.buttons[index].config(text=opp_symbol, state="disabled")
        self.is_my_turn = True
        self.status_label.config(text="Your turn!")
        self.check_win()

    def check_win(self):
        wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a, b, c in wins:
            if self.board[a] == self.board[b] == self.board[c] != "":
                winner = "You" if self.board[a] == self.my_symbol else "Opponent"
                self.status_label.config(text=f"{winner} won!")
                self.is_my_turn = False
                return
        if "" not in self.board:
            self.status_label.config(text="It's a draw!")