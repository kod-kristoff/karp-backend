from karp.domain.model.lexicon import create_lexicon


def test_create_lexicon_creates_lexicon():
    lexicon_id = "test_lexicon"
    name = "Test lexicon"
    conf = {
        "lexicon_id": lexicon_id,
        "lexicon_name": name,
        "sort": ["baseform"],
        "fields": {"baseform": {"type": "string", "required": True}},
    }
    lexicon = create_lexicon(conf)

    assert lexicon.id is None
    assert lexicon.version is None
    assert lexicon.lexicon_id == lexicon_id
    assert lexicon.name == name
    assert not lexicon.is_deleted
    assert not lexicon.is_active
    assert "lexicon_id" not in lexicon.config
    assert "lexicon_name" not in lexicon.config
    assert "sort" in lexicon.config
    assert lexicon.config["sort"] == conf["sort"]
    assert "fields" in lexicon.config
    assert lexicon.config["fields"] == conf["fields"]
