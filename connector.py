import requests
import xml.etree.ElementTree as ET
import time
import re
from typing import List, Optional
from .config import BASE_URL, USERNAME, PASSWORD, EVENTS_ENDPOINT
from .models import CardEvent
from datetime import datetime

class SmartServiceConnector:
    def __init__(self):
        self.session_key = None
        self.last_poll_time = datetime.now()

    def login(self) -> bool:
        try:
            url = f"{BASE_URL}/Login?userName={USERNAME}&password={PASSWORD}"
            print(f"Connecting to: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                match = re.search(r'SessionKey>([^<]+)<', response.text)
                if not match:
                    match = re.search(r'Key>([^<]+)<', response.text)
                
                if match:
                    self.session_key = match.group(1)
                    print(f"Login successful. SessionKey: {self.session_key}")
                    return True
                else:
                    print(f"Login failed. Could not find SessionKey in response: {response.text}")
            else:
                print(f"Login failed. Status: {response.status_code}, Body: {response.text}")
                
        except Exception as e:
            print(f"Login exception: {e}")
        
        return False

    def get_events(self) -> List[CardEvent]:
        if not self.session_key:
            if not self.login():
                return []

        events = []
        try:
            url = f"{BASE_URL}/{EVENTS_ENDPOINT}?sdKey={self.session_key}"
            response = requests.get(url, timeout=10)

            if response.status_code == 401 or response.status_code == 403:
                print("Session expired. Re-logging...")
                self.session_key = None
                return []

            if response.status_code == 200:
                root = ET.fromstring(response.text)
                
                for item in root.findall(".//Row"): 
                    card_elem = item.find("CardNumber") or item.find("Card")
                    reader_elem = item.find("ReaderName") or item.find("Reader")
                    time_elem = item.find("DateTime") or item.find("Time")

                    if card_elem is not None and card_elem.text:
                        card_num = card_elem.text
                        reader = reader_elem.text if reader_elem is not None else "Unknown"
                        
                        time_str = time_elem.text if time_elem is not None else str(datetime.now())
                        try:
                            dt = datetime.now()
                        except:
                            dt = datetime.now()

                        event = CardEvent(
                            card_number=card_num,
                            reader_name=reader,
                            timestamp=dt,
                            raw_data=ET.tostring(item, encoding='unicode')
                        )
                        events.append(event)
                
        except Exception as e:
            print(f"Error fetching events: {e}")
        
        return events
