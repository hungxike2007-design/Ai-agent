
import datetime
import os

def log_debug(message):
    log_file = os.path.join(os.getcwd(), "debug_log.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now()}] {message}\n")
