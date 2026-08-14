"""
Central configuration. All values are read from environment variables so the
same code runs unchanged on whatever machine the factory ends up using.
Copy .env.example to .env and fill in real values before starting the app.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Database -----------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/iwpas.db")

# --- SMTP / weekly email -------------------------------------------------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # Gmail: use an App Password, not your login password
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "IWPAS Reporting")

# --- Weekly report schedule ----------------------------------------------
REPORT_DAY_OF_WEEK = os.getenv("REPORT_DAY_OF_WEEK", "mon")  # mon/tue/.../sun
REPORT_HOUR = int(os.getenv("REPORT_HOUR", "7"))
REPORT_MINUTE = int(os.getenv("REPORT_MINUTE", "0"))

# --- Box ID format ---------------------------------------------------------
BOX_ID_PREFIX = os.getenv("BOX_ID_PREFIX", "BOX")

# --- Weighing engine -------------------------------------------------------
# How many consecutive identical (within STABILITY_TOLERANCE_KG) readings
# before a weight is accepted as "stable" and sent to print. Prevents
# printing a box mid-placement while the reading is still bouncing.
STABILITY_SAMPLE_COUNT = int(os.getenv("STABILITY_SAMPLE_COUNT", "5"))
STABILITY_TOLERANCE_KG = float(os.getenv("STABILITY_TOLERANCE_KG", "0.010"))
STABILITY_POLL_INTERVAL_SEC = float(os.getenv("STABILITY_POLL_INTERVAL_SEC", "0.2"))
