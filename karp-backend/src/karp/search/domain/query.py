import typing

import pydantic


class Query(pydantic.BaseModel):  # noqa: D101
    fields: list[str]
    resources: list[str]
    sort: list[str]
    from_: int = pydantic.Field(0, alias="from")
    size: int = 25
    split_results: bool = False
    lexicon_stats: bool = True
    include_fields: typing.Optional[list[str]] = None
    exclude_fields: typing.Optional[list[str]] = None
    q: typing.Optional[str] = None
    sort_dict: typing.Optional[dict[str, list[str]]] = pydantic.Field(
        default_factory=dict
    )

    @pydantic.validator(
        "resources", "include_fields", "exclude_fields", "sort", pre=True
    )
    def split_str(cls, v):  # noqa: ANN206, D102
        return v.split(",") if isinstance(v, str) else v

    @pydantic.validator("fields", "sort", pre=True, always=True)
    def set_ts_now(cls, v):  # noqa: ANN206, D102
        return v or []

    class Config:  # noqa: D106
        arbitrary_types_allowed = True
