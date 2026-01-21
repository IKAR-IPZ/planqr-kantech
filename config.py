import os

BASE_URL = os.getenv("KANTECH_URL", "http://kd.zut.edu.pl:8801/SmartService")
USERNAME = os.getenv("KANTECH_USER", "WISync")
PASSWORD = os.getenv("KANTECH_PASS", "o22FpTPh33eLEKYMQqHU")
POLL_INTERVAL = int(os.getenv("KANTECH_POLL_INTERVAL", "1"))
