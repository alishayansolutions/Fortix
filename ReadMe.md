- source env/bin/activate
- check python version python --version
- pip install -r requirements.txt
- python detect.py

How to create a python environment

- python3.9 -m venv my-env-folder-name
- source my-env-folder-name/bin/activate
- deactivate


.\env\Scripts\activate
uvicorn app:app --reload

python3.9 -m uvicorn app:app

sudo vim /etc/nginx/sites-enabled/fortix 
server {
      listen 80;
      server_name 18.169.18.218;
      location / {
           proxy_pass http://127.0.0.1:8000;
      }
}
sudo service nginx restart


nohup uvicorn app:app --host 0.0.0.0 --port 8000 &
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > myapp.log 2>&1 &
ps aux | grep uvicorn

pgrep -fl uvicorn
kill <PID>

logs 
tail -f nohup.out

