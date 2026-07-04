import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from models.task import Task
from repositories.task import task_repository, category_repository, reminder_repository
from services.analytics import analytics_service
from schemas.ai import IntentRouterOutput
from core.exceptions import BadRequestException, NotFoundException

logger = logging.getLogger(__name__)


class DatabaseAgentService:
    async def execute_intent(
        self, db: AsyncSession, user_id: int, router_output: IntentRouterOutput, background_tasks = None
    ) -> Dict[str, Any]:
        """Execute the structural database intent safely using SQLAlchemy ORM."""
        intent = router_output.intent
        logger.info(f"Database Agent executing intent: {intent} for user: {user_id}")

        if intent == "CREATE_TASK":
            return await self._create_task(db, user_id, router_output, background_tasks)
            
        elif intent == "UPDATE_TASK":
            return await self._update_task(db, user_id, router_output, background_tasks)
            
        elif intent == "DELETE_TASK":
            return await self._delete_task(db, user_id, router_output)
            
        elif intent == "COMPLETE_TASK":
            return await self._complete_task(db, user_id, router_output)
            
        elif intent == "QUERY_DATABASE":
            return await self._query_database(db, user_id, router_output)
            
        elif intent == "CALENDAR_QUERY":
            return await self._calendar_query(db, user_id, router_output)
            
        elif intent == "ANALYTICS":
            metrics = await analytics_service.get_productivity_metrics(db, user_id)
            return {
                "success": True,
                "message": "Analytics compiled successfully",
                "data": metrics
            }
            
        else:
            raise BadRequestException(detail=f"Unhandled database agent intent: {intent}")

    async def _create_task(
        self, db: AsyncSession, user_id: int, router_output: IntentRouterOutput, background_tasks
    ) -> Dict[str, Any]:
        if not router_output.title:
            raise BadRequestException(detail="Task title is required for creation")

        # 1. Resolve Category
        category_id = None
        if router_output.category:
            category = await category_repository.get_or_create(db, user_id=user_id, name=router_output.category)
            category_id = category.id

        # 2. Parse due date
        due_date = None
        if router_output.due_date:
            try:
                due_date = datetime.fromisoformat(router_output.due_date)
            except ValueError:
                # Fallback if parsing fails
                logger.warning(f"Could not parse due date: {router_output.due_date}")

        # 3. Create Task
        task_data = {
            "title": router_output.title,
            "description": router_output.description,
            "due_date": due_date,
            "priority": router_output.priority or "normal",
            "status": "pending",
            "user_id": user_id,
            "category_id": category_id
        }
        
        task = await task_repository.create(db, obj_in=task_data)

        # 4. Create default reminders if due date is provided
        reminders_created = []
        if due_date:
            # Create a reminder 1 hour before due date
            reminder_time = due_date - timedelta(hours=1)
            reminder = await reminder_repository.create(
                db,
                obj_in={
                    "user_id": user_id,
                    "task_id": task.id,
                    "title": f"Reminder: {task.title}",
                    "reminder_time": reminder_time,
                    "is_sent": False
                }
            )
            reminders_created.append({
                "id": reminder.id,
                "time": reminder.reminder_time.isoformat()
            })

        # 5. Trigger Async Embedding generation
        if background_tasks:
            from background.worker import background_worker
            background_tasks.add_task(background_worker.generate_task_embedding, task.id)

        return {
            "success": True,
            "message": "Task created successfully",
            "task": {
                "id": task.id,
                "title": task.title,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "priority": task.priority,
                "category": router_output.category,
                "reminders": reminders_created
            }
        }

    async def _update_task(
        self, db: AsyncSession, user_id: int, router_output: IntentRouterOutput, background_tasks
    ) -> Dict[str, Any]:
        task_query = router_output.task_search_query or router_output.title
        if not task_query:
            raise BadRequestException(detail="Specify task title or keywords to update")

        # Find target task
        tasks = await task_repository.search_by_title_keyword(db, user_id, task_query)
        if not tasks:
            raise NotFoundException(detail=f"No task found matching '{task_query}'")
            
        task = tasks[0] # Take best match

        # Update properties
        update_data = {}
        if router_output.title:
            update_data["title"] = router_output.title
        if router_output.description is not None:
            update_data["description"] = router_output.description
        if router_output.priority:
            update_data["priority"] = router_output.priority
        if router_output.due_date:
            try:
                update_data["due_date"] = datetime.fromisoformat(router_output.due_date)
            except ValueError:
                pass
        if router_output.category:
            category = await category_repository.get_or_create(db, user_id=user_id, name=router_output.category)
            update_data["category_id"] = category.id

        updated_task = await task_repository.update(db, db_obj=task, obj_in=update_data)
        
        # Trigger async embedding update
        if background_tasks:
            from background.worker import background_worker
            background_tasks.add_task(background_worker.generate_task_embedding, updated_task.id)

        return {
            "success": True,
            "message": "Task updated successfully",
            "task": {
                "id": updated_task.id,
                "title": updated_task.title,
                "due_date": updated_task.due_date.isoformat() if updated_task.due_date else None,
                "priority": updated_task.priority
            }
        }

    async def _complete_task(self, db: AsyncSession, user_id: int, router_output: IntentRouterOutput) -> Dict[str, Any]:
        task_query = router_output.task_search_query
        if not task_query:
            raise BadRequestException(detail="Specify task title or keywords to complete")

        tasks = await task_repository.search_by_title_keyword(db, user_id, task_query)
        if not tasks:
            raise NotFoundException(detail=f"No task found matching '{task_query}'")

        task = tasks[0]
        updated_task = await task_repository.update(db, db_obj=task, obj_in={"status": "completed"})

        return {
            "success": True,
            "message": "Task marked as completed",
            "task": {
                "id": updated_task.id,
                "title": updated_task.title,
                "status": updated_task.status
            }
        }

    async def _delete_task(self, db: AsyncSession, user_id: int, router_output: IntentRouterOutput) -> Dict[str, Any]:
        task_query = router_output.task_search_query
        if not task_query:
            raise BadRequestException(detail="Specify task title or keywords to delete")

        tasks = await task_repository.search_by_title_keyword(db, user_id, task_query)
        if not tasks:
            raise NotFoundException(detail=f"No task found matching '{task_query}'")

        task = tasks[0]
        await task_repository.remove(db, id=task.id)

        return {
            "success": True,
            "message": "Task deleted successfully",
            "task_id": task.id,
            "title": task.title
        }

    async def _query_database(self, db: AsyncSession, user_id: int, router_output: IntentRouterOutput) -> Dict[str, Any]:
        filter_query = router_output.sql_search_filter
        if not filter_query:
            # Return all tasks
            tasks = await task_repository.get_user_tasks(db, user_id)
        else:
            tasks = await task_repository.search_by_title_keyword(db, user_id, filter_query)

        return {
            "success": True,
            "count": len(tasks),
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "priority": t.priority,
                    "status": t.status
                }
                for t in tasks
            ]
        }

    async def _calendar_query(self, db: AsyncSession, user_id: int, router_output: IntentRouterOutput) -> Dict[str, Any]:
        # Resolve timeframe start and end
        now = datetime.now(timezone.utc)
        start_date = now
        end_date = now + timedelta(days=7) # Default 1 week

        if router_output.time_frame_start:
            try:
                start_date = datetime.fromisoformat(router_output.time_frame_start)
            except ValueError:
                pass
        if router_output.time_frame_end:
            try:
                end_date = datetime.fromisoformat(router_output.time_frame_end)
            except ValueError:
                pass

        tasks = await task_repository.get_tasks_in_range(db, user_id, start_date, end_date)

        return {
            "success": True,
            "timeframe": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "count": len(tasks),
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "priority": t.priority,
                    "status": t.status
                }
                for t in tasks
            ]
        }


db_agent_service = DatabaseAgentService()
