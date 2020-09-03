from pydantic import BaseModel, UUID4, Json


class ResourceBase(BaseModel):
    resource_id: str
    config: Json


class ResourceCreate(ResourceBase):
    pass


class Resource(ResourceBase):
    id: UUID4

    class Config:
        orm_mode = True
