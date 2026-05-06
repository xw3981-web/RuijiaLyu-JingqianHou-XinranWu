import threading
import select
from tkinter import *
from chat_utils import *
import json

from sentiment_tools import analyze_sentiment
from image_gen import generate_image
from nlp_tools import extract_keywords, simple_summary
from game_snake import SnakeGame
from game_tictactoe import TicTacToeGame

# 👉 chatbot
from ai_client import ask_llm


class GUI:
    def __init__(self, send, recv, sm, s):
        self.Window = Tk()
        self.Window.withdraw()

        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s

        self.my_msg = ""
        self.chat_history = []

        # ================= CHATBOT MEMORY =================
        self.bot_messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a friendly chatbot in a chat room. Keep replies short and helpful."}]
            }
        ]

    # ================= LOGIN =================
    def login(self):
        self.login = Toplevel()
        self.login.title("Login")
        self.login.geometry("400x250")

        Label(self.login, text="Enter Username",
              font="Helvetica 14 bold").pack(pady=20)

        self.entryName = Entry(self.login, font="Helvetica 14")
        self.entryName.pack(pady=10)
        self.entryName.focus()

        Button(self.login, text="CONTINUE",
               command=lambda: self.goAhead(self.entryName.get())
               ).pack(pady=20)

        self.Window.mainloop()

    def goAhead(self, name):
        if len(name) > 0:
            msg = json.dumps({"action": "login", "name": name})
            self.send(msg)

            response = json.loads(self.recv())
            if response["status"] == 'ok':
                self.login.destroy()

                self.sm.set_state(S_LOGGEDIN)
                self.sm.set_myname(name)

                self.layout(name)

                self.display_system("Welcome to Chat System 🚀")
                self.help_button()

                process = threading.Thread(target=self.proc)
                process.daemon = True
                process.start()

    # ================= LAYOUT =================
    def layout(self, name):
        self.name = name

        self.Window.deiconify()
        self.Window.title("Chat Room")
        self.Window.geometry("560x700")
        self.Window.configure(bg="#17202A")

        Label(self.Window, text=f"User: {name}",
              bg="#17202A", fg="white",
              font="Helvetica 14 bold").pack(pady=5)

        self.textCons = Text(self.Window, bg="#17202A",
                             fg="#EAECEE", font="Helvetica 13")
        self.textCons.pack(expand=True, fill=BOTH)
        self.textCons.config(state=DISABLED)

        self.entryMsg = Entry(self.Window,
                              bg="#2C3E50",
                              fg="white",
                              font="Helvetica 13")
        self.entryMsg.pack(fill=X, pady=5)
        self.entryMsg.focus()

        # ================= BUTTONS =================
        frame = Frame(self.Window)
        frame.pack(pady=5)

        Button(frame, text="Send",
               command=lambda: self.sendButton(self.entryMsg.get())
               ).grid(row=0, column=0, padx=5)

        Button(frame, text="Image",
               command=self.aipic_button).grid(row=0, column=1, padx=5)

        Button(frame, text="Summary",
               command=self.summary_button).grid(row=0, column=2, padx=5)

        Button(frame, text="Keywords",
               command=self.keywords_button).grid(row=0, column=3, padx=5)

        Button(frame, text="Help",
               command=self.help_button).grid(row=0, column=4, padx=5)

        # ================= GAME BUTTONS =================
        frame2 = Frame(self.Window, bg="#17202A")
        frame2.pack(pady=5)

        Button(frame2, text="🐍 Play Snake",
               command=self.start_snake).grid(row=0, column=0, padx=5)

        Button(frame2, text="❌⭕ Invite TicTacToe",
               command=self.invite_ttt).grid(row=0, column=1, padx=5)

    # ================= DISPLAY =================
    def display_message(self, msg):
        self.textCons.config(state=NORMAL)
        self.textCons.insert(END, msg + "\n\n")
        self.textCons.config(state=DISABLED)
        self.textCons.see(END)

    def display_system(self, msg):
        self.display_message(f"--- System ---\n{msg}\n--------------")

    # ================= CHATBOT =================
    def get_bot_reply(self, msg):
        self.bot_messages.append({
            "role": "user",
            "content": [{"type": "text", "text": msg}]
        })

        try:
            reply = ask_llm(msg)
        except:
            reply = "⚠️ Bot error"

        self.bot_messages.append({
            "role": "assistant",
            "content": [{"type": "text", "text": reply}]
        })

        if len(self.bot_messages) > 10:
            self.bot_messages = self.bot_messages[-10:]

        return reply

    # ================= HELP =================
    def help_button(self):
        self.display_system(
"""HOW TO USE:

CHAT:
- just type message and send
- @bot xxx  → ask chatbot

FEATURES:
Image      → generate AI image
Summary    → summarize last messages
Keywords   → extract important words
"""
        )

    # ================= IMAGE =================
    def aipic_button(self):
        prompt = self.entryMsg.get()
        if not prompt:
            return

        self.entryMsg.delete(0, END)
        self.display_message(f"[AI Image] {prompt}")

        try:
            generate_image(prompt)
            self.display_message("[Image Generated ✅]")
        except:
            self.display_message("[Image Failed ❌]")

    # ================= SUMMARY =================
    def summary_button(self):
        if len(self.chat_history) < 3:
            self.display_message("[System] Not enough data for summary")
            return

        summary = simple_summary(self.chat_history, n=3)

        self.display_message("[SUMMARY]")
        for s in summary:
            self.display_message(f"- {s}")

    # ================= KEYWORDS =================
    def keywords_button(self):
        if len(self.chat_history) < 2:
            self.display_message("[System] Not enough data")
            return

        keywords = extract_keywords(self.chat_history, top_k=6)

        self.display_message("[KEYWORDS]")
        self.display_message(", ".join(keywords))

    # ================= SEND =================
    def sendButton(self, msg):
        if not msg:
            return

        self.entryMsg.delete(0, END)

        # ===== chatbot trigger =====
        if msg.startswith("@bot"):
            user_msg = msg.replace("@bot", "").strip()
            self.display_message("[🤖 Bot thinking...]")

            def bot_task():
                reply = self.get_bot_reply(user_msg)
                self.Window.after(0, lambda: self.display_message(f"[🤖 Bot] {reply}"))

            threading.Thread(target=bot_task).start()
            return

        # NLP commands
        if msg == "/summary":
            self.summary_button()
            return

        if msg == "/keywords":
            self.keywords_button()
            return

        if msg.startswith("/aipic:"):
            prompt = msg.replace("/aipic:", "").strip()
            self.display_message(f"[AI Image] {prompt}")

            try:
                generate_image(prompt)
                self.display_message("[Image Generated ✅]")
            except:
                self.display_message("[Image Failed ❌]")
            return

        label, emoji = analyze_sentiment(msg)
        self.display_message(f"[{label} {emoji}] You: {msg}")

        self.chat_history.append(msg)
        self.my_msg = msg

    # ================= RECEIVE =================
    def proc(self):
        while True:
            read, _, _ = select.select([self.socket], [], [], 0)
            peer_msg = ""

            if self.socket in read:
                peer_msg = self.recv()

            if self.my_msg or peer_msg:
                msg = self.sm.proc(self.my_msg, peer_msg)
                self.my_msg = ""
                if msg:
                    self.Window.after(0, lambda m=msg: self.display_message(self.format_message(m)))

    # ================= FORMAT =================
    def format_message(self, msg):
        result = []
        for line in msg.split("\n"):
            line = line.strip()
            if not line:
                continue
            if "[" in line and "]" in line:
                try:
                    name = line.split("]")[0].replace("[", "")
                    content = line.split("]")[1].strip()
                    label, emoji = analyze_sentiment(content)
                    result.append(f"[{label} {emoji}] {name}: {content}")
                    self.chat_history.append(content)
                except:
                    result.append(line)
            else:
                result.append(line)
        return "\n".join(result)

    def run(self):
        self.login()

    # ================= GAMES =================
    def start_snake(self):
        SnakeGame(self.Window, self.on_snake_over)

    def on_snake_over(self, score):
        msg = json.dumps({"action": "game_snake_score", "score": score})
        self.send(msg)

    def invite_ttt(self):
        if self.sm.get_state() != S_CHATTING or not self.sm.peer:
            self.display_message("[System] Connect to a user first!")
            return
        msg = json.dumps({"action": "game_ttt_invite", "target": self.sm.peer})
        self.send(msg)

    def start_ttt_game(self, is_first):
        my_symbol = "X" if is_first else "O"
        self.ttt_game = TicTacToeGame(self.Window, is_first, my_symbol, self.send_ttt_move)

    def send_ttt_move(self, index):
        peer = self.sm.peer
        if peer:
            payload = json.dumps({"action": "game_ttt_move", "target": peer, "move": index})
            self.send(payload)
#基础bot功能 没有群聊+记忆