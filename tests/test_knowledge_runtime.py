from __future__ import annotations

from scripts.plan_consultation import plan
from scripts.query_knowledge_plugins import query


def _plugin_ids(result: dict) -> set[str]:
    return {item["id"] for item in result["plugins"]}


def test_relationship_topic_adapter_is_runtime_visible() -> None:
    result = query(topic="relationship", limit=0)

    assert "interpretation-topic-adapters" in _plugin_ids(result)
    assert any(item["id"] == "love_relationship" for item in result["topic_modules"])


def test_children_topic_adapter_is_runtime_visible() -> None:
    result = query(topic="education", limit=0)

    assert "interpretation-topic-adapters" in _plugin_ids(result)
    assert any(item["id"] == "children_education" for item in result["topic_modules"])


def test_all_children_route_aliases_reach_the_same_topic_adapter() -> None:
    for topic in ("children", "schooling", "parenting"):
        result = query(topic=topic, limit=0)
        assert any(item["id"] == "children_education" for item in result["topic_modules"])


def test_home_remains_property_route_and_family_route_is_unambiguous() -> None:
    assert plan(topic="home")["route_id"] == "property_wealth"
    assert plan(topic="household")["route_id"] == "relationship_family"
