class QueryDSLError(Exception):
    def __init__(self, message):
        super().__init__(message)


class ParseError(QueryDSLError):
    def __init__(self, message: str) -> None:
        super().__init__(message)

    def __repr__(self) -> str:
        return f"ParseError message='{self}'"


class SyntaxError(ParseError):
    def __init__(self, message: str):
        super().__init__(message)

    def __repr__(self) -> str:
        return f"SyntaxError message='{str(self)}'"