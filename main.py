from kantech_service.connector import SmartServiceConnector
from kantech_service.poller import EventPoller
import sys

def main():
    print("Initializing Kantech SmartService Connector...")
    
    connector = SmartServiceConnector()
    
    if not connector.login():
        print("Initial login failed. Poller will attempt to retry.")
    
    poller = EventPoller(connector)
    
    try:
        poller.start()
    except KeyboardInterrupt:
        print("\nStopping service...")
        poller.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()
