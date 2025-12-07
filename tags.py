# tags.py
"""
Static BLE Tag Configuration - Single Source of Truth
All BLE tags MUST be defined manually here. NO auto-generation.
"""

from typing import Dict, List, Optional
import re

# ============================================================================
# CRITICAL: STATIC TAG LIST - MANUALLY DEFINED
# ============================================================================

TAGS: List[Dict[str, str]] = [
    # Wheelchairs
    {"name": "WHEELCHAIR_A", "mac": "AA:BB:CC:DD:EE:01", "type": "equipment", "location": "ward_a"},
    {"name": "WHEELCHAIR_B", "mac": "AA:BB:CC:DD:EE:02", "type": "equipment", "location": "ward_b"},
    {"name": "WHEELCHAIR_C", "mac": "AA:BB:CC:DD:EE:03", "type": "equipment", "location": "emergency"},
    
    # Patients
    {"name": "PATIENT_1",    "mac": "AA:BB:CC:DD:EE:04", "type": "patient", "room": "201"},
    {"name": "PATIENT_2",    "mac": "AA:BB:CC:DD:EE:05", "type": "patient", "room": "202"},
    {"name": "PATIENT_3",    "mac": "AA:BB:CC:DD:EE:06", "type": "patient", "room": "icu_1"},
    
    # Medical Staff
    {"name": "NURSE_1",      "mac": "AA:BB:CC:DD:EE:07", "type": "staff", "role": "head_nurse"},
    {"name": "NURSE_2",      "mac": "AA:BB:CC:DD:EE:08", "type": "staff", "role": "rn"},
    {"name": "DOCTOR_1",     "mac": "AA:BB:CC:DD:EE:09", "type": "staff", "role": "surgeon"},
    
    # Medical Equipment
    {"name": "IV_PUMP_1",    "mac": "AA:BB:CC:DD:EE:0A", "type": "equipment", "location": "pharmacy"},
    {"name": "DEFIB_1",      "mac": "AA:BB:CC:DD:EE:0B", "type": "equipment", "location": "emergency"},
    {"name": "VENTILATOR_1", "mac": "AA:BB:CC:DD:EE:0C", "type": "equipment", "location": "icu_1"},
]

# Create lookup dictionaries for O(1) access
TAG_BY_MAC: Dict[str, Dict[str, str]] = {}
TAG_BY_NAME: Dict[str, Dict[str, str]] = {}

for tag in TAGS:
    normalized_mac = normalize_mac(tag["mac"])
    TAG_BY_MAC[normalized_mac] = tag
    TAG_BY_NAME[tag["name"]] = tag

# ============================================================================
# MAC ADDRESS UTILITIES
# ============================================================================

def normalize_mac(mac_address: str) -> str:
    """
    Normalize MAC address to standard colon-separated uppercase format.
    
    Args:
        mac_address: MAC in any format (aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, aabbccddeeff)
    
    Returns:
        Normalized MAC address in AA:BB:CC:DD:EE:FF format
    
    Raises:
        ValueError: If MAC address cannot be normalized
    """
    if not mac_address or not isinstance(mac_address, str):
        raise ValueError(f"Invalid MAC address: {mac_address}")
    
    # Remove all separators and convert to uppercase
    clean_mac = re.sub(r'[:\-\.\s]', '', mac_address).upper()
    
    # Validate length
    if len(clean_mac) != 12:
        raise ValueError(f"MAC address must be 12 hex characters, got {len(clean_mac)}: {mac_address}")
    
    # Validate hex characters
    if not re.match(r'^[0-9A-F]{12}$', clean_mac):
        raise ValueError(f"Invalid hex characters in MAC address: {mac_address}")
    
    # Insert colons every 2 characters
    normalized = ':'.join(clean_mac[i:i+2] for i in range(0, 12, 2))
    
    return normalized

def validate_mac_format(mac_address: str) -> bool:
    """
    Validate MAC address format without raising exceptions.
    
    Args:
        mac_address: MAC address to validate
    
    Returns:
        True if MAC address is valid, False otherwise
    """
    try:
        normalize_mac(mac_address)
        return True
    except ValueError:
        return False

def get_tag_by_mac(mac_address: str) -> Optional[Dict[str, str]]:
    """
    Get tag information by MAC address (with normalization).
    
    Args:
        mac_address: MAC address to look up
    
    Returns:
        Tag dictionary if found, None otherwise
    """
    try:
        normalized_mac = normalize_mac(mac_address)
        return TAG_BY_MAC.get(normalized_mac)
    except ValueError:
        return None

def get_all_tags() -> List[Dict[str, str]]:
    """
    Get all configured tags.
    
    Returns:
        List of all tag dictionaries
    """
    return TAGS.copy()

def is_known_tag(mac_address: str) -> bool:
    """
    Check if a MAC address corresponds to a known tag.
    
    Args:
        mac_address: MAC address to check
    
    Returns:
        True if tag is known, False otherwise
    """
    return get_tag_by_mac(mac_address) is not None