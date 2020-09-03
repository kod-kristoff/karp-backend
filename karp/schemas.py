"""Schemas used by the app."""
from enum import Enum

# from karp.application.services.system_monitor import SystemMonitorResponse
from typing import Optional

from pydantic import BaseModel, UUID4, Json


class ProtectionLevel(str, Enum):
    read = "READ"
    write = "WRITE"
    admin = "ADMIN"


class ResourceBase(BaseModel):
    resource_id: str


class ResourceCreate(ResourceBase):
    pass


class ResourceOut(ResourceBase):
    """Schema used when returning resources from conf."""

    protected: Optional[ProtectionLevel]


class Resource(ResourceBase):
    id: UUID4

    class Config:
        orm_mode = True


class SystemMonitorResponse(BaseModel):
    database: str
