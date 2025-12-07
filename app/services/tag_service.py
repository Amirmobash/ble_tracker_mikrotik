# app/services/tag_service.py
"""
Tag Service - Business logic for tag management and queries
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import structlog

from app.core.config import settings
from app.core.exceptions import TagNotFoundException, DatabaseException
from app.domain.models import BLESighting
from tags import get_all_tags, get_tag_by_mac, TAG_BY_MAC
from app.utils.time_utils import utc_now
from app.core.logging_config import BLELogger

logger = structlog.get_logger("tag_service")

class TagService:
    """Service for tag-related operations and queries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_tag_statuses(self) -> List[Dict[str, Any]]:
        """
        Get current status for all configured tags.
        
        Returns:
            List of tag status dictionaries
        """
        tags = get_all_tags()
        results = []
        
        for tag in tags:
            try:
                status = self._get_tag_status(tag["mac"])
                results.append(status)
            except Exception as e:
                logger.warning("tag_status_failed", tag=tag["name"], error=str(e))
                # Include tag with error status
                results.append({
                    "name": tag["name"],
                    "mac": tag["mac"],
                    "error": str(e),
                    "status": "error"
                })
        
        return results
    
    def get_tag_status(self, mac_address: str) -> Dict[str, Any]:
        """
        Get detailed status for a specific tag.
        
        Args:
            mac_address: MAC address in any format
        
        Returns:
            Tag status dictionary
        
        Raises:
            TagNotFoundException: If tag not found
        """
        from app.utils.mac_utils import normalize_mac
        
        try:
            normalized_mac = normalize_mac(mac_address)
        except ValueError as e:
            raise TagNotFoundException(mac_address)
        
        tag_info = get_tag_by_mac(normalized_mac)
        if not tag_info:
            raise TagNotFoundException(normalized_mac)
        
        return self._get_tag_status(normalized_mac, tag_info)
    
    def _get_tag_status(
        self, 
        normalized_mac: str, 
        tag_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Internal method to get tag status.
        
        Args:
            normalized_mac: Normalized MAC address
            tag_info: Optional tag info from static config
        
        Returns:
            Tag status dictionary
        """
        # Get latest sighting
        latest_sighting = self.db.query(BLESighting)\
            .filter(BLESighting.mac == normalized_mac)\
            .order_by(desc(BLESighting.ts_utc))\
            .first()
        
        # Calculate presence
        is_present = False
        if latest_sighting:
            time_diff = (utc_now() - latest_sighting.ts_utc).total_seconds() / 60
            is_present = time_diff <= settings.TAG_TIMEOUT_MINUTES
        
        # Get tag info if not provided
        if not tag_info:
            tag_info = get_tag_by_mac(normalized_mac) or {}
        
        # Build response
        status = {
            "name": tag_info.get("name", "unknown"),
            "mac": normalized_mac,
            "type": tag_info.get("type", "unknown"),
            "is_present": is_present,
            "last_seen_utc": latest_sighting.ts_utc.isoformat() if latest_sighting else None,
            "last_rssi": latest_sighting.rssi if latest_sighting else None,
            "location": tag_info.get("location") or tag_info.get("room"),
            "metadata": {k: v for k, v in tag_info.items() 
                        if k not in ["name", "mac", "type", "location", "room"]}
        }
        
        # Add signal strength category
        if latest_sighting and latest_sighting.rssi:
            if latest_sighting.rssi >= -50:
                status["signal_strength"] = "excellent"
            elif latest_sighting.rssi >= -65:
                status["signal_strength"] = "good"
            elif latest_sighting.rssi >= -80:
                status["signal_strength"] = "fair"
            else:
                status["signal_strength"] = "poor"
        
        return status
    
    def get_tag_history(
        self, 
        mac_address: str, 
        hours: int = 24,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get history for a specific tag.
        
        Args:
            mac_address: MAC address
            hours: Hours of history to retrieve
            limit: Maximum number of records
        
        Returns:
            Tag history dictionary
        """
        from app.utils.mac_utils import normalize_mac
        
        try:
            normalized_mac = normalize_mac(mac_address)
        except ValueError as e:
            raise TagNotFoundException(mac_address)
        
        # Get tag info
        tag_info = get_tag_by_mac(normalized_mac)
        if not tag_info:
            raise TagNotFoundException(normalized_mac)
        
        # Calculate time cutoff
        cutoff_time = utc_now() - timedelta(hours=hours)
        
        # Query sightings
        sightings = self.db.query(BLESighting)\
            .filter(
                BLESighting.mac == normalized_mac,
                BLESighting.ts_utc >= cutoff_time
            )\
            .order_by(desc(BLESighting.ts_utc))\
            .limit(limit)\
            .all()
        
        # Calculate statistics
        if sightings:
            rssi_values = [s.rssi for s in sightings]
            avg_rssi = sum(rssi_values) / len(rssi_values)
            min_rssi = min(rssi_values)
            max_rssi = max(rssi_values)
        else:
            avg_rssi = min_rssi = max_rssi = None
        
        return {
            "tag": {
                "name": tag_info["name"],
                "mac": normalized_mac,
                "type": tag_info.get("type", "unknown")
            },
            "time_range_hours": hours,
            "sighting_count": len(sightings),
            "statistics": {
                "average_rssi": round(avg_rssi, 2) if avg_rssi is not None else None,
                "min_rssi": min_rssi,
                "max_rssi": max_rssi,
                "first_seen": sightings[-1].ts_utc.isoformat() if sightings else None,
                "last_seen": sightings[0].ts_utc.isoformat() if sightings else None
            },
            "sightings": [s.to_dict() for s in sightings]
        }
    
    def search_tags(
        self,
        query: Optional[str] = None,
        tag_type: Optional[str] = None,
        is_present: Optional[bool] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search tags with filters.
        
        Args:
            query: Search query (name or MAC)
            tag_type: Filter by tag type
            is_present: Filter by presence
            limit: Maximum results
        
        Returns:
            Search results
        """
        # Start with all tags
        all_tags = get_all_tags()
        filtered_tags = all_tags.copy()
        
        # Apply filters
        if query:
            query_lower = query.lower()
            filtered_tags = [
                t for t in filtered_tags
                if query_lower in t["name"].lower() or query_lower in t["mac"].lower()
            ]
        
        if tag_type:
            filtered_tags = [
                t for t in filtered_tags
                if t.get("type", "").lower() == tag_type.lower()
            ]
        
        # Get status for filtered tags
        results = []
        for tag in filtered_tags[:limit]:
            try:
                status = self._get_tag_status(tag["mac"], tag)
                
                # Filter by presence if requested
                if is_present is not None:
                    if status["is_present"] == is_present:
                        results.append(status)
                else:
                    results.append(status)
                    
            except Exception as e:
                logger.warning("tag_search_failed", tag=tag["name"], error=str(e))
        
        return {
            "total_found": len(filtered_tags),
            "returned": len(results),
            "tags": results
        }