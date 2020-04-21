class DomainError(Exception):
    """Base exception for domain errors.
    """

    pass


class ConsistencyError(DomainError):
    """Raised when an internal consistency problem is detected."""

    pass


class DeletedEntityError(DomainError):
    """Raised when an attempt is made to use a deleted Entity."""

    pass
