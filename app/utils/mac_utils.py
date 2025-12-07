# app/utils/mac_utils.py
"""
MAC Address Utilities - Pure functions for MAC manipulation
"""

import re
from typing import Optional
import structlog

logger = structlog.get_logger("mac_utils")

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
        logger.warning("invalid_mac_input", input=mac_address)
        raise ValueError(f"Invalid MAC address: {mac_address}")
    
    # Remove all separators and convert to uppercase
    clean_mac = re.sub(r'[:\-\.\s]', '', mac_address).upper()
    
    # Validate length
    if len(clean_mac) != 12:
        logger.warning("invalid_mac_length", input=mac_address, length=len(clean_mac))
        raise ValueError(f"MAC address must be 12 hex characters, got {len(clean_mac)}: {mac_address}")
    
    # Validate hex characters
    if not re.match(r'^[0-9A-F]{12}$', clean_mac):
        logger.warning("invalid_mac_characters", input=mac_address)
        raise ValueError(f"Invalid hex characters in MAC address: {mac_address}")
    
    # Insert colons every 2 characters
    normalized = ':'.join(clean_mac[i:i+2] for i in range(0, 12, 2))
    
    logger.debug("mac_normalized", original=mac_address, normalized=normalized)
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

def mac_to_manufacturer(mac_address: str) -> Optional[str]:
    """
    Attempt to identify manufacturer from MAC address (OUI lookup).
    
    Args:
        mac_address: MAC address
    
    Returns:
        Manufacturer name or None
    """
    # This is a simplified version. In production, use a proper OUI database.
    try:
        normalized = normalize_mac(mac_address)
        oui = normalized[:8]  # First 3 bytes
        
        # Common OUI prefixes (example)
        oui_database = {
            "AA:BB:CC": "Example Medical Devices Inc.",
            "00:0C:29": "VMware Virtual MAC",
            "00:50:56": "VMware Virtual MAC",
            "00:1A:11": "Google",
            "00:1B:63": "Apple",
            "00:1D:4F": "Cisco",
            "00:24:D4": "Samsung",
        }
        
        return oui_database.get(oui)
    except ValueError:
        return None

def format_mac_human_readable(mac_address: str) -> str:
    """
    Format MAC address for human-readable display.
    
    Args:
        mac_address: MAC address
    
    Returns:
        Formatted MAC address
    """
    try:
        normalized = normalize_mac(mac_address)
        return normalized.lower()  # Lowercase is often more readable
    except ValueError:
        return mac_address  # Return original if invalid

def is_multicast_mac(mac_address: str) -> bool:
    """
    Check if MAC address is a multicast/broadcast address.
    
    Args:
        mac_address: MAC address
    
    Returns:
        True if multicast/broadcast, False otherwise
    """
    try:
        normalized = normalize_mac(mac_address)
        first_byte = int(normalized[:2], 16)
        return bool(first_byte & 0x01)  # Multicast bit
    except ValueError:
        return False

def is_locally_administered_mac(mac_address: str) -> bool:
    """
    Check if MAC address is locally administered.
    
    Args:
        mac_address: MAC address
    
    Returns:
        True if locally administered, False otherwise
    """
    try:
        normalized = normalize_mac(mac_address)
        first_byte = int(normalized[:2], 16)
        return bool(first_byte & 0x02)  # Locally administered bit
    except ValueError:
        return False