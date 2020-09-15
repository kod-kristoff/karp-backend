from karp.domain.models.resource import Resource


def add_entries(resource: Resource):
    if resource is None:
        raise ValueError("Must provide resource.")
