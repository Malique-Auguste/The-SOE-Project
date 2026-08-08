from dotenv import find_dotenv, load_dotenv
import os, atexit

load_dotenv(find_dotenv())
PRINTING_PRIORITY = int(os.environ.get("PRINTING_PRIORITY", "1"))
log_text = ""


def debug_print(text, priority):
    global log_text
    log_text = log_text + "\n" + text
    if priority <= PRINTING_PRIORITY:
        print(text)

def exit_handler():
    with open("log.txt", "w", encoding="utf-8") as f:
        f.write(log_text[1:])

atexit.register(exit_handler)