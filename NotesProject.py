import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
import datetime
import threading
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Database setup
def init_db():
    conn = sqlite3.connect('notes.db')
    cursor = conn.cursor()
    
    # Drop and recreate the notes table
    cursor.execute('DROP TABLE IF EXISTS notes')
    cursor.execute('''
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title TEXT,
            content TEXT,
            category TEXT,
            reminder_time TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create the users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# User authentication
class Auth:
    def __init__(self):
        self.current_user = None
        self.current_email = None

    def register(self, username, password, email):
        conn = sqlite3.connect('notes.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', (username, password, email))
            conn.commit()
            messagebox.showinfo("Success", "Registration successful!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists.")
        finally:
            conn.close()

    def login(self, username, password):
        conn = sqlite3.connect('notes.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            self.current_user = user[0]  
            self.current_email = user[3] 
            return True
        return False

# Notes management
class NoteManager:
    def __init__(self, user_id):
        self.user_id = user_id

    def add_note(self, title, content, category, reminder_time=None):
        conn = sqlite3.connect('notes.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notes (user_id, title, content, category, reminder_time) VALUES (?, ?, ?, ?, ?)",
                       (self.user_id, title, content, category, reminder_time))
        conn.commit()
        conn.close()

    def get_notes(self):
        conn = sqlite3.connect('notes.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notes WHERE user_id=?', (self.user_id,))
        notes = cursor.fetchall()
        conn.close()
        return notes

    def delete_note(self, note_id):
        conn = sqlite3.connect('notes.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM notes WHERE id=?', (note_id,))
        conn.commit()
        conn.close()

    def edit_note(self, note_id, title, content, category, reminder_time=None):
        conn = sqlite3.connect('notes.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE notes
            SET title=?, content=?, category=?, reminder_time=?
            WHERE id=?
        ''', (title, content, category, reminder_time, note_id))
        conn.commit()
        conn.close()

# Reminder feature
def send_email(subject, body, to_email):
    from_email = "shraddhak293@gmail.com" 
    from_password = "dbdh rnxj zdhw bbdl" 

    smtp_server = "smtp.gmail.com"
    smtp_port = 587 
    
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain')) 
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_reminders(master, auth):
    while True:
        conn = sqlite3.connect('notes.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, reminder_time FROM notes WHERE reminder_time IS NOT NULL')
        reminders = cursor.fetchall()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for note_id, title, reminder_time in reminders:
            if reminder_time <= current_time:
                master.after(0, lambda t=title: messagebox.showinfo("Reminder", f"Reminder: {t}"))
                master.after(0, lambda: send_email("Reminder", f"Reminder for your note: {title}", auth.current_email))
                cursor.execute('UPDATE notes SET reminder_time = NULL WHERE id = ?', (note_id,))
                conn.commit()
        time.sleep(60)  

# In the NoteApp class
def login(self):
    username = self.username_entry.get()
    password = self.password_entry.get()
    if self.auth.login(username, password):
        self.login_frame.pack_forget()
        self.note_manager = NoteManager(self.auth.current_user)  
        self.show_notes()
        threading.Thread(target=check_reminders, args=(self.master, self.auth), daemon=True).start()  
    else:
        messagebox.showerror("Error", "Invalid credentials")

# GUI Application
class NoteApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Pin Your Note")
        self.auth = Auth()
        self.note_manager = None 

        self.login_frame = tk.Frame(self.master)
        self.login_frame.pack(padx=10, pady=10)

        tk.Label(self.login_frame, text="Username").grid(row=0, column=0)
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1)

        tk.Label(self.login_frame, text="Password").grid(row=1, column=0)
        self.password_entry = tk.Entry(self.login_frame, show='*')
        self.password_entry.grid(row=1, column=1)

        tk.Label(self.login_frame, text="Email").grid(row=2, column=0)
        self.email_entry = tk.Entry(self.login_frame)
        self.email_entry.grid(row=2, column=1)

        tk.Button(self.login_frame, text="Login", command=self.login).grid(row=3, column=0, columnspan=2)
        tk.Button(self.login_frame, text="Register", command=self.register).grid(row=4, column=0, columnspan=2)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if self.auth.login(username, password):
            self.login_frame.pack_forget()
            self.note_manager = NoteManager(self.auth.current_user)  
            self.show_notes()
            threading.Thread(target=check_reminders, args=(self.master,self.auth), daemon=True).start()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        email = self.email_entry.get()
        self.auth.register(username, password, email)

    def show_notes(self):
        self.notes_frame = tk.Frame(self.master)
        self.notes_frame.pack(padx=10, pady=10)

        self.note_listbox = tk.Listbox(self.notes_frame, width=50)
        self.note_listbox.pack(side=tk.LEFT)

        self.scrollbar = tk.Scrollbar(self.notes_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.note_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.note_listbox.yview)

        tk.Button(self.master, text="Add Note", command=self.add_note).pack(pady=5)
        tk.Button(self.master, text="Edit Note", command=self.edit_note).pack(pady=5)
        tk.Button(self.master, text="Delete Note", command=self.delete_note).pack(pady=5)

        self.load_notes()

    def load_notes(self):
        self.note_listbox.delete(0, tk.END)
        notes = self.note_manager.get_notes()
        for note in notes:
            self.note_listbox.insert(tk.END, f"Title : {note[2]} , Content : {note[3]} , Category : {note[4]}")  # Title - Content

    def add_note(self):
        title = simpledialog.askstring("Title", "Enter note title:")
        content = simpledialog.askstring("Content", "Enter note content:")
        category = simpledialog.askstring("Category", "Enter note category:")
        reminder_time = simpledialog.askstring("Reminder", "Enter reminder time (YYYY-MM-DD HH:MM:SS) or leave blank:")
    
        if not title or not content or not category:
            messagebox.showwarning("Warning", "All fields must be filled out.")
            return

        self.note_manager.add_note(title, content, category, reminder_time)
        self.load_notes()

    def edit_note(self):
        selected_note = self.note_listbox.curselection()
        if selected_note:
            note_id = self.note_manager.get_notes()[selected_note[0]][0] 
            old_note = self.note_manager.get_notes()[selected_note[0]]
            title = simpledialog.askstring("Title", "Edit note title:", initialvalue=old_note[2])
            content = simpledialog.askstring("Content", "Edit note content:", initialvalue=old_note[3])
            category = simpledialog.askstring("Category", "Edit note category:", initialvalue=old_note[4])
            reminder_time = simpledialog.askstring("Reminder", "Edit reminder time (YYYY-MM-DD HH:MM:SS) or leave blank:", initialvalue=old_note[5])
            if title and content and category:
                self.note_manager.edit_note(note_id, title, content, category, reminder_time)
                self.load_notes()
            else:
                messagebox.showwarning("Warning", "All fields must be filled out.")
        else:
            messagebox.showwarning("Warning", "Select a note to edit.")

    def delete_note(self):
        selected_note = self.note_listbox.curselection()
        if selected_note:
            note_id = self.note_manager.get_notes()[selected_note[0]][0]  
            self.note_manager.delete_note(note_id)
            self.load_notes()
        else:
            messagebox.showwarning("Warning", "Select a note to delete.")

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = NoteApp(root)
    root.mainloop()
