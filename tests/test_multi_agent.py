import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from schemas.ai import MultiAgentPlan, SubTask
from agents.master_orchestrator import master_orchestrator

LOCAL_TZ = ZoneInfo("Asia/Kolkata")


@pytest.mark.asyncio
async def test_master_orchestrator_query_decomposition():
    query = "Create a task to buy groceries tomorrow at 5pm AND show me my productivity stats AND check today's agenda"
    plan = await master_orchestrator.decompose_query(query)

    assert isinstance(plan, MultiAgentPlan)
    assert plan.user_query == query
    assert len(plan.sub_tasks) >= 2
    assert plan.is_multi_intent is True

    targets = {st.agent_target for st in plan.sub_tasks}
    assert "task_worker" in targets
    assert "analytics_worker" in targets


@pytest.mark.asyncio
async def test_single_intent_query_decomposition():
    query = "What is the weather like today?"
    plan = await master_orchestrator.decompose_query(query)

    assert isinstance(plan, MultiAgentPlan)
    assert len(plan.sub_tasks) >= 1
    assert plan.sub_tasks[0].agent_target == "chat_worker"
