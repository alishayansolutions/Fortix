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