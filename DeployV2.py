# Import packages
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

# Define and parse input arguments
parser = argparse.ArgumentParser()
# parser.add_argument(
#     "--labels",
#     help="Name of the labelmap file, if different than labelmap.txt",
#     default="labelmap.txt",
# )
parser.add_argument(
    "--threshold",
    help="Minimum confidence threshold for displaying detected objects",
    default=0.5,
)
parser.add_argument(
    "--edgetpu",
    help="Use Coral Edge TPU Accelerator to speed up detection",
    action="store_true",
)

args = parser.parse_args()

LABELMAP_NAME = "labelmap.txt"
min_conf_threshold = float(args.threshold)
use_TPU = args.edgetpu

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


# Not doing local file saving
# # Define path to images and grab all image filenames
# if IM_DIR:
#     PATH_TO_IMAGES = os.path.join(CWD_PATH,IM_DIR)
#     images = glob.glob(PATH_TO_IMAGES + '/*')

# elif IM_NAME:
#     PATH_TO_IMAGES = os.path.join(CWD_PATH,IM_NAME)
#     images = glob.glob(PATH_TO_IMAGES)

def set_input_tensor(interpreter, image):
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = image

def classify_image(interpreter, image, top_k=1):
  """Returns a sorted array of classification results."""
  set_input_tensor(interpreter, image)
  interpreter.invoke()
  output_details = interpreter.get_output_details()[0]
  output = np.squeeze(interpreter.get_tensor(output_details['index']))

  # If the model is quantized (uint8 data), then dequantize the results
  if output_details['dtype'] == np.uint8:
    scale, zero_point = output_details['quantization']
    output = scale * (output - zero_point)

  ordered = np.argpartition(-output, top_k)
  return [(i, output[i]) for i in ordered[:top_k]]
  
def continuousCV():
    # Load the label map
    with open(PATH_TO_LABELS, 'r') as f:
        labels = [line.strip() for line in f.readlines()]


    # Load the Tensorflow Lite model with TPU attributes from Coral
    interpreter = Interpreter(
        model_path=PATH_TO_CKPT,
        experimental_delegates=[load_delegate("libedgetpu.so.1.0")],
    )
    

    interpreter.allocate_tensors()
    _, height, width, _ = interpreter.get_input_details()[0]['shape']


    print("After config done, using camera")
    with picamera.PiCamera(resolution=(640, 480), framerate=30) as camera:
        camera.start_preview()
        try:
          stream = io.BytesIO()
          for _ in camera.capture_continuous(
              stream, format='jpeg', use_video_port=True):
            stream.seek(0)
            image = Image.open(stream).convert('RGB').resize((width, height),
                                                             Image.ANTIALIAS)
            start_time = time.time()
            results = classify_image(interpreter, image)
            elapsed_ms = (time.time() - start_time) * 1000
            label_id, prob = results[0]
            stream.seek(0)
            stream.truncate()
            camera.annotate_text = '%s %.2f\n%.1fms' % (labels[label_id], prob,
                                                        elapsed_ms)
        finally:
          camera.stop_preview()

def captureImage():
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



captureImage()
# continuousCV()

