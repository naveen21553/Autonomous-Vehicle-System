import argparse
import base64
from datetime import datetime
import os, shutil
import numpy as np
import socketio
import eventlet
import eventlet.wsgi
from PIL import Image
from flask import Flask
from io import BytesIO
from keras.models import load_model
import utils

sio = socketio.Server()
app = Flask(__name__)
model = None
prev_image_array = None

MAX_SPEED = 25
MIN_SPEED = 10

speed_limit = MAX_SPEED

@sio.on('telemetry')
def telemetry(sid, data):
    if data:
        steering_angle = float(data['steering_angle'])
        throttle = float(data['throttle'])
        speed = float(data['speed'])

        image = Image.open(BytesIO(base64.b64decode(data['image'])))
        try:
            image = np.asarray(image)
            image = utils.preprocess(image)
            image = np.asarray([image])

            steering_angle = float(model.predict(image, batch_size=1))
            global speed_limit 
            if speed > speed_limit:
                speed_limit = MIN_SPEED
            else: speed_limit = MAX_SPEED

            throttle = 1.0 - steering_angle**2 - (speed/speed_limit)**2
            print('Steering angle: {}  Throttle: {}  Speed: {}'.format(steering_angle, throttle, speed))
            send_control(steering_angle, throttle)
        
        except Exception as e:
            print(e)

        if args.image_folder != '':
            timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
            image_filename = os.path.join(args.image_folder, timestamp)
            image.save('{}.jpg'.format(image_filename))
    else:
        sio.emit('manual', data={}, skip_sid=True)

@sio.on('connect')
def connect(sid, environ):
    print('connect', sid)
    send_control(0, 0)

def send_control(steering_angle, throttle):
    sio.emit(
        "steer",
        data={
            'steering_angle': steering_angle.__str__(),
            'throttle': throttle.__str__()
        },
        skip_sid=True
    )

def printline():
    print('-'*30)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Self Driving')
    parser.add_argument('model', type=str, help='Path to model h5 file')
    parser.add_argument('image_folder', type=str, nargs='?', default='', help='Path to image folder')
    args = parser.parse_args()

    model = load_model(args.model)
    printline()

    if args.image_folder != "":
        print('Creating image folder at {}'.format(args.image_folder))
        if os.path.exists(args.image_folder):
            shutil.rmtree(args.image_folder)
        os.makedirs(args.image_folder)
        print('RECORDING THIS RUN ...')
    
    else: print('NOT RECORDING THIS RUN')

    app = socketio.Middleware(sio, app)

    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)
            

