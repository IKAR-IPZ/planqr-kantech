import time
from typing import Set, List
from .connector import SmartServiceConnector
from .config import POLL_INTERVAL
from .models import CardEvent

class EventPoller:
    def __init__(self, connector: SmartServiceConnector):
        self.connector = connector
        self.seen_events: Set[str] = set()
        self.running = False

    def start(self):
        self.running = True
        print(f"Starting poller with interval: {POLL_INTERVAL}s")
        
        while self.running:
            try:
                events = self.connector.get_events()
                new_events = self.process_events(events)
                
                if new_events:
                    print(f"By polling, found {len(new_events)} new events:")
                    for evt in new_events:
                        print(f" >>> {evt}")
                
            except Exception as e:
                print(f"Poller loop error: {e}")
            
            time.sleep(POLL_INTERVAL)

    def process_events(self, events: List[CardEvent]) -> List[CardEvent]:
        new_items = []
        for evt in events:
            signature = f"{evt.card_number}_{evt.timestamp}_{evt.reader_name}"
            
            if signature not in self.seen_events:
                self.seen_events.add(signature)
                new_items.append(evt)
                
                if len(self.seen_events) > 10000:
                    self.seen_events.clear()
        
        return new_items

    def stop(self):
        self.running = False
