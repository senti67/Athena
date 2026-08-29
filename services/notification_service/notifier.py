"""
ATHENA Notification & Incident Alerting Service
Dispatches risk alerts, kill switch notices, and trade fill notifications.
"""

from datetime import datetime
from typing import Dict, List, Optional
from packages.logging.logger import get_logger

logger = get_logger("athena.notifications")


class NotificationService:
    """Dispatches alerts across logging, webhooks, and streaming channels."""

    def __init__(self):
        self.notification_history: List[Dict[str, str]] = []

    def send_alert(self, level: str, title: str, message: str, metadata: Optional[dict] = None):
        alert_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "title": title,
            "message": message,
            "metadata": str(metadata or {}),
        }
        self.notification_history.append(alert_record)
        if len(self.notification_history) > 100:
            self.notification_history.pop(0)

        if level in ("CRITICAL", "ERROR"):
            logger.critical(f"[{title}] {message}")
        else:
            logger.info(f"[{title}] {message}")

    def get_recent_alerts(self, limit: int = 20) -> List[Dict[str, str]]:
        return self.notification_history[-limit:]


notification_service = NotificationService()
