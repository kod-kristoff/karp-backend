from unittest import mock
import uuid

import pytest

from karp.domain.errors import (
    ConfigurationError,
    DiscardedEntityError,
)
from karp.domain.model.entry_repository import (
    EntryRepository,
)


def test_entry_repository_create_raises_configuration_error_on_nonexisting_type():
    with pytest.raises(ConfigurationError):
        EntryRepository.create("non-existing", {})


def test_entry_repository_has_class_attribute():
    assert EntryRepository.type == "entry_repository"
