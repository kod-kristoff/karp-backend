"""Entity"""


class Entity:
    def __init__(self, entity_id):
        self._id = entity_id

    @property
    def id(self):
        return self._id


class VersionedEntity(Entity):
    pass
