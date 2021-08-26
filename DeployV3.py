# Import packages
from tkinter import *
import tkinter.font as font
from PIL import Image, ImageTk
import serial
import time
import threading
import os
import argparse
import cv2
import numpy as np
import sys
import glob
import importlib.util
import pathlib
import io
import time
import picamera
from PIL import Image
from pycoral.utils import edgetpu
from pycoral.utils import dataset
from pycoral.adapters import common
from pycoral.adapters import classify
from tflite_runtime.interpreter import Interpreter
from tflite_runtime.interpreter import load_delegate

# CV Configurations:
# Label Map File
LABELMAP_NAME = "labelmap.txt"
# Image Directory
IM_DIR = "images"
# Working Directory for Model & LabelMap
WORKING_DIR = "model"
# Model Name
GRAPH_NAME = "model_edgetpu.tflite"
# Get path to current working directory
CWD_PATH = os.getcwd()
# Path to .tflite file, which contains the model that is used for object detection
PATH_TO_CKPT = os.path.join(CWD_PATH, WORKING_DIR, GRAPH_NAME)
# Path to label map file
PATH_TO_LABELS = os.path.join(CWD_PATH, WORKING_DIR, LABELMAP_NAME)


#Once both devices paired, find the port of the arduino
port = serial.Serial("/dev/rfcomm0", baudrate=9600, timeout=5)
port.flush()

# Create the main window
root = Tk()
root.title("Syringe Cleaner 101")

#Start function and countdown
t = 3600
def start():
    displayText.set("Started")
    # x = threading.Thread(target=countdown)
    # x.start()
    
    startButton['state'] = 'disable' #disable start button when the machine is running
    root.update_idletasks()
    root.update()    
    port.write("S".encode()) # send start msg to Arduino

    # result = captureImage()
    # print("result is " + result)
    while True:
        root.update_idletasks()
        root.update() 

        #Reading actions made by arduino
        readArduinoString = port.readline().decode("utf-8").strip()
        if readArduinoString!='' :
            print (readArduinoString)
            # readArduinoString = readArduinoString.decode("utf-8")
            if readArduinoString == "Washing":
                displayText.set("Washing")
                root.update_idletasks()
                root.update() 

            if readArduinoString == "Drying":
                displayText.set("Drying")
                root.update_idletasks()
                root.update() 
            if readArduinoString == "Camera Checking":
                displayText.set("Camera Checking")
                root.update_idletasks()
                root.update() 
                print("Inside camera checking if statement")
                # call 4 times captureImage function
                for i in range(0,4):
                    # put delay to wait for rotation, may not need cause already wait 2 second in captureImage function
                    # time.sleep(1)
                    result = captureImage()
                    if (result == "clean and dry"):
                        port.write("P".encode()) #Send syringe check is passed for this syringe
                    else:
                        port.write("F".encode()) #Send syringe check is fail for this syringe

                    if (i == 3):
                        print("all checked")
                        port.write("C".encode()) #Once all checked, send back C message.


            if readArduinoString == "Finish":
                #Received from arduino drying and check process is successful, indicating process has finished.
                displayText.set("Finished... Wait 2 seconds")
                root.after(2000)
                startButton['state'] = 'enable'
                displayText.set("Syringe Cleaner 101")
                break

    

# def countdown():
#     global t
#     mins, secs = divmod(t, 60)
#     timer = '{:02d}:{:02d}'.format(mins, secs)
#     timerText.set(timer)
#     if t > 0:
#         t = t - 1
#         root.after(1000, start)


def captureImage():
    print("Capturing Image")
    # Load the label map
    with open(PATH_TO_LABELS, "r") as f:
        labels = [line.strip() for line in f.readlines()]

    # Load the Tensorflow Lite model with TPU attributes from Coral
    interpreter = Interpreter(
        model_path=PATH_TO_CKPT,
        experimental_delegates=[load_delegate("libedgetpu.so.1.0")],
    )
    # print(PATH_TO_CKPT) #Path to tflite print

    # Set intepreter
    interpreter.allocate_tensors()
    size = common.input_size(interpreter)

    # On Camera, take picture and retrieve image:
    stream = io.BytesIO()     # Create the in-memory stream
    with picamera.PiCamera() as camera:
        camera.start_preview()
        time.sleep(2)
        camera.capture(stream, format='jpeg')
    # "Rewind" the stream to the beginning so we can read its content
    stream.seek(0)

    image = Image.open(stream).convert('RGB').resize(
        size, Image.ANTIALIAS)  # Resize image for CV

    # Run an inference on the image
    start_time = time.time()
    common.set_input(interpreter, image)
    interpreter.invoke()
    classes = classify.get_classes(interpreter, top_k=1)
    elapsed_ms = (time.time() - start_time) * 1000

    # Print the result
    labels = dataset.read_label_file(PATH_TO_LABELS)
    for c in classes:
        print('%s: %.5f, elapsed:%s' %
              (labels.get(c.id, c.id), c.score, elapsed_ms))
        if (labels.get(c.id, c.id) == "dry and clean"):
            return "clean and dry"

        else:
            return "dirty"
        
    
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

    # #Timer Label
    # timerText = StringVar()
    # timerText.set("hello")

    # timerLabel = Label(f1, textvariable=timerText)
    # timerLabel.config(width=20, height=3)
    # timerLabel.config(font=("Courier", 16))
    # timerLabel.grid(row=0,column=0,sticky="s")

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

    startButton = Button(f1, text="Start", image = startPhoto, compound=LEFT, command=start)
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

