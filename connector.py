import requests
import xml.etree.ElementTree as ET
import time
import re
from typing import List, Optional
from config import BASE_URL, USERNAME, PASSWORD
from models import CardEvent
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

    def logout(self) -> bool:
        if not self.session_key:
            return True
        
        try:
            url = f"{BASE_URL}/Logout?sdKey={self.session_key}"
            print(f"Logging out...")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print("Logout successful.")
                self.session_key = None
                return True
            else:
                print(f"Logout failed. Status: {response.status_code}")
        except Exception as e:
            print(f"Logout exception: {e}")
        
        return False

    def get_card(self, card_id: str) -> Optional[str]:
        if not self.session_key:
            if not self.login():
                return None
        
        try:
            url = f"{BASE_URL}/Cards/{card_id}?sdKey={self.session_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"Get card failed. Status: {response.status_code}")
        except Exception as e:
            print(f"Get card exception: {e}")
        
        return None
    
    def get_card_types(self) -> Optional[str]:
        if not self.session_key:
            if not self.login():
                return None
        
        try:
            url = f"{BASE_URL}/CardTypes/?sdKey={self.session_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"Get card types failed. Status: {response.status_code}, Body: {response.text}")
        except Exception as e:
            print(f"Get card types exception: {e}")
        
        return None

    def list_cards(
        self,
        filter_value: str = "",
        contains: int = 0,
        number_of_cards: int = 50,
        list_index: str = "USERNAME",
        list_start_value: str = "0",
        extended_fields: Optional[str] = None,
        list_field_filter: Optional[str] = None,
    ) -> Optional[str]:
        if not self.session_key:
            if not self.login():
                return None

        try:
            if not filter_value:
                contains = 0
                filter_encoded = ""
            else:
                filter_encoded = filter_value.replace(" ", "+").replace(":", "[COLON]")

            base = f"{BASE_URL}/Cards?sdKey={self.session_key}"
            query_parts = [
                f"filter={filter_encoded}",
                f"contains={contains}",
                f"numberOfCards={number_of_cards}",
                f"listIndex={list_index}",
                f"listStartValue={list_start_value}",
            ]

            if extended_fields:
                query_parts.append(f"extendedFields={extended_fields}")
            if list_field_filter:
                query_parts.append(f"listFieldFilter={list_field_filter}")

            url = base + "&" + "&".join(query_parts)
            response = requests.get(url, timeout=15)

            if response.status_code == 200:
                return response.text
            else:
                print(
                    f"List cards failed. Status: {response.status_code}, Body: {response.text}"
                )
        except Exception as e:
            print(f"List cards exception: {e}")

        return None

    def get_last_door_access(
        self,
        id: str,
        access_type: str = "",
    ) -> Optional[str]:
        if not self.session_key:
            if not self.login():
                return None

        try:
            url = f"{BASE_URL}/LastDoorAccess?sdKey={self.session_key}&id={id}"
            if access_type:
                url += f"&accessType={access_type}"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                return response.text
            else:
                print(
                    f"Get last door access failed. Status: {response.status_code}, Body: {response.text}"
                )
        except Exception as e:
            print(f"Get last door access exception: {e}")

        return None

    def get_doors(self) -> Optional[str]:
        if not self.session_key:
            if not self.login():
                return None

        try:
            url = f"{BASE_URL}/Doors?sdKey={self.session_key}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                return response.text
            else:
                print(f"Get doors failed. Status: {response.status_code}, Body: {response.text}")
        except Exception as e:
            print(f"Get doors exception: {e}")

        return None

