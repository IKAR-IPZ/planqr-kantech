import xml.etree.ElementTree as ET
from typing import List, Dict
import pandas as pd
from datetime import datetime

def parse_smartlink_xml(xml_string: str) -> List[Dict]:
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


def format_access_logs_table(xml_data: str) -> str:
    """Format access logs as a nice table."""
    records = parse_smartlink_xml(xml_data)
    
    if not records:
        return "No records found"
    
    df = pd.DataFrame(records)
    
    display_cols = ['Access_ID', 'Date', 'Time', 'Card_ID', 'User', 'Status']
    df_display = df[display_cols]
    
    return df_display.to_string(index=False)


def format_access_logs_csv(xml_data: str, filename: str = None) -> str:
    """Export access logs as CSV."""
    records = parse_smartlink_xml(xml_data)
    
    if not records:
        return "No records found"
    
    df = pd.DataFrame(records)
    
    if filename:
        df.to_csv(filename, index=False)
        return f"Exported {len(records)} records to {filename}"
    else:
        return df.to_csv(index=False)


if __name__ == "__main__":
    xml_sample = '''<?xml version="1.0" encoding="utf-8"?><ArrayOfSmartLinkDataRow xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><SmartLinkDataRow><item><key><string>ACCESS1</string></key><value><SmartLinkDataValue><Value>2026-01-28  09:29:07 Access granted 004F:EAC4 gsliwinski</Value></SmartLinkDataValue></value></item><item><key><string>ACCESS2</string></key><value><SmartLinkDataValue><Value>2026-01-28  09:28:54 Access granted 004F:EAC4 gsliwinski</Value></SmartLinkDataValue></value></item><item><key><string>ACCESS3</string></key><value><SmartLinkDataValue><Value>2026-01-23  10:04:43 Access granted 004F:EAC4 gsliwinski</Value></SmartLinkDataValue></value></item><item><key><string>ACCESS4</string></key><value><SmartLinkDataValue><Value>2026-01-21  10:29:12 Access granted 00D7:FCA2 WISync_3</Value></SmartLinkDataValue></value></item><item><key><string>ACCESS5</string></key><value><SmartLinkDataValue><Value>2026-01-21  10:27:31 Access granted 004F:EAC4 gsliwinski</Value></SmartLinkDataValue></value></item></SmartLinkDataRow></ArrayOfSmartLinkDataRow>'''
    
    print("=== Access Log Summary ===\n")
    print(format_access_logs_table(xml_sample))
    print("\n=== CSV Export ===\n")
    print(format_access_logs_csv(xml_sample))
