import pkg_resources


def get_resource_string(name: str) -> str:
    return pkg_resources.resource_string("karp", name).decode("utf-8")
