
import os

def get_streaming_link(config, type):
    if type.upper() == "RTSP":
        return f"rtsp://{config.username}:{config.password}@{config.ip_address}:{config.rtsp_port}/{config.stream_path}"
    elif type.upper() == "RTMP":
        return f"rtmp://{config.server_address}/{config.app_name}/{config.stream_key}"
    elif type.upper() == "CLOUD":
        return config.link
    elif type.upper() == "FTP":
        return f"ftp://{config.ftp_host}:{config.ftp_port}/{config.ftp_directory}"    
    else:
        raise ValueError("Invalid link type. Must be 'RTSP', 'RTMP', 'CLOUD', or 'FTP'.")

def create_directory(path):
    try:
        os.makedirs(path, exist_ok=True)
        print(f"Directory created or already exists: {path}")
    except Exception as e:
        print(f"Error creating directory {path}: {e}")

def setup_directories(folders):
    for folder in folders:
        create_directory(folder)
    print("Directories are set up successfully.")
