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


def test_revision_uses_plain_markdown_when_json_is_unavailable(monkeypatch):
    responses = iter([
        RuntimeError("structured output unavailable"),
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="# Revised report\n\n## Key findings\n\nUpdated evidence."
                    )
                )
            ]
        ),
    ])

    def fake_request(_prompt, structured=True):
        response = next(responses)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(llm_service, "_request_revision", fake_request)

    result = llm_service.revise_research_report(
        topic="Test topic",
        report="# Original report\n\n## Summary\n\nOriginal.",
        sources=[],
        conversation=[{"role": "user", "content": "Improve the evidence"}],
        request="Improve the evidence",
    )

    assert result["report"].startswith("# Revised report")


def test_revision_preserves_report_for_plain_user_facing_answer(monkeypatch):
    monkeypatch.setattr(
        llm_service,
        "_request_revision",
        lambda _prompt, structured=True: SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="The requested comparison is now clearer.")
                )
            ]
        ) if not structured else (_ for _ in ()).throw(RuntimeError("JSON unavailable")),
    )

    result = llm_service.revise_research_report(
        topic="Test topic",
        report="# Original report\n\n## Summary\n\nOriginal.",
        sources=[],
        conversation=[],
        request="Make the comparison clearer",
    )

    assert "# Original report" in result["report"]
    assert "The requested comparison is now clearer." in result["report"]