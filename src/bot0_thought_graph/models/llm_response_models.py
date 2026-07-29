"""Provider-neutral response models used by domain services."""

from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pydantic import BaseModel, ConfigDict


class TextResponse(BaseModel):
    content: str
    model_config = ConfigDict(frozen=True)


class SubConcept(BaseModel):
    name: str
    description: str
    details: Optional[Dict[str, Union[str, List[str]]]] = None


class JSONResponse(BaseModel):
    data: Union[Dict[str, Any], List[Dict[str, Any]]]

    class Config:
        arbitrary_types_allowed = True


class TabularResponse(BaseModel):
    data: pd.DataFrame

    class Config:
        arbitrary_types_allowed = True


class CodeResponse(BaseModel):
    code: str

    class Config:
        arbitrary_types_allowed = True
