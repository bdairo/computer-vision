from flask import Flask, render_template, Response
import cv2
import depthai as dai
import numpy as np
from queue import Queue
from utils import create_pipeline, detect_markers, get_object_distance, get_object_dimensions, annotate_rgb_feed

app = Flask(__name__)
frame_queue = Queue(maxsize=10) 

def generate_frames():
    pipeline = create_pipeline()
    with dai.Device(pipeline) as device:
        qLeft = device.getOutputQueue(name="left", maxSize=4, blocking=False)
        qRight = device.getOutputQueue(name="right", maxSize=4, blocking=False)
        qRgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)

        while True:
            inLeft = qLeft.get()
            inRight = qRight.get()
            inRgb = qRgb.get()

            if inLeft is not None and inRight is not None:
                frameLeft = inLeft.getCvFrame()
                frameRight = inRight.getCvFrame()
                frameRgb = inRgb.getCvFrame()

                # Here we detect markers in the left, right, and rgb camera
                cornersLeft, _ = detect_markers(frameLeft)
                cornersRight, _ = detect_markers(frameRight)
                cornersRgb, _ = detect_markers(frameRgb)
                 
                # Here we get the object distance by using stereo vision theory between two corresponding arUco markers from the left and right camera
                distances= get_object_distance(cornersLeft, cornersRight)
                dimensions = get_object_dimensions(cornersRgb, distances)
                
                # Here we use the corners from the rgb camera to map and annotate the aruco markers with the appropriate distance
                annotate_rgb_feed(frameRgb, cornersLeft, distances, dimensions)

                # Display results on the frame
                _ , buffer = cv2.imencode('.jpg', frameRgb)
                frame_data = buffer.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')  
                  
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
