import tkinter as tk
import random

class SnakeGame(tk.Toplevel):
    def __init__(self, parent, on_game_over):
        super().__init__(parent)
        self.title("🐍 Snake Game")
        self.geometry("400x450")
        self.on_game_over = on_game_over
        
        self.score = 0
        self.score_label = tk.Label(self, text=f"Score: {self.score}", font=("Helvetica", 14))
        self.score_label.pack(pady=5)
        
        self.canvas = tk.Canvas(self, width=400, height=400, bg="black")
        self.canvas.pack()
        
        self.snake = [(200, 200), (190, 200), (180, 200)]
        self.food = self.place_food()
        self.direction = "Right"
        self.running = True
        
        self.bind("<KeyPress>", self.change_direction)
        self.update_snake()

        self.direction = "Right"
        self.running = True
        
        self.bind("<KeyPress>", self.change_direction)
        
        self.focus_force() 
        
        self.update_snake()

    def place_food(self):
        x = random.randint(0, 39) * 10
        y = random.randint(0, 39) * 10
        return (x, y)

    def change_direction(self, event):
        if event.keysym in ["Up", "Down", "Left", "Right"]:
            # 防止反向移动
            if (event.keysym == "Up" and self.direction != "Down") or \
               (event.keysym == "Down" and self.direction != "Up") or \
               (event.keysym == "Left" and self.direction != "Right") or \
               (event.keysym == "Right" and self.direction != "Left"):
                self.direction = event.keysym

    def update_snake(self):
        if not self.running: return
        
        head_x, head_y = self.snake[0]
        if self.direction == "Up": head_y -= 10
        elif self.direction == "Down": head_y += 10
        elif self.direction == "Left": head_x -= 10
        elif self.direction == "Right": head_x += 10
        
        new_head = (head_x, head_y)
        
        # 撞墙或撞自己，游戏结束
        if head_x < 0 or head_x >= 400 or head_y < 0 or head_y >= 400 or new_head in self.snake:
            self.running = False
            self.canvas.create_text(200, 200, text=f"GAME OVER\nScore: {self.score}", fill="white", font=("Helvetica", 20))
            self.on_game_over(self.score) # 把分数传给聊天系统
            return
            
        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 10
            self.score_label.config(text=f"Score: {self.score}")
            self.food = self.place_food()
        else:
            self.snake.pop()
            
        self.canvas.delete("all")
        self.canvas.create_rectangle(self.food[0], self.food[1], self.food[0]+10, self.food[1]+10, fill="red")
        for x, y in self.snake:
            self.canvas.create_rectangle(x, y, x+10, y+10, fill="green")
            
        self.after(100, self.update_snake)