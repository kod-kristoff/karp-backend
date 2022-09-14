import pydantic
from karp.foundation import events


class DomainEvent(events.Event, pydantic.BaseModel):
    timestamp: float
