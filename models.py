from pydantic import BaseModel

class RTSPConfig(BaseModel):
    stream_id: str ="ss" 
    username: str
    password: str
    ip_address: str
    rtsp_port: int = 554  # Default RTSP port
    stream_path: str = "cam/realmonitor?channel=2&subtype=0" 

class RTMPPConfig(BaseModel):
    stream_id: str ="ss" 
    server_address: str
    stream_key: str
    app_name: str = "live"   

class CloudConfig(BaseModel):
    stream_id: str ="ss" 
    link: str 

class FTPConfig(BaseModel):
    ftp_host: str  
    ftp_port: int = 21
    username: str    
    password: str   
    ftp_directory: str 

class ModelLoadResponse(BaseModel):
    success: bool
    message: str      