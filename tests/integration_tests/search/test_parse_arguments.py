from itertools import zip_longest


from karp import search
from karp.query_dsl import op



def _test_nodes(r, facit):
    for x, f in zip_longest(r.gen_stream(), facit):
        assert x is not None, "x is too short"
        assert f is not None, "x is too long"

        assert x.type == f[0]
        assert x.value == f[1]
        assert isinstance(x.value, type(f[1]))


def test_rewrite_ast(client_with_entries_scope_session):
    q = search.Query()
    q.parse_arguments({"q": "equals|state|X", "sort": "Y"}, "places")
    expected = [
        (op.EQUALS, None),
        (op.ARG_OR, None),
        (op.STRING, "state"),  # noqa: E131
        (op.STRING, "v_municipality.state"),
        (op.STRING, "X"),
    ]
    print("q.ast = {!r}".format(q.ast))
    _test_nodes(q.ast, expected)
