import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import stations, presets, recipients, lookup, records, reports, auth

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they don't exist yet.
    Base.metadata.create_all(bind=engine)

    # Start auto-monitoring for all enabled stations
    from app.services.auto_weighing_service import start_all_enabled_stations, stop_all_monitors
    start_all_enabled_stations()

    # Start the weekly report scheduler in the background.
    from scheduler import start_scheduler
    scheduler = start_scheduler()

    yield

    # Shutdown: stop monitors and scheduler
    stop_all_monitors()
    scheduler.shutdown()


app = FastAPI(
    title="Trade Kings Weigh-Print-Audit System",
    description="Ties a digital scale and inkjet printer together with a full audit trail.",
    version="1.0.0",
    lifespan=lifespan,
)

# Admin panel and lookup webapp are separate static front ends calling this
# API from the browser - CORS is open here for factory-LAN use. Restrict
# allow_origins to your actual admin/lookup app URLs once deployed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(stations.router)
app.include_router(presets.router)
app.include_router(recipients.router)
app.include_router(lookup.router)
app.include_router(records.router)
app.include_router(reports.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
