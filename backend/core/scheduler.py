from datetime import datetime, timezone
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import async_session
from models.models import Crew
from core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

class CrewScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.orchestrator_instance = None

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Crew Scheduler started.")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Crew Scheduler shut down.")

    async def _run_scheduled_crew(self, crew_id: str):
        """Execute a crew in the background."""
        logger.info(f"⏰ Executing scheduled crew: {crew_id}")
        async with async_session() as db:
            crew = await db.get(Crew, crew_id)
            if not crew:
                logger.error(f"Crew {crew_id} not found for scheduling.")
                return

            orchestrator = Orchestrator(db)
            try:
                await orchestrator.execute_crew(crew)
                logger.info(f"✅ Scheduled execution of crew {crew_id} finished.")
            except Exception as e:
                logger.error(f"❌ Error in scheduled execution of crew {crew_id}: {str(e)}")

    def schedule_crew(self, crew: Crew):
        """Add or update a crew's schedule in the scheduler."""
        job_id = f"crew_{crew.id}"
        
        # Remove existing job if any
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        if crew.schedule_type == "none":
            return

        trigger = None
        try:
            if crew.schedule_type == "interval":
                # Assuming schedule_value is minutes for interval
                minutes = int(crew.schedule_value or 60)
                trigger = IntervalTrigger(minutes=minutes)
            elif crew.schedule_type == "cron":
                # Assuming schedule_value is a cron expression
                trigger = CronTrigger.from_crontab(crew.schedule_value)
            elif crew.schedule_type == "once":
                # Assuming schedule_value is an ISO datetime string
                run_at = datetime.fromisoformat(crew.schedule_value)
                if run_at.tzinfo is None:
                    run_at = run_at.replace(tzinfo=timezone.utc)
                trigger = DateTrigger(run_date=run_at)

            if trigger:
                self.scheduler.add_job(
                    self._run_scheduled_crew,
                    trigger,
                    args=[crew.id],
                    id=job_id,
                    replace_existing=True
                )
                logger.info(f"📅 Scheduled crew {crew.id} ({crew.name}) with type {crew.schedule_type}")
        except Exception as e:
            logger.error(f"Error scheduling crew {crew.id}: {str(e)}")

    async def load_all_schedules(self):
        """Load all active schedules from the database on startup."""
        async with async_session() as db:
            result = await db.execute(select(Crew).where(Crew.schedule_type != "none"))
            crews = result.scalars().all()
            for crew in crews:
                self.schedule_crew(crew)

# Singleton instance
scheduler = CrewScheduler()
