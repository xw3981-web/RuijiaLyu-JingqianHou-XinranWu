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

# 导入你的AI机器人
from ai_client import ask_llm, set_personality, reset_chat


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

        # AI 机器人新增
        self.chatbot_window = None

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

        # ===================== 【新增】Chatbot 按钮 =====================
        Button(frame, text="🤖 Chatbot",
               command=self.open_chatbot_window).grid(row=0, column=5, padx=5)

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

    # ================= HELP =================
    def help_button(self):
        self.display_system(
"""HOW TO USE:

CHAT:
- just type message and send

SERVER COMMANDS:
who        → show users
c name     → connect user
time       → server time
bye        → disconnect
q          → quit

FEATURES:
Image      → generate AI image
Summary    → summarize last messages
Keywords   → extract important words
Chatbot    → AI private chat
@chatbot   → let bot reply in group

TIP:
Better summary if you chat on ONE topic
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

        # NLP commands
        if msg == "/summary":
            self.summary_button()
            return

        if msg == "/keywords":
            self.keywords_button()
            return

        # image shortcut
        if msg.startswith("/aipic:"):
            prompt = msg.replace("/aipic:", "").strip()
            self.display_message(f"[AI Image] {prompt}")

            try:
                generate_image(prompt)
                self.display_message("[Image Generated ✅]")
            except:
                self.display_message("[Image Failed ❌]")
            return
        
        if msg == "/ttt_accept":
            if hasattr(self, "pending_ttt_peer"):
                payload = json.dumps({"action": "game_ttt_accept", "target": self.pending_ttt_peer})
                self.send(payload)
                self.start_ttt_game(False) 
                self.display_message("[System] TicTacToe started!")
            return
        
        if msg.lower() in ["y", "yes", "ok"]:
            if hasattr(self, "pending_ttt_peer"):
                payload = json.dumps({"action": "game_ttt_accept", "target": self.pending_ttt_peer})
                self.send(payload)
                self.start_ttt_game(False)
                self.display_message("[System] Game Start! ")
                delattr(self, "pending_ttt_peer") 
                return

        # ===================== 【新增】@chatbot 群聊回复 =====================
        if msg.lower().startswith("@chatbot"):
            question = msg.replace("@chatbot", "").replace("@Chatbot", "").strip()
            self.display_message(f"You: {msg}")
            
            def bot_reply():
                ans = ask_llm(question)
                self.display_message(f"🤖 Bot: {ans}")
            threading.Thread(target=bot_reply, daemon=True).start()
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

            if peer_msg:
                try:
                    parsed = json.loads(peer_msg)
                    action = parsed.get("action")
                    if action == "game_snake_rank":
                    
                        self.Window.after(0, lambda p=parsed: self.display_message(f"🏆 [Leaderboard]\n{p['rank']}"))
                        peer_msg = "" 
                   
                    elif action == "game_ttt_invite":
                        self.pending_ttt_peer = parsed["from"]
                        self.Window.after(0, lambda p=parsed: self.display_message(f"🎮 {p['from']} Invite you to play tictactoe! Enter 'y' to start the game. "))
                        peer_msg = ""

                    elif action == "game_ttt_accept":
                        self.Window.after(0, lambda: self.start_ttt_game(True)) 
                        self.Window.after(0, lambda: self.display_message("[System] Opponent accepted. TicTacToe started!"))
                        peer_msg = ""

                    elif action == "game_ttt_move":
                   
                        if hasattr(self, "ttt_game") and self.ttt_game:
                            self.Window.after(0, lambda p=parsed: self.ttt_game.apply_opponent_move(p["move"]))
                        peer_msg = ""
                except Exception:
                    pass 

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

    # ================= RUN =================
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
            self.display_message("[System] Please connect to a user (c [name]) first!")
            return
        msg = json.dumps({"action": "game_ttt_invite", "target": self.sm.peer})
        self.send(msg)
        self.display_message(f"[System] Invite sent to {self.sm.peer}. Waiting for accept...")

    def start_ttt_game(self, is_first):
        my_symbol = "X" if is_first else "O"
        self.ttt_game = TicTacToeGame(self.Window, is_first, my_symbol, self.send_ttt_move)

    def send_ttt_move(self, index):
        peer = self.sm.peer if self.sm.get_state() == S_CHATTING else getattr(self, "pending_ttt_peer", "")
        if peer:
            payload = json.dumps({"action": "game_ttt_move", "target": peer, "move": index})
            self.send(payload) 

    # ===================== 【新增】AI 机器人窗口 =====================
    def open_chatbot_window(self):
        if self.chatbot_window and self.chatbot_window.winfo_exists():
            self.chatbot_window.lift()
            return

        win = Toplevel(self.Window)
        win.title("🤖 AI Chatbot")
        win.geometry("450x500")
        win.configure(bg="#2C3E50")
        self.chatbot_window = win

        # 聊天显示
        chat_text = Text(win, bg="#34495E", fg="white", font="Helvetica 11")
        chat_text.pack(fill=BOTH, expand=True, padx=10, pady=10)
        chat_text.config(state=DISABLED)
        self.chatbot_text = chat_text

        # 人格选择
        p_frame = Frame(win, bg="#2C3E50")
        p_frame.pack(fill=X, padx=10)
        Label(p_frame, text="Personality:", bg="#2C3E50", fg="white").pack(side=LEFT)
        self.p_var = StringVar(value="friendly")
        for p in ["friendly", "funny", "professional", "sarcastic"]:
            Radiobutton(p_frame, text=p.capitalize(), variable=self.p_var, value=p,
                        bg="#2C3E50", fg="white", command=lambda: set_personality(self.p_var.get())).pack(side=LEFT, padx=3)

        # 输入框
        entry = Entry(win, font="Helvetica 12")
        entry.pack(fill=X, padx=10, pady=5)
        self.chatbot_entry = entry

        # 按钮
        btn_frame = Frame(win, bg="#2C3E50")
        btn_frame.pack(fill=X, padx=10, pady=3)
        Button(btn_frame, text="Send", command=self.send_to_chatbot, bg="white", fg="black").pack(side=LEFT, expand=True, fill=X)
        Button(btn_frame, text="Clear", command=self.clear_chatbot, bg="white", fg="black").pack(side=LEFT, expand=True, fill=X)

        # 欢迎语
        self.append_bot_msg("Hello! I'm your AI chatbot 😊")

    def append_bot_msg(self, text):
        t = self.chatbot_text
        t.config(state=NORMAL)
        t.insert(END, f"🤖 Bot: {text}\n\n")
        t.see(END)
        t.config(state=DISABLED)

    def append_user_msg(self, text):
        t = self.chatbot_text
        t.config(state=NORMAL)
        t.insert(END, f"You: {text}\n")
        t.see(END)
        t.config(state=DISABLED)

    def clear_chatbot(self):
        reset_chat()
        t = self.chatbot_text
        t.config(state=NORMAL)
        t.delete(1.0, END)
        self.append_bot_msg("Chat cleared!")
        t.config(state=DISABLED)

    def send_to_chatbot(self):
        msg = self.chatbot_entry.get().strip()
        if not msg:
            return
        self.chatbot_entry.delete(0, END)
        self.append_user_msg(msg)

        def reply():
            res = ask_llm(msg)
            self.append_bot_msg(res)
        threading.Thread(target=reply, daemon=True).start()