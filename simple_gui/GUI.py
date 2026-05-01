import threading
import select
from tkinter import *
from chat_utils import *
import json

from sentiment_tools import analyze_sentiment
from image_gen import generate_image
from nlp_tools import extract_keywords, simple_summary


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

        # sentiment
        label, emoji = analyze_sentiment(msg)
        self.display_message(f"[{label} {emoji}] You: {msg}")

        self.chat_history.append(msg)
        self.my_msg = msg

    # ================= RECEIVE =================
    def proc(self):
        while True:
            read, _, _ = select.select([self.socket], [], [], 0)

            peer_msg = []
            if self.socket in read:
                peer_msg = self.recv()

            if self.my_msg or peer_msg:
                msg = self.sm.proc(self.my_msg, peer_msg)
                self.my_msg = ""

                if msg:
                    self.display_message(self.format_message(msg))

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