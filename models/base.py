from pydantic import BaseModel, ConfigDict
from datetime import datetime


class AppBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        validate_assignment=True,
    )


class MetaResponse(AppBaseModel):
    trace_id: str
    timestamp: datetime


class ErrorResponse(AppBaseModel):
    trace_id: str
    timestamp: datetime
    error_type: str
    message: str
    # model_config = {
    #     "json_encoders": {
    #         datetime: lambda v: v.isoformat(),
    #     }
    # }
