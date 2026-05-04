#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Beautiful Chatroom GUI - Menu Removed from Chat Display
"""

import threading
import select
from tkinter import *
from chat_utils import *
import json
import os


class GUI:
    def __init__(self, send, recv, sm, s):
        self.Window = Tk()
        self.Window.withdraw()

        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s

        self.my_msg = ""
        self.system_msg = ""
        self.mode = "chat"

    # ---------------- USER STORAGE ----------------
    def load_users(self):
        if not os.path.exists("users.json"):
            with open("users.json", "w") as f:
                json.dump({}, f)
        with open("users.json", "r") as f:
            return json.load(f)

    def save_users(self, users):
        with open("users.json", "w") as f:
            json.dump(users, f)

    # ---------------- POPUP ----------------
    def show_popup(self, icon, title, subtitle, color):
        popup = Toplevel()
        popup.title(title)
        popup.geometry("330x220")
        popup.configure(bg="white")
        popup.resizable(False, False)

        Label(popup, text=icon, font=("Helvetica", 38), bg="white").pack(pady=(18, 8))
        Label(popup, text=title, font=("Helvetica", 18, "bold"), fg=color, bg="white").pack()
        Label(popup, text=subtitle, font=("Helvetica", 11), fg="#666", bg="white").pack(pady=8)

        Button(
            popup,
            text="OK",
            font=("Helvetica", 11, "bold"),
            bg=color,
            fg="black",
            relief=FLAT,
            command=popup.destroy
        ).pack(pady=18, ipadx=25, ipady=6)

        popup.grab_set()
        popup.wait_window()

    def show_success_popup(self):
        self.show_popup("🎉", "Login Successful!", "Welcome back", "#4A90E2")

    def show_signup_popup(self):
        self.show_popup("🌸", "Account Created!", "Please log in", "#50C878")

    def show_error_popup(self, message):
        self.show_popup("❌", "Oops!", message, "#FF6B6B")

    # ---------------- LOGIN PAGE ----------------
    def login(self):
        self.login_win = Toplevel()
        self.login_win.title("Chatroom Login")
        self.login_win.geometry("500x550")
        self.login_win.configure(bg="#EAF4FF")
        self.login_win.resizable(False, False)

        Label(self.login_win, text="☁️ ✨ 💬 ✨ ☁️", font=("Helvetica", 24), bg="#EAF4FF", fg="#4A90E2").pack(pady=18)
        Label(self.login_win, text="Welcome to Chatroom", font=("Helvetica", 22, "bold"), bg="#EAF4FF", fg="#2E5AAC").pack()

        frame = Frame(self.login_win, bg="white")
        frame.pack(pady=30, padx=40, fill="both", expand=True)

        Label(frame, text="Username", font=("Helvetica", 12, "bold"), bg="white").pack(pady=(35, 5))
        self.entryName = Entry(frame, font=("Helvetica", 13))
        self.entryName.pack(ipady=10, ipadx=70)

        Label(frame, text="Password", font=("Helvetica", 12, "bold"), bg="white").pack(pady=(25, 5))
        self.entryPassword = Entry(frame, font=("Helvetica", 13), show="*")
        self.entryPassword.pack(ipady=10, ipadx=70)

        Button(frame, text="Log In", font=("Helvetica", 12, "bold"), bg="#4A90E2", fg="black", relief=FLAT, command=self.login_user).pack(pady=(35, 15), ipadx=40, ipady=8)
        Button(frame, text="Sign Up", font=("Helvetica", 12, "bold"), bg="#50C878", fg="black", relief=FLAT, command=self.signup_user).pack(ipadx=40, ipady=8)

        self.Window.mainloop()

    # ---------------- SIGNUP/LOGIN LOGIC ----------------
    def signup_user(self):
        username = self.entryName.get().strip()
        password = self.entryPassword.get().strip()
        users = self.load_users()
        if username == "" or password == "":
            self.show_error_popup("Username/password cannot be empty")
            return
        if username in users:
            self.show_error_popup("Username already exists")
            return
        users[username] = password
        self.save_users(users)
        self.show_signup_popup()

    def login_user(self):
        username = self.entryName.get().strip()
        password = self.entryPassword.get().strip()
        users = self.load_users()
        if username not in users:
            self.show_error_popup("Username not found")
            return
        if users[username] != password:
            self.show_error_popup("Wrong password")
            return
        self.goAhead(username)

    def goAhead(self, name):
        msg = json.dumps({"action": "login", "name": name})
        self.send(msg)
        response = json.loads(self.recv())

        if response["status"] == "ok":
            self.show_success_popup()
            self.login_win.destroy()
            self.sm.set_state(S_LOGGEDIN)
            self.sm.set_myname(name)
            self.show_menu(name)
            process = threading.Thread(target=self.proc)
            process.daemon = True
            process.start()
        else:
            self.show_error_popup("Login failed")

    # ---------------- MAIN MENU (Buttons) ----------------
    def show_menu(self, name):
        self.Window.deiconify()
        self.Window.title("Main Menu")
        self.Window.geometry("500x500")
        self.Window.configure(bg="#F4F7FB")

        for widget in self.Window.winfo_children():
            widget.destroy()

        Label(self.Window, text=f"Welcome, {name}", font=("Helvetica", 22, "bold"), bg="#F4F7FB", fg="#2E5AAC").pack(pady=35)

        # 每个按钮进入对应的 Mode
        Button(self.Window, text="🎮 Online Game", font=("Helvetica", 16, "bold"), bg="#FFD166", fg="black", width=20, height=2, command=lambda: None).pack(pady=20)
        Button(self.Window, text="🤖 Chatbot", font=("Helvetica", 16, "bold"), bg="#4A90E2", fg="black", width=20, height=2, command=self.enter_chatbot_mode).pack(pady=20)
        Button(self.Window, text="💬 Chat", font=("Helvetica", 16, "bold"), bg="#50C878", fg="black", width=20, height=2, command=self.enter_chat_mode).pack(pady=20)

    # ---------------- MODE SWITCHING ----------------
    def enter_chatbot_mode(self):
        self.mode = "chatbot"
        self.sm.set_mode("chatbot")
        self.create_chat_window("🤖 Chatbot Mode")

    def enter_chat_mode(self):
        self.mode = "chat"
        self.sm.set_mode("chat")
        self.create_chat_window("💬 Chat Mode")

    # ---------------- CHAT WINDOW ----------------
    def create_chat_window(self, title):
        for widget in self.Window.winfo_children():
            widget.destroy()

        self.Window.geometry("520x620") # 稍微调高一点高度
        
        # 顶部标题栏
        header = Frame(self.Window, bg="#4A90E2")
        header.pack(fill=X)
        
        Label(header, text=title, font=("Helvetica", 18, "bold"), bg="#4A90E2", fg="white", pady=14).pack(side=LEFT, padx=20)
        
        # 返回菜单按钮 (为了方便切换 Mode)
        Button(header, text="Back", font=("Helvetica", 10, "bold"), bg="#2E5AAC", fg="white", command=lambda: self.show_menu(self.sm.get_myname())).pack(side=RIGHT, padx=20)

        self.textCons = Text(self.Window, bg="white", fg="#222", font=("Helvetica", 12), padx=10, pady=10)
        self.textCons.place(x=20, y=70, width=480, height=400)
        self.textCons.config(state=DISABLED)

        self.entryMsg = Entry(self.Window, font=("Helvetica", 13))
        self.entryMsg.place(x=20, y=490, width=350, height=40)
        self.entryMsg.bind("<Return>", lambda e: self.sendButton(self.entryMsg.get())) # 绑定回车键

        Button(self.Window, text="Send", font=("Helvetica", 12, "bold"), bg="#4A90E2", fg="black", command=lambda: self.sendButton(self.entryMsg.get())).place(x=390, y=490, width=110, height=40)

    # ---------------- SEND ----------------
    def sendButton(self, msg):
        if msg.strip() == "":
            return
        
        # UI 直接清空输入框
        self.my_msg = msg
        self.entryMsg.delete(0, END)

    # ---------------- RECEIVE LOOP ----------------
    def proc(self):
        while True:
            read, _, _ = select.select([self.socket], [], [], 0.1)
            peer_msg = ""
            if self.socket in read:
                peer_msg = self.recv()

            if len(self.my_msg) > 0 or len(peer_msg) > 0:
                # 调用 SM 逻辑
                response = self.sm.proc(self.my_msg, peer_msg)
                self.my_msg = ""

                if response and response.strip() != "":
                    # 这里只会显示聊天内容，因为 SM 里的 menu 已经被删掉了
                    self.textCons.config(state=NORMAL)
                    self.textCons.insert(END, response) 
                    self.textCons.config(state=DISABLED)
                    self.textCons.see(END)

    def run(self):
        self.login()

if __name__ == "__main__":
    print("Run via client launcher.")
