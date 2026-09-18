from services.research_planner import create_research_plan


topic = "Impact of Generative AI on software development"

profile = {
    "purpose": "Academic project",
    "audience": "My professor",
    "depth": "Deep research",
}


plan = create_research_plan(
    topic=topic,
    profile=profile,
)


print("\n" + "=" * 60)
print("RESEARCH PLAN")
print("=" * 60)

print(plan)