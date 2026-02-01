from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from fastapi.responses import JSONResponse


class AppBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        validate_assignment=True,
        from_attributes=True,
    )


class MetaResponse(AppBaseModel):
    trace_id: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(AppBaseModel):
    trace_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    error_type: str
    message: str
    # model_config = {
    #     "json_encoders": {
    #         datetime: lambda v: v.isoformat(),
    #     }
    # }
