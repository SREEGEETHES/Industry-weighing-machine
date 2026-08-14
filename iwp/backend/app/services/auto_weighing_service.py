"""
Automatic weighing service - continuously monitors scale and auto-triggers
weigh+print when a box is detected (no button press needed).

This runs as a background thread for each enabled station.
"""
import time
import threading
import logging
from typing import Dict
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Station
from app.drivers.registry import build_scale_driver
from app.drivers.base import DriverConnectionError, DriverReadTimeoutError
from app.services.weighing_service import perform_weigh_and_print
from app.config import STABILITY_SAMPLE_COUNT, STABILITY_TOLERANCE_KG, STABILITY_POLL_INTERVAL_SEC

logger = logging.getLogger("iwpas.auto_weighing")

# Global registry of running monitor threads
_monitors: Dict[int, 'StationMonitor'] = {}


class StationMonitor:
    """Continuously monitors a scale and auto-triggers weigh+print when box detected."""
    
    def __init__(self, station_id: int):
        self.station_id = station_id
        self.running = False
        self.thread = None
        self._last_weight = 0.0
        self._zero_threshold = 0.5  # kg - anything below this is "empty scale"
        
    def start(self):
        """Start monitoring thread."""
        if self.running:
            logger.warning(f"Monitor for station {self.station_id} already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started auto-monitor for station {self.station_id}")
    
    def stop(self):
        """Stop monitoring thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"Stopped auto-monitor for station {self.station_id}")
    
    def _monitor_loop(self):
        """Main monitoring loop - runs continuously."""
        db = SessionLocal()
        consecutive_empty_readings = 0
        
        try:
            while self.running:
                try:
                    station = db.get(Station, self.station_id)
                    if not station or not station.is_enabled:
                        time.sleep(5)
                        continue
                    
                    if not station.scale:
                        time.sleep(5)
                        continue
                    
                    # Build scale driver and connect
                    scale_driver = build_scale_driver(station.scale)
                    scale_driver.connect()
                    
                    try:
                        # Read current weight
                        reading = scale_driver.read_weight()
                        current_weight = reading.value
                        
                        # Detect box placement: weight goes from ~0 to >threshold
                        if self._last_weight < self._zero_threshold and current_weight >= self._zero_threshold:
                            logger.info(f"Station {self.station_id}: Box detected ({current_weight} kg)")
                            
                            # Wait for weight to stabilize
                            time.sleep(1.5)  # Give it time to settle
                            
                            # Check if weight is still there (not a transient spike)
                            check_reading = scale_driver.read_weight()
                            if check_reading.value >= self._zero_threshold:
                                logger.info(f"Station {self.station_id}: Weight stable, auto-triggering weigh+print")
                                scale_driver.disconnect()
                                
                                # Trigger full weigh+print cycle
                                try:
                                    result = perform_weigh_and_print(db, station)
                                    logger.info(f"Station {self.station_id}: {result.box_id} - {result.weight} {result.unit} - {result.print_status}")
                                except Exception as e:
                                    logger.error(f"Station {self.station_id}: Auto-weigh failed: {e}")
                                
                                # Wait for box to be removed before monitoring again
                                time.sleep(3)
                                self._last_weight = 0.0
                                consecutive_empty_readings = 0
                                continue
                        
                        # Track empty scale state
                        if current_weight < self._zero_threshold:
                            consecutive_empty_readings += 1
                            if consecutive_empty_readings >= 3:
                                self._last_weight = 0.0
                        else:
                            consecutive_empty_readings = 0
                            self._last_weight = current_weight
                        
                    finally:
                        scale_driver.disconnect()
                    
                    # Poll every 0.5 seconds
                    time.sleep(0.5)
                    
                except (DriverConnectionError, DriverReadTimeoutError) as e:
                    logger.debug(f"Station {self.station_id}: Scale connection issue: {e}")
                    time.sleep(5)  # Wait longer on connection errors
                    
                except Exception as e:
                    logger.error(f"Station {self.station_id}: Monitor error: {e}", exc_info=True)
                    time.sleep(5)
        
        finally:
            db.close()


def start_auto_monitoring(station_id: int):
    """Start automatic monitoring for a station."""
    if station_id in _monitors:
        logger.warning(f"Monitor for station {station_id} already exists")
        return
    
    monitor = StationMonitor(station_id)
    monitor.start()
    _monitors[station_id] = monitor


def stop_auto_monitoring(station_id: int):
    """Stop automatic monitoring for a station."""
    if station_id not in _monitors:
        return
    
    monitor = _monitors.pop(station_id)
    monitor.stop()


def stop_all_monitors():
    """Stop all monitoring threads (called on shutdown)."""
    logger.info("Stopping all auto-monitoring threads")
    for station_id in list(_monitors.keys()):
        stop_auto_monitoring(station_id)


def start_all_enabled_stations():
    """Start auto-monitoring for all enabled stations on app startup."""
    db = SessionLocal()
    try:
        stations = db.query(Station).filter(Station.is_enabled == True).all()
        for station in stations:
            if station.scale and station.printer:
                logger.info(f"Starting auto-monitor for station {station.id} ({station.name})")
                start_auto_monitoring(station.id)
    finally:
        db.close()
