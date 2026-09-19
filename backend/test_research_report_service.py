from services import research_report_service


def test_generate_research_report_saves_transparent_draft_when_unavailable(monkeypatch):
    def unavailable(_prompt):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(research_report_service, "_run_research", unavailable)

    report, sources = research_report_service.generate_research_report(
        topic="Future of renewable energy",
        profile={"audience": "general readers"},
        plan={
            "tasks": [
                {
                    "title": "Collect evidence",
                    "description": "Find authoritative sources.",
                }
            ]
        },
    )

    assert "transparent draft" in report
    assert "No findings are presented yet" in report
    assert sources == []