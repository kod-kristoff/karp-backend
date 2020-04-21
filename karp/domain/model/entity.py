"""Entity"""


class Entity:
    def __init__(self, entity_id):
        self._id = entity_id

    @property
    def id(self):
        return self._id


class VersionedEntity(Entity):
    def __init__(self, entity_id, version):
        super().__init__(entity_id)
        self._version = version

    @property
    def version(self) -> int:
        return self._version
