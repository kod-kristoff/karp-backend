from uuid import UUID
from typing import Dict, Iterable, Optional

from karp.domain.errors import ConfigurationError
from karp.domain.model.entry_repository import EntryRepository
from karp.domain.model.resource import Resource, ResourceCategory, ResourceRepository


class LexicalResource(
    Resource,
    resource_category=ResourceCategory.LEXICAL_RESOURCE,
    resource_type="lexical_resource_v1",
):
    """Model for a lexical resource.
    """

    def __init__(self, *args, entry_repository: EntryRepository = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._entry_repository = entry_repository

    @classmethod
    def from_dict(
        cls, config: Dict, resource_repository: Optional[ResourceRepository] = None
    ):
        resource_id = config["resource_id"]
        # resource_
        entry_repository = config.pop("entry_repository", None)
        if entry_repository is None:
            if "entry_repository_id" in config:
                if isinstance(config["entry_repository_id"], UUID):
                    config["entry_repository_id"] = str(config["entry_repository_id"])
                if resource_repository:
                    entry_repository = resource_repository.by_id(
                        config["entry_repository_id"]
                    )
                    if entry_repository is None:
                        raise ConfigurationError(
                            f"Can't load EntryRepository with id={config['entry_repository_id']}."
                        )
                else:
                    entry_repository = None
            else:
                if "entry_repository_type" not in config:
                    config[
                        "entry_repository_type"
                    ] = EntryRepository.get_default_repository_type()

                entry_respository_settings = config.pop(
                    "entry_repository_settings", None
                )

                if entry_respository_settings is None:
                    entry_respository_settings = EntryRepository.create_repository_settings(
                        config["entry_repository_type"], resource_id
                    )
                entry_repository = EntryRepository.create(
                    config["entry_repository_type"], entry_respository_settings
                )

        if "entry_repository_type" not in config:
            config[
                "entry_repository_type"
            ] = EntryRepository.get_default_repository_type()

        if entry_repository is not None:
            config["entry_repository_id"] = str(entry_repository.id)
        resource = super().from_dict(config, entry_repository=entry_repository)
        # resource._entry_repository = entry_repository
        return resource

    @property
    def entry_repository(self) -> EntryRepository:
        """The entry repository used by this resource."""
        return self._entry_repository

    @property
    def entry_repository_id(self) -> UUID:
        """The id for the entry repository used by this resource."""
        return UUID(self.config["entry_repository_id"], version=4)

    @property
    def entry_repository_type(self):
        return self.config["entry_repository_type"]

    @property
    def entry_repository_settings(self):
        return self.config["entry_repository_settings"]

    @property
    def _resource_dependencies(self) -> Iterable[UUID]:
        yield self.entry_repository_id
