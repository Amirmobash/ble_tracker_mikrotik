# app/utils/time_utils.py
"""
Time Utilities - Consistent time handling across the system
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Union
import structlog

logger = structlog.get_logger("time_utils")

def utc_now() -> datetime:
    """
    Get current UTC time with timezone awareness.
    
    Returns:
        Current UTC datetime
    """
    return datetime.now(timezone.utc)

def parse_timestamp(timestamp: Union[str, int, float, datetime]) -> datetime:
    """
    Parse timestamp from various formats to UTC datetime.
    
    Args:
        timestamp: Timestamp in ISO string, Unix timestamp, or datetime
    
    Returns:
        UTC datetime
    
    Raises:
        ValueError: If timestamp cannot be parsed
    """
    if isinstance(timestamp, datetime):
        # Ensure datetime is timezone aware
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)
    
    elif isinstance(timestamp, (int, float)):
        # Unix timestamp
        try:
            dt = datetime.fromtimestamp(timestamp, timezone.utc)
            logger.debug("timestamp_parsed", source="unix", value=timestamp, result=dt.isoformat())
            return dt
        except (ValueError, OSError) as e:
            logger.warning("timestamp_parse_failed", source="unix", value=timestamp, error=str(e))
            raise ValueError(f"Invalid Unix timestamp: {timestamp}")
    
    elif isinstance(timestamp, str):
        # ISO format string
        try:
            # Try ISO format first
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Ensure timezone awareness
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            
            logger.debug("timestamp_parsed", source="iso", value=timestamp, result=dt.isoformat())
            return dt.astimezone(timezone.utc)
            
        except ValueError:
            # Try other common formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%d-%m-%Y %H:%M:%S",
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp, fmt)
                    dt = dt.replace(tzinfo=timezone.utc)
                    logger.debug("timestamp_parsed", source=fmt, value=timestamp, result=dt.isoformat())
                    return dt
                except ValueError:
                    continue
            
            logger.warning("timestamp_parse_failed", source="string", value=timestamp)
            raise ValueError(f"Cannot parse timestamp: {timestamp}")
    
    else:
        logger.warning("timestamp_parse_failed", source=type(timestamp).__name__, value=str(timestamp))
        raise ValueError(f"Unsupported timestamp type: {type(timestamp)}")

def format_timestamp(dt: Optional[datetime] = None, format_str: str = "iso") -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime to format (defaults to current time)
        format_str: Format type ('iso', 'human', 'log')
    
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = utc_now()
    
    # Ensure UTC
    dt_utc = dt.astimezone(timezone.utc)
    
    if format_str == "iso":
        return dt_utc.isoformat().replace('+00:00', 'Z')
    
    elif format_str == "human":
        return dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    elif format_str == "log":
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
    elif format_str == "date_only":
        return dt_utc.strftime("%Y-%m-%d")
    
    elif format_str == "time_only":
        return dt_utc.strftime("%H:%M:%S")
    
    else:
        # Custom format
        return dt_utc.strftime(format_str)

def get_time_range(
    hours: Optional[int] = None,
    days: Optional[int] = None
) -> tuple[datetime, datetime]:
    """
    Get UTC time range for queries.
    
    Args:
        hours: Hours ago
        days: Days ago
    
    Returns:
        Tuple of (start_time, end_time)
    """
    end_time = utc_now()
    
    if hours is not None:
        start_time = end_time - timedelta(hours=hours)
    elif days is not None:
        start_time = end_time - timedelta(days=days)
    else:
        # Default to last 24 hours
        start_time = end_time - timedelta(hours=24)
    
    return start_time, end_time

def validate_timestamp_range(
    start_time: Optional[datetime],
    end_time: Optional[datetime],
    max_range_days: int = 30
) -> tuple[datetime, datetime]:
    """
    Validate and normalize timestamp range.
    
    Args:
        start_time: Start time
        end_time: End time
        max_range_days: Maximum allowed range in days
    
    Returns:
        Validated (start_time, end_time)
    
    Raises:
        ValueError: If range is invalid
    """
    now = utc_now()
    
    # Default values
    if end_time is None:
        end_time = now
    else:
        end_time = end_time.astimezone(timezone.utc)
    
    if start_time is None:
        start_time = end_time - timedelta(hours=24)
    else:
        start_time = start_time.astimezone(timezone.utc)
    
    # Validate order
    if start_time > end_time:
        raise ValueError("Start time must be before end time")
    
    # Validate range
    range_days = (end_time - start_time).total_seconds() / 86400
    if range_days > max_range_days:
        raise ValueError(f"Time range exceeds maximum of {max_range_days} days")
    
    # Ensure not in future
    if end_time > now + timedelta(minutes=5):  # Allow 5 minutes clock skew
        raise ValueError("End time cannot be in the future")
    
    return start_time, end_time

def humanize_duration(seconds: float) -> str:
    """
    Convert duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Human-readable duration
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
    else:
        days = seconds / 86400
        return f"{days:.1f} days"