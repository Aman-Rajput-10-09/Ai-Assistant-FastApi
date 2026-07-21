from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from main import app
from models.task import Task
from models.user import User
from routers.deps import get_current_active_user

pytestmark = pytest.mark.asyncio


async def test_calendar_returns_tasks_without_lazy_loading_errors(client: AsyncClient, db_session):
    user = User(
        email="calendar@example.com",
        hashed_password="unused",
        full_name="Calendar Tester",
    )
    db_session.add(user)
    await db_session.flush()

    due_date = datetime.now(timezone.utc) + timedelta(days=1)
    task = Task(
        title="Calendar smoke task",
        due_date=due_date,
        priority="normal",
        status="pending",
        user_id=user.id,
    )
    db_session.add(task)
    await db_session.commit()

    async def override_current_user():
        return user

    app.dependency_overrides[get_current_active_user] = override_current_user
    try:
        response = await client.get("/api/v1/calendar")
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Calendar smoke task"
    assert data[0]["recurring_rules"] == []
    assert data[0]["attachments"] == []
