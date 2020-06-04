from karp.domain.model.resource import Resource, ResourceRepository


def init_resource(resource: Resource, resource_repo: ResourceRepository):
    for dependency in resource.resource_dependencies:
        print(f"handling dependency: {dependency}")
