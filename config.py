import os

BASE_URL = os.getenv("KANTECH_URL", "http://kd.zut.edu.pl:8801/SmartService")
USERNAME = os.getenv("KANTECH_USER", "WISync")
PASSWORD = os.getenv("KANTECH_PASS", "o22FpTPh33eLEKYMQqHU")
POLL_INTERVAL = int(os.getenv("KANTECH_POLL_INTERVAL", "1"))

# PostgreSQL Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "192.168.203.174")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "planqr-db-prod")
POSTGRES_USER = os.getenv("POSTGRES_USER", "zut")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_CONNECT_TIMEOUT = int(os.getenv("POSTGRES_CONNECT_TIMEOUT", "5"))

# WebService Configuration
WEBSERVICE_HOST = os.getenv("WEBSERVICE_HOST", "0.0.0.0")
WEBSERVICE_PORT = int(os.getenv("WEBSERVICE_PORT", "5000"))
WEBSERVICE_DEBUG = os.getenv("WEBSERVICE_DEBUG", "False").lower() == "true"
