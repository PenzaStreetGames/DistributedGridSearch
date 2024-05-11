import enum
from typing import Optional

import pydantic


class ResponseStatus(enum.Enum):
    SUCCESS = 'success'
    FAILURE = 'failure'


class BaseResponse(pydantic.BaseModel):
    status: ResponseStatus
    message: Optional[str] = None
