# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__ = "arelin"
__date__ = "$Nov 7, 2015 6:23:50 AM$"

import socket
import subprocess
from tkinter import *
from tkinter.ttk import Button
from tkinter.ttk import Frame
from tkinter.ttk import Style

TCP_IP = '127.0.0.1'
TCP_PORT = 3006
BUFFER_SIZE = 1024

user = "frankcash"

def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""

def clear_text(x):
    x.e.delete(1.0, END)

def exitC(x):
    x.top.destroy()

def send_text(x):
    print(user)
    string_to_encrypt = x.e.get("1.0", END)
    print(string_to_encrypt)
    string_together = "keybase encrypt -m \"" + string_to_encrypt + "\" " + user
    status = subprocess.check_output(string_together, shell=True)

    status = status.decode('utf-8')
    print(status)
    justPGP = find_between(status, "-----BEGIN PGP MESSAGE-----", "-----END PGP MESSAGE-----")
    justPGP = "-----BEGIN PGP MESSAGE-----" + justPGP + "-----END PGP MESSAGE-----"
    justPGP = ' '.join((format(ord(x), 'b') for x in justPGP))
    f=open("info.dat",'w')
    f.write(justPGP)
    f.close();
    python2_env = {"PYTHONPATH":"/lib/python2.7"}
    process = subprocess.Popen("python2 txcode.py".split(), stdout=subprocess.PIPE, env=python2_env)
    
def change_user(x):
    top = x.top = Toplevel(x)
    top.wm_title("Change User")
    Label(top, text="Keybase Username").pack()
    x.g = Entry(top)
    x.g.pack(padx=5)
    b = Button(top, text="OK", command=lambda: user_reg(x.g.get(), x))
    b.pack(pady=5)
    c = Button(top, text="Cancel", command=lambda: exitC(x))
    c.pack(pady=5)
 
def user_reg(given, x):
    global user 
    user = given
    x.top.destroy()
    
def exitC(x):
    x.top.destroy()

master = Tk()

master.title("Send Message")
master.style = Style()
master.style.theme_use("default")
master.e = Text(master)
master.e.pack(expand=1, fill=BOTH)
    #frame = Frame(self, relief=RAISED, borderwidth=1)
    #frame.pack(fill=BOTH, expand=1)
        
#master.pack(fill=BOTH, expand=1)

clearButton = Button(master, text="Clear", command=lambda: clear_text(master))
clearButton.pack(side=RIGHT, padx=5, pady=5)
okButton = Button(master, text="Send", command=lambda: send_text(master))
okButton.pack(side=RIGHT, padx=5, pady=5)
changeUser = Button(master, text="Change User", command=lambda: change_user(master))
changeUser.pack(side=RIGHT, padx=5, pady=5)

mainloop()