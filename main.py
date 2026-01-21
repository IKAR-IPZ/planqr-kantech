try:
    from connector import SmartServiceConnector
    from poller import EventPoller
except Exception:
    from connector import SmartServiceConnector
    from poller import EventPoller

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
        connector.logout()
        sys.exit(0)
    finally:
        connector.logout()

if __name__ == "__main__":
    main()
