# app/services/ingest_service.py
"""
Ingestion Service - Core business logic for processing BLE packets
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from app.core.config import settings
from app.core.exceptions import DatabaseException
from app.domain.validators import BLEPacketValidator
from app.domain.models import BLESighting
from tags import get_tag_by_mac
from app.utils.mac_utils import normalize_mac
from app.core.logging_config import BLELogger

logger = structlog.get_logger("ingest_service")

class IngestService:
    """Service for ingesting and processing BLE packets"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = BLEPacketValidator()
    
    def ingest_packet(
        self,
        mac: str,
        rssi: int,
        timestamp: Optional[str] = None,
        gateway_ip: Optional[str] = None,
        raw_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest a BLE packet from a gateway.
        
        Args:
            mac: MAC address
            rssi: RSSI value
            timestamp: Optional timestamp
            gateway_ip: Optional gateway IP
            raw_data: Optional raw packet data
        
        Returns:
            Dictionary with ingestion result
        
        Raises:
            InvalidMACException: If MAC is invalid
            InvalidRSSIException: If RSSI is invalid
            DatabaseException: If database operation fails
        """
        # Step 1: Validate and normalize MAC
        normalized_mac = self.validator.validate_mac(mac)
        
        # Step 2: Validate RSSI
        validated_rssi = self.validator.validate_rssi(rssi)
        
        # Step 3: Validate timestamp
        validated_ts = self.validator.validate_timestamp(timestamp)
        
        # Step 4: Validate gateway IP
        validated_ip = self.validator.validate_gateway_ip(gateway_ip)
        
        # Step 5: Identify tag
        tag_info = get_tag_by_mac(normalized_mac)
        tag_name = tag_info["name"] if tag_info else None
        
        # Step 6: Create database record
        sighting = self._create_sighting_record(
            mac=normalized_mac,
            rssi=validated_rssi,
            timestamp=validated_ts,
            tag_name=tag_name,
            gateway_ip=validated_ip
        )
        
        # Step 7: Log the ingestion
        BLELogger.log_ingestion(
            mac=normalized_mac,
            rssi=validated_rssi,
            tag_name=tag_name,
            gateway_ip=validated_ip
        )
        
        # Step 8: Return response
        return {
            "status": "ok",
            "known_tag": tag_info is not None,
            "mac": normalized_mac,
            "tag_name": tag_name,
            "tag_info": tag_info,
            "sighting_id": sighting.id,
            "timestamp": sighting.ts_utc.isoformat() if sighting.ts_utc else None,
            "rssi": validated_rssi
        }
    
    def _create_sighting_record(
        self,
        mac: str,
        rssi: int,
        timestamp: Optional[datetime],
        tag_name: Optional[str],
        gateway_ip: Optional[str]
    ) -> BLESighting:
        """
        Create a sighting record in the database.
        
        Args:
            mac: Normalized MAC address
            rssi: RSSI value
            timestamp: Timestamp
            tag_name: Tag name
            gateway_ip: Gateway IP
        
        Returns:
            Created BLESighting object
        
        Raises:
            DatabaseException: If creation fails
        """
        try:
            sighting = BLESighting(
                mac=mac,
                rssi=rssi,
                ts_utc=timestamp or datetime.utcnow(),
                tag_name=tag_name,
                gateway_ip=gateway_ip
            )
            
            self.db.add(sighting)
            self.db.flush()  # Get the ID without committing
            
            BLELogger.log_database_operation("create_sighting", mac, success=True)
            
            return sighting
            
        except Exception as e:
            BLELogger.log_database_operation("create_sighting", mac, success=False)
            logger.error("sighting_creation_failed", mac=mac, error=str(e))
            raise DatabaseException("create_sighting", {"mac": mac, "error": str(e)})
    
    def batch_ingest(
        self,
        packets: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Ingest multiple BLE packets in a batch.
        
        Args:
            packets: List of packet dictionaries
        
        Returns:
            Batch ingestion results
        """
        results = {
            "total": len(packets),
            "successful": 0,
            "failed": 0,
            "errors": [],
            "results": []
        }
        
        for i, packet in enumerate(packets):
            try:
                result = self.ingest_packet(
                    mac=packet.get("mac"),
                    rssi=packet.get("rssi"),
                    timestamp=packet.get("timestamp"),
                    gateway_ip=packet.get("gateway_ip"),
                    raw_data=packet.get("raw_data", {})
                )
                results["successful"] += 1
                results["results"].append(result)
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "index": i,
                    "mac": packet.get("mac", "unknown"),
                    "error": str(e)
                })
                logger.warning("batch_ingest_failed", index=i, error=str(e))
        
        logger.info("batch_ingest_completed", 
                   total=results["total"],
                   successful=results["successful"],
                   failed=results["failed"])
        
        return results