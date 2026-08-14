import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.services.report_service import generate_weekly_report
from app.services.email_service import send_weekly_report_email, EmailSendError

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/run-now")
def run_report_now(db: Session = Depends(get_db)):
    """Manually trigger a report for the last 7 days and email it - useful
    for testing the whole pipeline before relying on the weekly schedule."""
    period_end = dt.datetime.utcnow()
    period_start = period_end - dt.timedelta(days=7)

    filepath = generate_weekly_report(db, period_start, period_end)

    recipients = [
        r.email for r in db.query(models.EmailRecipient).filter_by(is_active=True).all()
    ]

    records_count = (
        db.query(models.BoxRecord)
        .filter(models.BoxRecord.created_at >= period_start, models.BoxRecord.created_at < period_end)
        .count()
    )

    log = models.ReportLog(
        period_start=period_start,
        period_end=period_end,
        recipients=", ".join(recipients),
        box_count=records_count,
        file_path=filepath,
    )

    try:
        send_weekly_report_email(
            recipients=recipients,
            filepath=filepath,
            period_start_str=period_start.strftime("%d/%m/%Y"),
            period_end_str=period_end.strftime("%d/%m/%Y"),
            summary_lines=[f"Total boxes this period: {records_count}"],
        )
        log.status = "sent"
    except EmailSendError as e:
        log.status = "failed"
        log.error_message = str(e)
        db.add(log)
        db.commit()
        raise HTTPException(500, str(e))

    db.add(log)
    db.commit()
    return {"status": "sent", "file": filepath, "recipients": recipients, "box_count": records_count}


@router.get("/logs")
def list_report_logs(db: Session = Depends(get_db)):
    logs = db.query(models.ReportLog).order_by(models.ReportLog.sent_at.desc()).all()
    return [
        {
            "id": l.id,
            "period_start": l.period_start,
            "period_end": l.period_end,
            "recipients": l.recipients,
            "box_count": l.box_count,
            "sent_at": l.sent_at,
            "status": l.status,
            "error_message": l.error_message,
        }
        for l in logs
    ]


@router.get("/download/{log_id}")
def download_report(log_id: int, db: Session = Depends(get_db)):
    log = db.get(models.ReportLog, log_id)
    if not log or not log.file_path:
        raise HTTPException(404, "Report not found.")
    return FileResponse(log.file_path, filename=log.file_path.split("/")[-1])
