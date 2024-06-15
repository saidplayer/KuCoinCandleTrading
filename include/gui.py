from tkinter import *
from tkinter import scrolledtext
import threading

def run_gui():
    mainRT = Tk()
    mainRT.resizable(False, False) 
    mainRT.title("Crypto analyzer")

    Label(mainRT,text="Open order state:").grid(row=0, column=0, sticky="w", padx=2, pady=1)
    aa = scrolledtext.ScrolledText(mainRT,width=50,height=10)
    aa.grid(row=1,column=0,sticky="we",columnspan=4, padx=2, pady=1)
    aa.bind("<Key>", lambda e: "break")
    Label(mainRT,text="What is happening:").grid(row=2, column=0, sticky="w", padx=2, pady=1)
    bb = scrolledtext.ScrolledText(mainRT,width=50,height=10)
    bb.grid(row=3,column=0,sticky="we",columnspan=4, padx=2, pady=1)
    bb.bind("<Key>", lambda e: "break")

    btnStart = Button(mainRT, text="Analyze!", padx=10, pady=2 , command=lambda: candle_polling)
    btnStart.grid(row=4,column=0,pady=2,padx=10)

    btnStop = Button(mainRT, text="Download data", padx=10, pady=2 , command=lambda: runThread(pullData))
    btnStop.grid(row=4,column=1,pady=2,padx=10)

    btnReset = Button(mainRT, text=" Reset DB ", padx=10, pady=2 , command=lambda: aa.delete(1.0,END))
    btnReset.grid(row=4,column=2,pady=2,padx=10)

    mainRT.mainloop()
