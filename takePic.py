from picamera import PiCamera
from time import sleep
from datetime import datetime

camera = PiCamera()
camera.start_preview()
sleep(2)
camera.capture('/home/pi/oiptflite/images/'+str(datetime.now())+'.jpg')
camera.stop_preview()