from types import SimpleNamespace

from services import llm_service


def test_parse_revision_json_accepts_fenced_json_with_prefix():
    result = llm_service.parse_revision_json(
        "Here is the revision:\n```json\n"
        '{"assistant_message":"Updated","report":"# Revised","sources":[]}'
        "\n```"
    )

    assert result["report"] == "# Revised"


def test_generate_response_returns_model_content(monkeypatch):
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_: SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content="A concise answer")
                        )
                    ]
                )
            )
        )
    )
    monkeypatch.setattr(llm_service, "get_client", lambda: fake_client)

    assert llm_service.generate_response("Explain decorators") == "A concise answer"


def test_parse_revision_json_rejects_non_object():
    try:
        llm_service.parse_revision_json("[1, 2, 3]")
    except RuntimeError as error:
        assert "JSON object" in str(error)
    else:
        raise AssertionError("Expected invalid revision JSON to be rejected")