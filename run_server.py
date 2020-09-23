import os
import time
import subprocess
import webbrowser


def open_browser():
    time.sleep(3)
    webbrowser.open('http://127.0.0.1:8000/', new=2)


virtual_env = os.path.join(os.getcwd()[:-10], '.venv', 'Scripts', 'python.exe')
process = subprocess.Popen([virtual_env, 'manage.py', 'runserver'], shell=True)
open_browser()
process.communicate()
