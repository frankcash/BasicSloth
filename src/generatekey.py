# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__ = "arelin"
__date__ = "$Nov 7, 2015 6:05:27 AM$"

from tkinter import Tk, RIGHT, BOTH, RAISED, Text, END, Toplevel, Label, Entry
from tkinter.ttk import Frame, Button, Style
import os




            
def initUI(self):
     
    self.parent.title("Send Message")
    self.style = Style()
    self.style.theme_use("default")
    self.e = Text(self)
    self.e.pack(expand = 1, fill= BOTH)
        #frame = Frame(self, relief=RAISED, borderwidth=1)
        #frame.pack(fill=BOTH, expand=1)
        
    self.pack(fill=BOTH, expand=1)
        
    createButton = Button(self, text="New User", command=self.create_key)
    createButton.pack(side=RIGHT, padx=5, pady=5)
    closeButton = Button(self, text="Clear", command=self.clear_text)
    closeButton.pack(side=RIGHT, padx=5, pady=5)
    okButton = Button(self, text="Send", command=self.send_text)
    okButton.pack(side=RIGHT)
    
        
        
        
def clear_text(self):
    self.e.delete(1.0, END)

def send_text(self):
    string_to_encrypt = self.e.get("1.0",END)
        

def exitC(self):
    self.top.destroy()

def main():
  
    root = Tk()
    root.geometry("800x600+300+300")
    app = SDR(root)
    root.mainloop()  


if __name__ == '__main__':
    main()  
