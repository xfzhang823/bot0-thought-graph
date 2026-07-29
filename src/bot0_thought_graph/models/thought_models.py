"""Deterministic models for unindexed thought graphs."""

import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class SubThoughtJSONModel(BaseModel):
    name: str = Field(..., description="The name of the sub-thought")
    description: str = Field(..., description="A description of the sub-thought")
    importance: Optional[str] = Field(None, description="The importance of the sub-thought, optional")
    connection_to_next: Optional[str] = Field(
        None, description="Description of how this sub-thought connects to the next, optional"
    )


class ThoughtJSONModel(BaseModel):
    thought: str = Field(..., description="The main thought or concept")
    description: Optional[str] = Field(None, description="A description of the main thought")
    sub_thoughts: Optional[List[SubThoughtJSONModel]] = Field(
        None, description="An optional list of sub-thoughts associated with the main thought"
    )

    class Config:
        from_attributes = True
        json_encoders = {Optional: lambda v: v or None}
        exclude_none = True


class ClusterJSONModel(BaseModel):
    name: str = Field(..., description="Name of the cluster")
    description: Optional[str] = Field(None, description="Description of the cluster")
    thoughts: List[str] = Field(..., description="List of thought names within the cluster")

    class Config:
        from_attribute = True
        json_encoders = {Optional: lambda v: v or None}


class IdeaClusterJSONModel(BaseModel):
    idea: str = Field(..., description="The overarching theme or idea")
    clusters: List[ClusterJSONModel] = Field(..., description="List of clusters")


class IdeaJSONModel(BaseModel):
    idea: str = Field(..., description="The overarching theme or idea.")
    thoughts: Optional[List[ThoughtJSONModel]] = Field(
        None, description="A list of individual thoughts without clustering."
    )

    class Config:
        from_attribute = True
        json_encoders = {Optional: lambda v: v or None}


def validate_thought_batch(thought_data_batch: List[dict]) -> List[ThoughtJSONModel]:
    """Validate each thought and return only valid entries."""
    validated_thoughts = []
    for idx, data in enumerate(thought_data_batch):
        try:
            validated_thoughts.append(ThoughtJSONModel(**data))
        except ValidationError as exc:
            logger.error("Validation error in batch item at index %s: %s", idx, exc)
    return validated_thoughts


class EvalJSONModel(BaseModel):
    """Placeholder model for generic evaluation data."""

    data: Union[Dict[str, Any], List[Dict[str, Any]]]
