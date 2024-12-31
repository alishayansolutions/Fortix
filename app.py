import cv2
import numpy as np
import subprocess
import os
import threading
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from models import RTSPConfig, RTMPPConfig, CloudConfig, FTPConfig, ModelLoadResponse
from stream_connection import check_connection, check_ftp_connection
from ultralytics import YOLO
import supervision as sv
import time
from functools import partial
from stream_process import process_stream_via_model 
from helper import setup_directories, get_streaming_link
from ultralytics import YOLO

app = FastAPI()

STREAMS_DIR = "./streams"
VIOLATION_DIR = "./violation"
folders_to_create = [STREAMS_DIR, VIOLATION_DIR]
setup_directories(folders_to_create)

# Registry to track active streams and their processes
stream_registry = {}

async def start_stream_helper(config, stream_type):
    if stream_type.upper() == "FTP":
       await check_ftp_connection(config)
    else:
       await check_connection(config, stream_type)

    streaming_url = get_streaming_link(config, stream_type)

    # Output HLS directory for this stream
    stream_dir = os.path.join(STREAMS_DIR, config.stream_id)
    os.makedirs(stream_dir, exist_ok=True)
    hls_path = os.path.join(stream_dir, "stream.m3u8")

    # Check if the stream is already running
    if config.stream_id in stream_registry:
        return {"status": "Stream already running", "url": f"/streams/{config.stream_id}/stream.m3u8"}

    # Start ffmpeg process in the background for HLS
    ffmpeg_command = [
        "ffmpeg",
        "-i", streaming_url,
        "-c:v", "libx264",
        "-f", "hls",
        "-hls_time", "2",
        "-hls_list_size", "5",
        "-hls_flags", "delete_segments",
        hls_path
    ]

    try:
        # Start the ffmpeg process
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Register the process in the stream registry
        stream_registry[config.stream_id] = process.pid
        threading.Thread(target=process_stream_via_model, args=(config, stream_registry, stream_type), daemon=True).start()
        return {"status": "Stream started", "url": f"/streams/{config.stream_id}/stream.m3u8"}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed to start stream: {e}")


# RTSP MODULE
@app.post("/check/rtsp_connection")
async def check_rtsp_connection(config: RTSPConfig):
    return await check_connection(config, "RTSP") 

@app.post("/rtsp/start_stream")
async def start_rtsp_stream(config: RTSPConfig):
    return await start_stream_helper(config, "RTSP")

# RTMP MODULE
@app.post("/check/rtmp_connection")
async def check_rtsp_connection(config: RTMPPConfig):
    return await check_connection(config, "RTMP")

@app.post("/rtmp/start_stream")
async def start_rtmp_stream(config: CloudConfig):
    return await start_stream_helper(config, "RTMP")    

# CLOUD MODULE
@app.post("/check/cloud_connection")
async def check_rtsp_connection(config: CloudConfig):
    return await check_connection(config, "CLOUD")     

@app.post("/cloud/start_stream")
async def start_cloud_stream(config: CloudConfig):
    return await start_stream_helper(config, "CLOUD")

# CLOUD MODULE
@app.post("/check/ftp_connection")
async def check_ftp_connection(config: FTPConfig):
    return await check_ftp_connection(config)     

@app.post("/ftp/start_stream")
async def start_ftp_stream(config: FTPConfig):
    return await start_stream_helper(config, "FTP")    

@app.get("/stop_stream/{stream_id}")
async def stop_rtsp_stream(stream_id: str):
    if stream_id not in stream_registry:
        raise HTTPException(status_code=404, detail="Stream not found")

    # Get the process ID and terminate it
    pid = stream_registry.pop(stream_id, None)
    try:
        os.kill(pid, 9)  # Forcefully terminate the ffmpeg process
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop stream: {e}")

    # Remove the HLS files
    stream_dir = os.path.join(STREAMS_DIR, stream_id)
    if os.path.exists(stream_dir):
        for root, dirs, files in os.walk(stream_dir):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(stream_dir)
    else:
        print(f"Directory {stream_dir} does not exist.")

    # Remove the Violation files
    violation_dir = os.path.join(VIOLATION_DIR, stream_id)
    if os.path.exists(violation_dir):
        for root, dirs, files in os.walk(violation_dir):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(violation_dir)
    else:
        print(f"Directory {violation_dir} does not exist.")

    return {"status": "Stream stopped"}


@app.get("/list-streams")
async def list_streams():
    return {"active_streams": list(stream_registry.keys())}

@app.get("/test_model", response_model=ModelLoadResponse)
def test_model():
    try:
        model = YOLO("hard-hat.pt")  # Replace with the actual path to your model file
        frame = cv2.imread("sample.jpg")
        print("frame", frame)
        result = model(frame)
        print(result)

        return ModelLoadResponse(success=True, message="Model loaded successfully.")
    except Exception as e:
        error_message = f"Failed to load YOLO model: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)

# Serve HLS files
app.mount("/streams", StaticFiles(directory=STREAMS_DIR), name="streams")
