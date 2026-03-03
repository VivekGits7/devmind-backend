from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


# ==================== BASE RESPONSE ====================


class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    success: bool = Field(default=True, description="Whether the request was successful")
    message: str = Field(..., description="Response message", examples=["Operation successful"])


# ==================== SWAGGER ERROR RESPONSE MODELS ====================


class ErrorDetail(BaseModel):
    """Individual validation error detail shown in 422 responses."""
    field: str = Field(
        ...,
        description="Dot-separated path to the invalid field",
        examples=["body.email"],
    )
    message: str = Field(
        ...,
        description="Human-readable validation error message",
        examples=["value is not a valid email address"],
    )
    type: str = Field(
        ...,
        description="Machine-readable error type identifier",
        examples=["value_error.email"],
    )


class ErrorBody(BaseModel):
    """Structured error information returned in all error responses."""
    status_code: int = Field(..., description="HTTP status code of the error", examples=[400])
    status_message: str = Field(
        ...,
        description="HTTP status text (e.g., BAD REQUEST, NOT FOUND)",
        examples=["BAD REQUEST"],
    )
    message: str = Field(
        ...,
        description="User-friendly error message",
        examples=["Invalid request. Please check your input."],
    )
    code: Optional[str] = Field(
        None,
        description="Machine-readable error code for client-side handling",
        examples=["BAD_REQUEST"],
    )
    details: Optional[List[ErrorDetail]] = Field(
        None,
        description="List of individual field validation errors (only for 422)",
    )


# ---- 400 Bad Request ----
class BadRequestResponse(BaseModel):
    """Returned when the request data is invalid or malformed."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorBody = Field(..., description="Error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "status_code": 400,
                    "status_message": "BAD REQUEST",
                    "message": "Invalid request. Please check your input.",
                    "code": "BAD_REQUEST",
                },
            }
        }
    )


# ---- 401 Unauthorized ----
class UnauthorizedResponse(BaseModel):
    """Returned when authentication is missing or token is invalid/expired."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorBody = Field(..., description="Error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "status_code": 401,
                    "status_message": "UNAUTHORIZED",
                    "message": "Please log in to continue.",
                    "code": "UNAUTHORIZED",
                },
            }
        }
    )


# ---- 403 Forbidden ----
class ForbiddenResponse(BaseModel):
    """Returned when the user does not have permission to access the resource."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorBody = Field(..., description="Error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "status_code": 403,
                    "status_message": "FORBIDDEN",
                    "message": "You don't have permission to access this resource.",
                    "code": "FORBIDDEN",
                },
            }
        }
    )


# ---- 404 Not Found ----
class NotFoundResponse(BaseModel):
    """Returned when the requested resource does not exist."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorBody = Field(..., description="Error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "status_code": 404,
                    "status_message": "NOT FOUND",
                    "message": "The requested resource was not found.",
                    "code": "NOT_FOUND",
                },
            }
        }
    )


# ---- 409 Conflict ----
class ConflictResponse(BaseModel):
    """Returned when the request conflicts with existing data (e.g., duplicate email)."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorBody = Field(..., description="Error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "status_code": 409,
                    "status_message": "CONFLICT",
                    "message": "This resource already exists.",
                    "code": "CONFLICT",
                },
            }
        }
    )


# ---- 422 Validation Error ----
class ValidationErrorResponse(BaseModel):
    """Returned when request body fails Pydantic schema validation."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorBody = Field(..., description="Error details with per-field validation errors")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "status_code": 422,
                    "status_message": "UNPROCESSABLE ENTITY",
                    "message": "Please check your input and try again.",
                    "code": "VALIDATION_ERROR",
                    "details": [
                        {
                            "field": "body.email",
                            "message": "value is not a valid email address",
                            "type": "value_error.email",
                        }
                    ],
                },
            }
        }
    )


# ---- 429 Too Many Requests ----
class RateLimitResponse(BaseModel):
    """Returned when the client exceeds the rate limit for an endpoint."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorBody = Field(..., description="Error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "status_code": 429,
                    "status_message": "TOO MANY REQUESTS",
                    "message": "Rate limit exceeded. Please try again later.",
                    "code": "RATE_LIMITED",
                },
            }
        }
    )


# ---- 500 Internal Server Error ----
class InternalServerErrorResponse(BaseModel):
    """Returned when an unexpected server error occurs."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorBody = Field(..., description="Error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "status_code": 500,
                    "status_message": "INTERNAL SERVER ERROR",
                    "message": "Something went wrong. Please try again later.",
                    "code": "INTERNAL_ERROR",
                },
            }
        }
    )


# ---- 502 Bad Gateway ----
class BadGatewayResponse(BaseModel):
    """Returned when an external service (AI, payment, etc.) fails."""
    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorBody = Field(..., description="Error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "status_code": 502,
                    "status_message": "BAD GATEWAY",
                    "message": "Service temporarily unavailable. Please try again later.",
                    "code": "EXTERNAL_SERVICE_ERROR",
                },
            }
        }
    )


# ==================== COMMON SWAGGER RESPONSES ====================

COMMON_ERROR_RESPONSES = {
    401: {
        "model": UnauthorizedResponse,
        "description": "Authentication required or token invalid/expired",
    },
    422: {
        "model": ValidationErrorResponse,
        "description": "Request body failed schema validation",
    },
    429: {
        "model": RateLimitResponse,
        "description": "Rate limit exceeded for this endpoint",
    },
    500: {
        "model": InternalServerErrorResponse,
        "description": "Unexpected server error",
    },
}
