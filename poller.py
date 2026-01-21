import time
from typing import Set, List
from connector import SmartServiceConnector
from config import POLL_INTERVAL
from models import CardEvent

class EventPoller:
    def __init__(self, connector: SmartServiceConnector):
        self.connector = connector
        self.seen_events: Set[str] = set()
        self.running = False

    def start(self):
        self.running = True
        print(f"Starting poller with interval: {POLL_INTERVAL}s")
        
        try:
            card_types = self.connector.get_doors()
            if card_types:
                print(card_types)
            else:
                print("failed fetch card types")
        except Exception as e:
            print(f"initial card types fetch error: {e}")
        
        while self.running:
            try:
                card_data = self.connector.get_last_door_access("49919", 0)
                
                if card_data:
                    print(card_data)
                else:
                    print("failed fetch")
                
            except Exception as e:
                print(f"poller loop error: {e}")
            
            time.sleep(POLL_INTERVAL)

    def stop(self):
        self.running = False
