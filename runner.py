import subprocess
import threading
import time
import sys

def run_app():
    subprocess.run([sys.executable, "app.py"])

def run_epg():
    subprocess.run([sys.executable, "epg.py"])

if __name__ == "__main__":
    # Inicia em threads separadas
    t1 = threading.Thread(target=run_app)
    t2 = threading.Thread(target=run_epg)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()