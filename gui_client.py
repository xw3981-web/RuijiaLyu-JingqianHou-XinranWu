import tkinter as tk
from tkinter import scrolledtext
import socket
import threading

class ChatGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("我的聊天室")
        
        # 显示消息的区域
        self.chat_area = scrolledtext.ScrolledText(self.root, width=50, height=20, state='disabled')
        self.chat_area.pack(padx=10, pady=10)
        
        # 输入框
        self.input_area = tk.Entry(self.root, width=40)
        self.input_area.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 发送按钮
        self.send_btn = tk.Button(self.root, text="发送", command=self.send_message)
        self.send_btn.pack(side=tk.LEFT, padx=5)
        
        # 连接服务器
        self.connect_to_server()
        
    def connect_to_server(self):
        """连接到聊天服务器"""
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(("127.0.0.1", 8888))  # 改成你服务器的IP和端口
        
        # 启动接收消息的线程
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
    def receive_messages(self):
        """不停接收服务器发来的消息"""
        while True:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message:
                    self.display_message(message)
            except:
                break
    
    def display_message(self, message):
        """在窗口上显示消息"""
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)  # 自动滚到底部
    
    def send_message(self):
        """发送消息"""
        message = self.input_area.get()
        if message.strip():
            self.client.send(message.encode('utf-8'))
            self.input_area.delete(0, tk.END)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ChatGUI()
    app.run()
