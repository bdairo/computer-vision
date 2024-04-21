import numpy as np
import cv2
import glob

def calibrate_camera(pattern_size=(8, 6), square_size=25):
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    # Prepare object points
    objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)

    objp = objp * square_size

    # Arrays to store object points and image points from all the images.
    obj_points = []  # 3D points in real world space
    img_points = []  # 2D points in image plane.

    # Read images
    images = glob.glob('../../calibration_images/*')
    img_size = (640, 480)
    for image in images:
        image = cv2.imread(image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        img_size = gray.shape[::-1]

        # Find the chessboard corners
        ret, corners = cv2.findChessboardCorners(gray, pattern_size, None)

        # If found, add object points, image points (after refining them)
        if ret:
            obj_points.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            img_points.append(corners2)

    ret, mtx = cv2.calibrateCamera(obj_points, img_points, img_size, None, None)
    return mtx


def process_point(point):
    splits = point.split(',')
    a, b = splits[0], splits[1]
    a, b = float(a), float(b)
    result = (a,b)
    return result


def calculate_object_dimensions(camera_matrix, distance_to_object, point1, point2):
    print('point1 is:', point1)
    print('point2 is:', point2)

    # Assuming point1 and point2 are tuples of (x, y) coordinates
    pixel_diameter = abs(point1[0] - point2[0])
    print(f"Diameter in pixels: {pixel_diameter}")

    # Extract the focal length from the camera matrix
    focal_length_px = camera_matrix[0][0]

    # Calculate the real-world dimension of the object
    calculated_dimension = (pixel_diameter * distance_to_object) / focal_length_px
    print(f'Derived dimension of the object: {calculated_dimension} mm')

    return calculated_dimension

def compute_integral_image(image):
    # Convert the image to grayscale
    # gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Initialize the integral image with zeros
    integral_image = np.zeros_like(image, dtype=np.uint64)

    # Compute the integral image
    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            integral_image[row, col] = image[row, col]
            if row > 0:
                integral_image[row, col] += integral_image[row - 1, col]
            if col > 0:
                integral_image[row, col] += integral_image[row, col - 1]
            if col > 0 and row > 0:
                integral_image[row, col] -= integral_image[row - 1, col - 1]

    return integral_image


def find_keypoints_and_features(image):
    sift = cv2.SIFT_create()
    keypoints, descriptors = sift.detectAndCompute(image, None)
    return keypoints, descriptors

def match_features(descriptors1, descriptors2):
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(descriptors1, descriptors2, k=2)
    good_matches = [m for m, n in matches if m.distance < 0.7*n.distance]
    return good_matches


def stitch_images(images):
    detector = cv2.SIFT_create()
    # Initialize the stitcher
    stitcher = cv2.Stitcher_create()

    # Create a placeholder for the final stitched image
    stitched_image = None

    # Iterate over pairs of consecutive images
    for i in range(len(images) - 1):
        # Detect keypoints and compute descriptors for each image
        keypoints1, descriptors1 = detector.detectAndCompute(images[i], None)
        keypoints2, descriptors2 = detector.detectAndCompute(images[i + 1], None)

        # Match keypoints between consecutive images
        matcher = cv2.DescriptorMatcher_create(cv2.DescriptorMatcher_BRUTEFORCE)
        matches = matcher.match(descriptors1, descriptors2)

        # Filter matches based on Lowe's ratio test
        good_matches = []
        for match in matches:
            if match.distance < 0.75 * min(match.queryIdx, match.trainIdx):
                good_matches.append(match)

        # Estimate homography transformation
        src_pts = np.float32([keypoints1[match.queryIdx].pt for match in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([keypoints2[match.trainIdx].pt for match in good_matches]).reshape(-1, 1, 2)
        H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        # Warp the second image
        warped_image = cv2.warpPerspective(images[i + 1], H, (images[i + 1].shape[1], images[i + 1].shape[0]))

        # Stitch the warped image with the first image
        result = stitcher.stitch((images[i], warped_image))

        # Check if stitching was successful
        if result[0] == cv2.Stitcher_OK:
            stitched_image = result[1]
        else:
            print("Stitching failed for images", i, "and", i + 1)

    return stitched_image

# def stitch_images(images):
#     base_image = images[0]
#     # Estimate canvas size (maximum possible)
#     height, width = base_image.shape[:2]
#     canvas_width = width * len(images)
#     canvas = np.zeros((height, canvas_width, 3), dtype=np.uint8)
#     canvas[:height, :width, :] = base_image

#     current_x = width  # Starting position for the next image

#     for i in range(1, len(images)):
#         keypoints1, descriptors1 = find_keypoints_and_features(base_image)
#         keypoints2, descriptors2 = find_keypoints_and_features(images[i])

#         good_matches = match_features(descriptors1, descriptors2)

#         if len(good_matches) > 4:
#             src_pts = np.float32([keypoints1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
#             dst_pts = np.float32([keypoints2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

#             H, _ = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)

#             warped_image = cv2.warpPerspective(images[i], H, (canvas_width, height))

#             # Update the canvas
#             overlay_mask = (warped_image > 0)
#             canvas[overlay_mask] = warped_image[overlay_mask]

#             # Update base_image for the next iteration
#             base_image = canvas[:, :current_x + width, :]
#             current_x += width

#     return canvas