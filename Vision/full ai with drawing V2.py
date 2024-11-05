from ultralytics import YOLO
import cv2
import numpy as np
import math
import time

CONFIDENCE_THRESHOLD = 0.90

model = YOLO('Pizza&Crates_nano.pt')

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Cannot open camera")
    exit()
    
def get_rotated_rectangle_points(x_center, y_center, width, height, angle_degrees):
    """
    Calculate the four corner points of a rotated rectangle.
    
    x_center, y_center: Center of the rectangle.
    width, height: Dimensions of the rectangle.
    angle_degrees: Rotation of the rectangle in degrees.
    """
    # Convert angle to radians
    angle_radians = math.radians(angle_degrees)

    # Half width and height
    half_width = width / 2
    half_height = height / 2

    # Calculate the unrotated corner points relative to the center
    corners = np.array([
        [-half_width, -half_height],  # Bottom-left
        [ half_width, -half_height],  # Bottom-right
        [ half_width,  half_height],  # Top-right
        [-half_width,  half_height]   # Top-left
    ])

    # Rotation matrix for 2D rotation
    rotation_matrix = np.array([
        [math.cos(angle_radians), -math.sin(angle_radians)],
        [math.sin(angle_radians),  math.cos(angle_radians)]
    ])

    # Rotate each corner point
    rotated_corners = np.dot(corners, rotation_matrix)

    # Translate the rotated points back to the rectangle's center
    rotated_corners[:, 0] += x_center
    rotated_corners[:, 1] += y_center

    return rotated_corners.astype(int)

def draw_circle(circle, img, inside):
    if inside:
        colour = (0,255,0) # green
    if not inside:
        colour = (0,0,255) # red
    cv2.circle(img,(circle[0],circle[1]), circle[2], colour, 2) # draw circel with colour

def draw_rotated_rectangle(image, rectangle_params, color=(255, 0, 0), thickness=2):
    """
    Draw a rotated rectangle on the image.
    
    image: The image on which to draw.
    rectangle_params: List [x_center, y_center, width, height, rotation (in degrees)].
    color: Color of the rectangle (default is green).
    thickness: Thickness of the rectangle edges (default is 2).
    """
    # Unpack the rectangle parameters
    x_center, y_center, width, height, rotation = rectangle_params
    
    # Get the four corner points of the rotated rectangle
    points = get_rotated_rectangle_points(x_center, y_center, width, height, -rotation)
    
    # Draw the rotated rectangle using polylines
    points = points.reshape((-1, 1, 2))  # Reshape for polylines function
    cv2.polylines(image, [points], isClosed=True, color=color, thickness=thickness)

    
def rotate_point(px, py, cx, cy, angle):
    """Rotate point (px, py) around (cx, cy) by 'angle' radians."""
    # Translate point to origin
    px -= cx
    py -= cy
    
    # Apply rotation
    x_new = px * math.cos(angle) - py * math.sin(angle)
    y_new = px * math.sin(angle) + py * math.cos(angle)
    
    # Translate back
    x_new += cx
    y_new += cy
    
    return x_new, y_new

def is_circle_in_rectangle(circle, rectangle):
    """
    Check if the circle is entirely within the rotated rectangle.
    
    circle: List containing the circle's properties in the form:
            [circle_x, circle_y, radius].
    rectangle: List containing the rectangle's properties in the form:
               [rect_x, rect_y, rect_width, rect_height, rect_angle].
    """
    # Unpack circle parameters from the array
    circle_x, circle_y, radius = circle
    
    # Unpack rectangle parameters from the array
    rect_x, rect_y, rect_width, rect_height, rect_angle_deg = rectangle
    
    # Convert the rectangle's rotation from degrees to radians
    rect_angle = math.radians(rect_angle_deg)
    
    # Step 1: Rotate the circle's center point to align with the rectangle's axis
    rotated_circle_x, rotated_circle_y = rotate_point(circle_x, circle_y, rect_x, rect_y, -rect_angle)
    
    # Step 2: Get the rectangle's boundaries
    half_width = rect_width / 2
    half_height = rect_height / 2
    
    # Step 3: Check if the circle lies within the rectangle's boundaries (accounting for the radius)
    if (rotated_circle_x - radius >= rect_x - half_width and
        rotated_circle_x + radius <= rect_x + half_width and
        rotated_circle_y - radius >= rect_y - half_height and
        rotated_circle_y + radius <= rect_y + half_height):
        return True
    else:
        return False
    
def Boundingbox(results, yolo_image):
    for result in results:
        obb = result.obb.cpu().numpy()

        results_xywhrs = obb.xywhr
        results_class = obb.cls
        circles = []
        rectangles = []
        
        for results_xywhr, cls in zip(results_xywhrs, results_class):
            if cls == 1:
                X_middle = int(results_xywhr[0])
                Y_middle = int(results_xywhr[1])
    
                radius= int((results_xywhr[2] + results_xywhr[3]) / 4)

                circles.append([X_middle, Y_middle, radius])
            if cls == 0:
                X_middle = int(results_xywhr[0])
                Y_middle = int(results_xywhr[1])
    
                rotation = results_xywhr[4]
                rotation = int(rotation * 180 / math.pi)

                rectangles.append([X_middle, Y_middle,results_xywhr[2], results_xywhr[3], rotation])

        return(circles, rectangles)

def amount_in_crate():
    success, yolo_image = cap.read()
    
    #apply moddel on image
    results = model.track(yolo_image, conf=CONFIDENCE_THRESHOLD)
    
    # Get position of the boundingboxes
    circles, rectangles = Boundingbox(results, yolo_image)
    
    # check & count pizza's in crate
    pizzas_in_crate = 0
    for rectangle in rectangles:
        draw_rotated_rectangle(yolo_image, rectangle)
        for cicle in circles:
            is_inside = is_circle_in_rectangle(cicle, rectangle)
            if is_inside:
                pizzas_in_crate += 1
                
            draw_circle(cicle, yolo_image, is_inside)
    
    if (len(rectangles) == 0):
        for cicle in circles:
            draw_circle(cicle, yolo_image, False)
    cv2.imshow('frame', yolo_image)# show image
    
    return(pizzas_in_crate)


while (1):
    start_time = time.time() #start timer
    print(amount_in_crate())
    print("My program took", time.time() - start_time, "to run") # print cycle time
    # end when q is pressed
    if cv2.waitKey(1) == ord('q'):
        break

cv2.destroyAllWindows()
