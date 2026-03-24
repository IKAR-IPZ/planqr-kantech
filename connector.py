import requests
import xml.etree.ElementTree as ET
import time
import re
from typing import List, Optional, Dict
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
                return self.format_access_logs_summary(response.text)
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

    def parse_smartlink_xml(self, xml_string: str) -> List[Dict]:
        """Parse SmartLink access log XML data into structured format."""
        records = []
        
        try:
            root = ET.fromstring(xml_string)
            
            for item in root.findall('.//item'):
                key_elem = item.find('key/string')
                value_elem = item.find('value/SmartLinkDataValue/Value')
                
                if key_elem is not None and value_elem is not None:
                    access_key = key_elem.text
                    access_value = value_elem.text
                    
                    # Format: "2026-01-28  09:29:07 Access granted 004F:EAC4 gsliwinski"
                    parts = access_value.split()
                    
                    record = {
                        'Access_ID': access_key,
                        'Date': parts[0] if len(parts) > 0 else '',
                        'Time': parts[1] if len(parts) > 1 else '',
                        'Status': ' '.join(parts[2:4]) if len(parts) > 3 else '',
                        'Card_ID': parts[4] if len(parts) > 4 else '',
                        'User': parts[5] if len(parts) > 5 else '',
                        'Full_Entry': access_value
                    }
                    records.append(record)
        
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            return []
        
        return records

    def format_access_logs_table(self, xml_data: str) -> str:
        """Format access logs as a nice table."""
        records = self.parse_smartlink_xml(xml_data)
        
        if not records:
            return "No records found"
        
        header = f"{'ID':<8} {'Date':<10} {'Time':<8} {'Card':<12} {'User':<12} {'Status':<15}"
        separator = "-" * len(header)
        
        lines = [separator, header, separator]
        for record in records:
            line = f"{record['Access_ID']:<8} {record['Date']:<10} {record['Time']:<8} {record['Card_ID']:<12} {record['User']:<12} {record['Status']:<15}"
            lines.append(line)
        lines.append(separator)
        
        return "\n".join(lines)

    def format_access_logs_summary(self, xml_data: str) -> str:
        records = self.parse_smartlink_xml(xml_data)
        
        if not records:
            return "No records found"
        
        users_data = {}
        for record in records:
            user = record['User']
            if user not in users_data:
                users_data[user] = {
                    'count': 0,
                    'cards': set(),
                    'latest_date': '',
                    'latest_time': '',
                    'status': record['Status']
                }
            users_data[user]['count'] += 1
            users_data[user]['cards'].add(record['Card_ID'])
            users_data[user]['latest_date'] = record['Date']
            users_data[user]['latest_time'] = record['Time']
        
        header = f"{'User':<12} {'Count':<7} {'Cards':<15} {'Last Access':<19} {'Status':<15}"
        separator = "-" * len(header)
        
        lines = [separator, header, separator]
        for user in sorted(users_data.keys()):
            data = users_data[user]
            cards = ', '.join(sorted(data['cards']))
            last_access = f"{data['latest_date']} {data['latest_time']}"
            line = f"{user:<12} {data['count']:<7} {cards:<15} {last_access:<19} {data['status']:<15}"
            lines.append(line)
        lines.append(separator)
        
        return "\n".join(lines)

    def get_component_full_status(self, component_id: str) -> Optional[str]:
        """Get full status of a component."""
        if not self.session_key:
            if not self.login():
                return None

        try:
            url = f"{BASE_URL}/ComponentFullStatus/{component_id}?sdKey={self.session_key}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                return self.format_component_status(response.text)
            else:
                print(f"Get component status failed. Status: {response.status_code}, Body: {response.text}")
        except Exception as e:
            print(f"Get component status exception: {e}")

        return None

    def get_events(self) -> Optional[str]:
        """Get events from the system."""
        if not self.session_key:
            if not self.login():
                return None

        try:
            url = f"{BASE_URL}/Events?sdKey={self.session_key}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                return response.text
            else:
                print(f"Get events failed. Status: {response.status_code}, Body: {response.text}")
        except Exception as e:
            print(f"Get events exception: {e}")

        return None

    def format_component_status(self, xml_data: str) -> str:
        """Format component full status from XML."""
        try:
            root = ET.fromstring(xml_data)
            statuses = []

            for line_status in root.findall('.//LineStatus'):
                status_elem = line_status.find('Status')
                if status_elem is not None and status_elem.text:
                    statuses.append(status_elem.text)

            if not statuses:
                return "No status lines found"

            header = f"{'Line':<6} {'Status':<50}"
            separator = "-" * len(header)
            
            lines = [separator, header, separator]
            for idx, status in enumerate(statuses, 1):
                line = f"{idx:<6} {status:<50}"
                lines.append(line)
            lines.append(separator)
            
            return "\n".join(lines)

        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            return "Error parsing component status"
