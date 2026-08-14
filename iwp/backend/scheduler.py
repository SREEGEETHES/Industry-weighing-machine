"""
Background scheduler that fires the weekly report + email automatically,
on the day/time configured in .env (REPORT_DAY_OF_WEEK / REPORT_HOUR /
REPORT_MINUTE). Runs inside the same FastAPI process - no separate cron
needed, but you can swap this for OS-level cron/Task Scheduler if you
prefer the report generation to survive independently of the API process.
"""
import datetime as dt
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app import models
from app.config import REPORT_DAY_OF_WEEK, REPORT_HOUR, REPORT_MINUTE
from app.services.report_service import generate_weekly_report
from app.services.email_service import send_weekly_report_email, EmailSendError

logger = logging.getLogger("iwpas.scheduler")


def run_weekly_report_job():
    db = SessionLocal()
    try:
        period_end = dt.datetime.utcnow()
        period_start = period_end - dt.timedelta(days=7)

        filepath = generate_weekly_report(db, period_start, period_end)
        recipients = [r.email for r in db.query(models.EmailRecipient).filter_by(is_active=True).all()]
        records_count = (
            db.query(models.BoxRecord)
            .filter(models.BoxRecord.created_at >= period_start, models.BoxRecord.created_at < period_end)
            .count()
        )

        log = models.ReportLog(
            period_start=period_start, period_end=period_end,
            recipients=", ".join(recipients), box_count=records_count, file_path=filepath,
        )
        try:
            send_weekly_report_email(
                recipients=recipients, filepath=filepath,
                period_start_str=period_start.strftime("%d/%m/%Y"),
                period_end_str=period_end.strftime("%d/%m/%Y"),
                summary_lines=[f"Total boxes this period: {records_count}"],
            )
            log.status = "sent"
            logger.info("Weekly report sent to %s", recipients)
        except EmailSendError as e:
            log.status = "failed"
            log.error_message = str(e)
            logger.error("Weekly report email failed: %s", e)

        db.add(log)
        db.commit()
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_weekly_report_job,
        trigger=CronTrigger(day_of_week=REPORT_DAY_OF_WEEK, hour=REPORT_HOUR, minute=REPORT_MINUTE),
        id="weekly_report",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Weekly report scheduled for %s at %02d:%02d UTC",
        REPORT_DAY_OF_WEEK, REPORT_HOUR, REPORT_MINUTE,
    )
    return scheduler
