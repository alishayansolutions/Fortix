import cv2
from ultralytics import YOLO
import supervision as sv
import numpy as np
import time
import os
from helper import get_streaming_link


# Define the class name for hardhat (adjust index based on your YOLO model's class mapping)
HARDHAT_CLASS_NAME = "hardhat"
NO_HARDHAT_CLASS_NAME = "NO-Hardhat"
SKIP_SECONDS= 3

# Initialize the YOLO model and background subtractor once
model = YOLO("hard-hat.pt")
box_annotator = sv.BoxAnnotator(
    thickness=2,
    text_thickness=2,
    text_scale=1
)

fgbg_instances = {}

def get_fgbg_instance(request_key):
    if request_key not in fgbg_instances:
        fgbg_instances[request_key] = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50, detectShadows=True)
    return fgbg_instances[request_key]


def process_frame(frame, first_frame, stream_id):
    if first_frame:
        return process_first_frame(frame)
    else:
        return process_subsequent_frame(frame , stream_id)

def process_first_frame(frame):
    result = model(frame, agnostic_nms=True)[0]
    detections = sv.Detections.from_yolov8(result)
    frame = annotate_frame(frame, detections)
    return frame, detections

def process_subsequent_frame(frame, stream_id):
    fgbg = get_fgbg_instance(stream_id) 
    fg_mask = fgbg.apply(frame)
    _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    significant_change = False
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 500:  # Threshold for significant change detection
            significant_change = True
            break

    print("significant_change", significant_change)
    if significant_change:
        result = model(frame, agnostic_nms=True)[0]
        detections = sv.Detections.from_yolov8(result)
        frame = annotate_frame(frame, detections)

        # Check for NO-Hardhat class in detections
        no_hardhat_found = any(
            model.model.names[class_id] == "NO-Hardhat"
            for _, _, class_id, _ in detections
        )

        if no_hardhat_found:
            # Save the frame to the "violation" folder
            stream_dir = os.path.join("./violation", stream_id)
            os.makedirs(stream_dir, exist_ok=True)
            violation_path = os.path.join(stream_dir, f"violation_frame_{int(time.time())}.jpg")
            cv2.imwrite(violation_path, frame)
            print(f"Violation detected. Frame saved to {violation_path}")
    else:
        detections = []  # No significant change detected
    return frame, detections

labels = []
def annotate_frame(frame, detections):
    for _, confidence, class_id, _ in detections:
        class_name = model.model.names[class_id]
        labels.append(f"{class_name} {confidence:0.2f}")
        
    frame = box_annotator.annotate(scene=frame, detections=detections, labels=labels)
    return frame

def display_frame(frame, hardhat_found):
    status_text = "Hardhat Found" if hardhat_found else "Hardhat Not Found"
    color = (0, 255, 0) if hardhat_found else (0, 0, 255)
    cv2.putText(frame, status_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.imshow("Detection", frame)

def reconnect(cap, url):
    print("Reconnecting to the stream...")
    cap.release()
    cap = cv2.VideoCapture(url)
    if cap.isOpened():
        print("Reconnected successfully.")
    else:
        print("Failed to reconnect.")
    return cap



def process_stream_via_model(config , process, streaming_type="RSTP"):
    from app import stream_registry
    print("stream_registry", stream_registry)
    print("process_stream_via_model", config)

    STREAMING_LINK = get_streaming_link(config, streaming_type)

    cap = cv2.VideoCapture(STREAMING_LINK)
    if not cap.isOpened():
        print("Error: Unable to connect to the DVR stream")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"FPS: {fps}")

    # Flag to track the first frame
    first_frame = True

    # Variable to skip frames
    skip_frame_count = int(fps * SKIP_SECONDS)
    frame_counter = 0
    
    while process.get(config.stream_id, False):
        ret, frame = cap.read()
        print("Frame", ret, streaming_type)
        if not ret and streaming_type == "RTSP":
            print("Failed to capture frame")
            cap = reconnect(cap, STREAMING_LINK)
            continue  
        elif not ret and streaming_type == "CLOUD": 
            break  

        frame_counter += 1
        # print("cond", frame_counter % skip_frame_count == 0)
        # Check if we should process the frame
        if frame_counter % skip_frame_count == 0:
            frame, detections = process_frame(frame, first_frame ,config.stream_id)

            # After processing the first frame, set flag to False
            if first_frame:
                first_frame = False

            print("class_id",[model.model.names[class_id] for _, _, class_id, _ in detections])    
            print("stream_id",config.stream_id)    
            
            # Check for hardhat detection
            hardhat_found = any(
                model.model.names[class_id] == HARDHAT_CLASS_NAME
                for _, _, class_id, _ in detections
            )

            # Display the frame with annotations
            # display_frame(frame, hardhat_found)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

