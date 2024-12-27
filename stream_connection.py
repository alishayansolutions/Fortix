import cv2
from helper import get_streaming_link
from fastapi import HTTPException

async def check_connection(config, stream_type):
    print("check_connection",config)
    # Construct RTSP URL
    
    streaming_url = get_streaming_link(config, stream_type)
    
    # Try to connect to the stream
    cap = cv2.VideoCapture(streaming_url)
    
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="Unable to connect to the stream")
    
    # You can optionally read a frame to check the connection further
    ret, frame = cap.read()
    if not ret:
        raise HTTPException(status_code=400, detail="Failed to fetch stream frame")
    
    # Release the capture object after use
    cap.release()
    
    return {"status": "Connection successful", "message": f"{stream_type} Stream connection established"} 
