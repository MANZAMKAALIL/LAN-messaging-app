import socket
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, scrolledtext
import os

# Server configuration
HOST = '127.0.0.1'
PORT = 35172

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("JKChat")
        self.root.geometry("800x600")
        self.username = simpledialog.askstring("Welcome", "Enter your username:")
        if not self.username:
            self.root.destroy()
            return

        # Socket setup
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((HOST, PORT))
        self.client_socket.send(self.username.encode('utf-8'))

        # UI Elements
        self.user_list = tk.Listbox(self.root, width=25, height=30)
        self.user_list.grid(row=0, column=0, padx=10, pady=10, sticky="ns")

        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=50, height=30)
        self.chat_area.grid(row=0, column=1, padx=10, pady=10)
        self.chat_area.config(state=tk.DISABLED)

        self.entry_message = tk.Entry(self.root, width=40)
        self.entry_message.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.grid(row=1, column=1, sticky="e", padx=10, pady=5)

        #self.delete_button = tk.Button(self.root, text="Delete Conversation", command=self.delete_conversation)
        #self.delete_button.grid(row=2, column=1, sticky="e", padx=10, pady=5)

        self.file_button = tk.Button(self.root, text="Send File", command=self.send_file)
        self.file_button.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        self.target_user = None
        self.user_list.bind("<<ListboxSelect>>", self.select_user)

        # Start receiving messages
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def select_user(self, event):
        try:
            self.target_user = self.user_list.get(self.user_list.curselection())
        except:
            self.target_user = None

    def send_message(self):
        message = self.entry_message.get()
        if not message or not self.target_user:
            messagebox.showwarning("Warning", "Select a user and write a message!")
            return
        self.client_socket.send(f"TO:{self.target_user}:{message}".encode('utf-8'))
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"You to {self.target_user}: {message}\n")
        self.chat_area.config(state=tk.DISABLED)
        self.entry_message.delete(0, tk.END)

    def send_file(self):
        if not self.target_user:
            messagebox.showwarning("Warning", "Select a user to send a file!")
            return
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        file_name = os.path.basename(file_path)
        self.client_socket.send(f"TO:{self.target_user}:FILE:{file_name}".encode('utf-8'))
        with open(file_path, 'rb') as f:
            self.client_socket.sendall(f.read())
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"You sent a file to {self.target_user}: {file_name}\n")
        self.chat_area.config(state=tk.DISABLED)

    def delete_conversation(self):
        if not self.target_user:
            messagebox.showwarning("Warning", "Select a user to delete the conversation!")
            return
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete(1.0, tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message.startswith("CLIENT_LIST:"):
                    clients = message.split(":", 1)[1].split(",")
                    self.user_list.delete(0, tk.END)
                    for client in clients:
                        if client != self.username:
                            self.user_list.insert(tk.END, client)
                else:
                    self.chat_area.config(state=tk.NORMAL)
                    self.chat_area.insert(tk.END, f"{message}\n")
                    self.chat_area.config(state=tk.DISABLED)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()
