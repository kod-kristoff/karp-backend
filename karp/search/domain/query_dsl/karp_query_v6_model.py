#!/usr/bin/env python

# CAVEAT UTILITOR
#
# This file was automatically generated by TatSu.
#
#    https://pypi.python.org/pypi/tatsu/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.

from __future__ import annotations

from typing import Any
from dataclasses import dataclass

from tatsu.objectmodel import Node
from tatsu.semantics import ModelBuilderSemantics


class ModelBase(Node):
    pass


class KarpQueryV6ModelBuilderSemantics(ModelBuilderSemantics):
    def __init__(self, context=None, types=None):
        types = [
            t
            for t in globals().values()
            if type(t) is type and issubclass(t, ModelBase)
        ] + (types or [])
        super(KarpQueryV6ModelBuilderSemantics, self).__init__(
            context=context, types=types
        )


@dataclass
class And(ModelBase):
    exps: Any = None
    op: Any = None


@dataclass
class Contains(ModelBase):
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass
class Endswith(ModelBase):
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass
class Equals(ModelBase):
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass
class Exists(ModelBase):
    field: Any = None
    op: Any = None


@dataclass
class Freergxp(ModelBase):
    arg: Any = None
    op: Any = None


@dataclass
class FreetextAnyButString(ModelBase):
    arg: Any = None
    op: Any = None


@dataclass
class FreetextString(ModelBase):
    arg: Any = None
    op: Any = None


@dataclass
class Gt(ModelBase):
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass
class Gte(ModelBase):
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass
class Lt(ModelBase):
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass
class Lte(ModelBase):
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass
class Missing(ModelBase):
    field: Any = None
    op: Any = None


@dataclass
class Not(ModelBase):
    exps: Any = None
    op: Any = None


@dataclass
class Or(ModelBase):
    exps: Any = None
    op: Any = None


@dataclass
class Regexp(ModelBase):
    arg: Any = None
    field: Any = None
    op: Any = None


@dataclass
class Startswith(ModelBase):
    arg: Any = None
    field: Any = None
    op: Any = None
