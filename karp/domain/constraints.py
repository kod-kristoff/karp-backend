"""Constraints."""


def length_gt_zero(attribute, value):
    if len(value) == 0:
        raise ValueError(
            f"'{attribute}' has to be non-empty. Got {attribute}='{value}'"
        )
    return value
