from tkinter import *
import tkinter.font as font
from PIL import Image, ImageTk
import serial
import time
import threading
from datetime import datetime

#Once both devices paired, find the port of the arduino
port = serial.Serial("/dev/rfcomm0", baudrate=9600, timeout=5)
if port.isOpen():
    print("Serial port opened properly")
    port.flush()

# Create the main window
root = Tk()
root.title("Syringe Cleaner 101")

#Start function and countdown
t = 100 #default value
def start(timerLabel):
    x = threading.Thread(target=counter_label(timerLabel))
    x.start()
    startButton['state'] = 'disable' #disable start button when the machine is running
    root.update_idletasks()
    root.update()    
    
    port.write("S".encode())
    
    # while True:
    #     root.update_idletasks()
    #     root.update()   
    #     #Reading actions made by arduino
    #     readArduinoString = port.readline().decode("utf-8")
    #     if readArduinoString.strip() != '':
    #         print(readArduinoString.strip())
    #         #readArduinoString = readArduinoString.decode("utf-8")
    #         if readArduinoString.strip() == "Washing":
    #             print("washing string")
    #             displayText.set("Washing")
    #             root.update_idletasks()
    #             root.update()

    #         if readArduinoString.strip() == "Drying":
    #             print("Drying string")
    #             displayText.set("Drying")
    #             root.update_idletasks()
    #             root.update()

    #         if readArduinoString.strip() == "Camera Checking":
    #             print("camera string")                
    #             displayText.set("Camera Checking")
    #             root.update_idletasks()
    #             root.update()

    #         if readArduinoString.strip() == "Finish":
    #             displayText.set("Finish")
    #             root.update_idletasks()
    #             root.update()
    #             break

def counter_label(timerLabel):
    def countdown():
        print("recursive")
        global t

        if (t == 100): #default value
            display = "Started"
            t = 0
        else:
            tt = datetime.fromtimestamp(t)
            string = tt.strftime("%H:%M:%S")
            display=string
        timerLabel.config(text =display) 
        root.update_idletasks()
        root.update()
        t = t + 1
        root.after(1000, countdown)

    countdown()
    





"""
    while True:
	    print("DIGITAL LOGIC -- > SENDING...")
	    port.write(str(3))
	    rcv = port.readline()
	    if rcv:
	        print(rcv)
	    time.sleep( 3 )
"""

""" 
def stop():
    displayText.set("stop") 
"""
if __name__ == '__main__':
    #getting screen width and height of display
    width= root.winfo_screenwidth() 
    height= root.winfo_screenheight()
    #setting tkinter window size
    root.geometry("%dx%d" % (width, height))
    f1 = Frame()
    f1.place(anchor="c", relx=.5, rely=.25)

    #Initialize the elements of the tkinter window    
    btnFont = font.Font(size=12)


    timerLabel = Label(f1)
    timerLabel.config(text="Welcome")
    timerLabel.config(width=20, height=3)
    timerLabel.config(font=("Courier", 16))
    timerLabel.grid(row=0,column=0,sticky="s")

    #Display Status Label
    displayText = StringVar()
    displayText.set("Syringe Cleaner 101")
        
    displayLabel = Label(f1, textvariable=displayText)
    displayLabel.config(width=20, height=3)
    displayLabel.config(font=("Courier", 16))
    displayLabel.grid(row=1,column=0,sticky="s")

    startImg = Image.open(r"play-button.png")
    startImg = startImg.resize((40, 40))
    startPhoto = ImageTk.PhotoImage(startImg)

    #Start button

    startButton = Button(f1, text="Start", image = startPhoto, compound=LEFT, command=lambda:start(timerLabel))
    startButton['font'] = btnFont
    startButton.grid(row=2, column=0, sticky="ew")
    """
    stopImg = Image.open(r"no-stopping.png")
    stopImg = stopImg.resize((40, 40))
    stopPhoto = ImageTk.PhotoImage(stopImg)

    stopButton = Button(f1, text="Stop", image = stopPhoto, compound=LEFT, command=stop)
    stopButton['font'] = btnFont
    stopButton.grid(row=1, column=1, sticky="ew")
    """

    root.resizable(False, False) 
    root.mainloop()


