import depthai as dai
import numpy as np
import cv2
import glob


baseline = 75  # 7.5 cm
focal_length = 442.5930392 # focal length in pixels

def create_pipeline():
    """Creates and configures the pipeline for stereo vision and depth estimation."""
    pipeline = dai.Pipeline()

    # Define sources for left and right cameras and rgb camera
    camLeft = pipeline.create(dai.node.MonoCamera)
    camRight = pipeline.create(dai.node.MonoCamera)
    camRgb = pipeline.create(dai.node.ColorCamera)

    camLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
    camRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)
    camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)

    camLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    camRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_720_P)

    # Create outputs for the cameras
    xoutLeft = pipeline.create(dai.node.XLinkOut)
    xoutRight = pipeline.create(dai.node.XLinkOut)
    xoutRgb = pipeline.create(dai.node.XLinkOut)

    xoutLeft.setStreamName("left")
    xoutRight.setStreamName("right")
    xoutRgb.setStreamName("rgb")

    camLeft.out.link(xoutLeft.input)
    camRight.out.link(xoutRight.input)
    camRgb.preview.link(xoutRgb.input)

    # Create stereo depth node
    stereo = pipeline.create(dai.node.StereoDepth)
    stereo.setConfidenceThreshold(200)
    stereo.setLeftRightCheck(True)
    stereo.setSubpixel(False)
    camLeft.out.link(stereo.left)
    camRight.out.link(stereo.right)

    # Output depth
    xoutDepth = pipeline.create(dai.node.XLinkOut)
    xoutDepth.setStreamName("depth")
    stereo.depth.link(xoutDepth.input)

    print('Pipeline created!!')
    return pipeline


def detect_markers(frame):
    # print('In detect markers function')
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
    corners, ids, _ = detector.detectMarkers(frame)  
    # print('returning detected markers') 
    return corners, ids

def get_object_distance(cornersLeft, cornersRight):
    # print('In get object distances fxn')
    distances = []
    if cornersLeft and cornersRight:
        # Calculate distance for each matched pair of markers
        for cornerL, cornerR in zip(cornersLeft, cornersRight):
            xL = np.mean(cornerL[0][:, 0])  # Average x-coordinates of corners in the left image
            xR = np.mean(cornerR[0][:, 0])  # Average x-coordinates of corners in the right image
            disparity = xL - xR
            if disparity != 0:
                distance = (443 * 7.5) / disparity  # focal length * baseline / disparity
                distances.append(distance)
            else:
                distances.append(float('inf'))  # Avoid division by zero
    # print('returning distances')
    return distances

def get_object_dimensions(cornersRgb, distances):
    # print('In get object dimensions fxn()')
    dimensions = []
    marker_physical_size = 15  # The physical size of the marker in centimeters; adjust as needed.
    
    for corner, distance in zip(cornersRgb, distances):
        if distance == float('inf'):
            dimensions.append(None)  # No dimension if distance is infinity (marker not found in one of the images)
            continue

        # Calculate the pixel length of the marker's side using the top left and top right corners
        pixel_length = np.linalg.norm(corner[0][0] - corner[0][1])
        
        # Convert pixel length to real-world length using similarity of triangles
        real_world_length = (pixel_length * distance) / 443  # 443 is the focal length in pixels

        scale = real_world_length / marker_physical_size  # Find the scaling factor
        dimensions.append(scale * marker_physical_size)  # Assume square marker for simplicity
        # dimensions.append(real_world_length)

    # print('returning dimensions')
    return dimensions


def annotate_rgb_feed(frameRgb, cornersRgb, distances, dimensions):
    # print('in annotate rgb feed() function')
    if cornersRgb:
        for (corner, distance, dimension) in zip(cornersRgb, distances, dimensions):
            centroid_x = int(np.mean(corner[0][:, 0]))
            centroid_y = int(np.mean(corner[0][:, 1]))
            
            # Display distance
            distance_text = f"Dist: {distance:.2f} cm"
            cv2.putText(frameRgb, distance_text, (centroid_x, centroid_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Display dimensions
            if dimension:
                dimension_text = f"Size: {dimension:.2f} cm"
                cv2.putText(frameRgb, dimension_text, (centroid_x, centroid_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    # print('Done with annotations')