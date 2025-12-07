# app/utils/response_builder.py
"""
Response Builder - Consistent API response formatting
"""

from typing import Any, Dict, Optional, Union
from datetime import datetime
from fastapi import status
from fastapi.responses import JSONResponse
import structlog

from app.utils.time_utils import utc_now

logger = structlog.get_logger("response_builder")

class ResponseBuilder:
    """Build consistent API responses"""
    
    @staticmethod
    def ok(
        data: Any = None,
        message: str = "success",
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build success response.
        
        Args:
            data: Response data
            message: Success message
            meta: Additional metadata
        
        Returns:
            Formatted response dictionary
        """
        response = {
            "status": "ok",
            "message": message,
            "timestamp": utc_now().isoformat(),
            "data": data
        }
        
        if meta:
            response["meta"] = meta
        
        logger.debug("response_ok", message=message, data_type=type(data).__name__)
        return response
    
    @staticmethod
    def error(
        error_code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        Build error response.
        
        Args:
            error_code: Machine-readable error code
            message: Human-readable error message
            status_code: HTTP status code
            details: Additional error details
            request_id: Request ID for tracing
        
        Returns:
            JSONResponse with error details
        """
        error_response = {
            "status": "error",
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": utc_now().isoformat()
            }
        }
        
        if details:
            error_response["error"]["details"] = details
        
        if request_id:
            error_response["request_id"] = request_id
        
        logger.warning(
            "api_error",
            error_code=error_code,
            message=message,
            status_code=status_code,
            details=details
        )
        
        return JSONResponse(
            content=error_response,
            status_code=status_code
        )
    
    @staticmethod
    def paginated(
        data: list,
        total: int,
        page: int,
        page_size: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Build paginated response.
        
        Args:
            data: Page data
            total: Total number of items
            page: Current page (1-indexed)
            page_size: Items per page
        
        Returns:
            Paginated response dictionary
        """
        total_pages = (total + page_size - 1) // page_size
        
        response = {
            "status": "ok",
            "timestamp": utc_now().isoformat(),
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }
        
        response.update(kwargs)
        
        logger.debug(
            "paginated_response",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(data)
        )
        
        return response
    
    @staticmethod
    def created(
        data: Any = None,
        message: str = "Resource created successfully",
        location: Optional[str] = None
    ) -> Union[Dict[str, Any], JSONResponse]:
        """
        Build created response.
        
        Args:
            data: Created resource data
            message: Success message
            location: URI of created resource
        
        Returns:
            Created response
        """
        response = {
            "status": "created",
            "message": message,
            "timestamp": utc_now().isoformat(),
            "data": data
        }
        
        if location:
            return JSONResponse(
                content=response,
                status_code=status.HTTP_201_CREATED,
                headers={"Location": location}
            )
        
        return response
    
    @staticmethod
    def no_content() -> JSONResponse:
        """
        Build no content response.
        
        Returns:
            No content response
        """
        return JSONResponse(
            content=None,
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @staticmethod
    def validation_error(
        errors: list,
        message: str = "Validation failed"
    ) -> JSONResponse:
        """
        Build validation error response.
        
        Args:
            errors: List of validation errors
            message: Error message
        
        Returns:
            Validation error response
        """
        return ResponseBuilder.error(
            error_code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"errors": errors}
        )