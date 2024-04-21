from flask import Flask, request, jsonify, render_template, send_file
import numpy as np
import cv2
import glob
import io
from utils import calibrate_camera, process_point, calculate_object_dimensions, compute_integral_image, stitch_images

app = Flask(__name__, '/static')

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calculate-dimensions', methods=['POST'])
def calculate_dimensions():
    if 'image' not in request.files:
        return "No image uploaded", 400

    print('request is:', request.form)
    distance_to_object = request.form.get('distance', type=float)
    point1 = request.form.get('point1')
    point1 = process_point(point1)
    point2 = request.form.get('point2')
    point2 = process_point(point2)

    matrix = calibrate_camera()
    calculated_diameter = calculate_object_dimensions(matrix, distance_to_object, point1, point2)

    return jsonify({"calculated_diameter": calculated_diameter})

@app.route('/compute-integral', methods=['POST'])
def compute_integral():
    print('request is:', request)
    file = request.files['image']
    if file:
        image = cv2.imdecode(np.fromstring(file.read(), np.uint8), cv2.IMREAD_UNCHANGED)
        integral_img = compute_integral_image(image)
        integral_img_normalized = cv2.normalize(integral_img, None, 0, 255, cv2.NORM_MINMAX)

        # Convert the integral image to a format that can be sent to the browser
        _, buffer = cv2.imencode('.png', integral_img_normalized)
        buffer = io.BytesIO(buffer)

        return send_file(buffer, mimetype='image/png')

    return 'No file uploaded', 400

@app.route('/stitch', methods=['POST'])
def stitch():
    files = request.files.getlist('images[]')
    images = [cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR) for file in files]

    if len(images) >= 2:
        stitched_image = stitch_images(images)
        if stitched_image is not None:
            # Convert the stitched image to a format that can be sent to the client
            _, buffer = cv2.imencode('.jpg', stitched_image)
            io_buf = io.BytesIO(buffer)
            return send_file(io_buf, mimetype='image/jpeg')
        else:
            return "Image stitching failed.", 500
    else:
        return "Need at least two images to stitch.", 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
