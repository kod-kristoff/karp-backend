"""Unit of Work"""
from functools import singledispatch
from typing import ContextManager


def unit_of_work(*, using) -> ContextManager:
    return create_unit_of_work(using)


@singledispatch
def create_unit_of_work(repo):
    raise NotImplementedError(f"Can't handle repository '{repo!r}'")
