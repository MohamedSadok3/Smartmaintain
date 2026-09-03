import json
import logging
import threading
from datetime import datetime, timedelta, timezone

from flask_socketio import SocketIO

from shared.constants import REDIS_ML_PREDICTIONS_CHANNEL
from .alert_service import AlertService

logger = logging.getLogger(__name__)


class RedisConsumer:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.alert_service = AlertService()
        self.predictions_channel = REDIS_ML_PREDICTIONS_CHANNEL
        self.consumer_thread = None
        # Cache des dernières alertes par machine pour déduplication
        self.last_alerts = {}  # {machine: {defect: timestamp}}

    def consume_predictions(self):
        """Consume ML predictions from Redis and create alerts."""
        pubsub = self.alert_service.redis_client.pubsub()
        pubsub.subscribe(self.predictions_channel)

        for message in pubsub.listen():
            if message.get("type") != "message":
                continue

            try:
                prediction = json.loads(message.get("data", "{}"))
                defect_scores = prediction.get("defect_scores") or {}
                score = float(prediction.get("defect_score", prediction.get("anomaly_score", 0)))
                defect_name = prediction.get("defect", "anomaly_detected")

                # Never turn confidence in the normal class into an alert.
                if defect_name == "normal_operation":
                    continue
                if isinstance(defect_scores, dict) and defect_scores:
                    abnormal_scores = {
                        name: float(value)
                        for name, value in defect_scores.items()
                        if name != "normal_operation"
                    }
                    if abnormal_scores:
                        defect_name = max(abnormal_scores, key=abnormal_scores.get)

                severity = self.alert_service.severity_from_score(score)

                self.socketio.emit("sensor:data", prediction)

                if not severity:
                    continue

                incoming_plant_id = prediction.get("plant_id")
                if incoming_plant_id is None:
                    logger.warning("Dropped prediction without plant_id")
                    continue
                plant_id = int(incoming_plant_id)

                machine = prediction.get("machine", "unknown")
                
                # Déduplication: ne créer une alerte que si:
                # 1. Nouveau défaut différent du précédent sur cette machine
                # 2. OU dernier défaut similaire il y a plus de 5 minutes (cooldown)
                now = datetime.now(timezone.utc)
                should_create_alert = True
                
                if machine in self.last_alerts:
                    last_defect_time = self.last_alerts[machine].get(defect_name)
                    if last_defect_time:
                        time_since_last = (now - last_defect_time).total_seconds()
                        # Cooldown de 5 minutes (300 secondes) entre alertes identiques
                        if time_since_last < 300:
                            should_create_alert = False
                            logger.debug(f"Alerte dédupliquée: {machine}/{defect_name} (dernière il y a {time_since_last:.0f}s)")
                
                if should_create_alert:
                    alert = self.alert_service.insert_alert(
                        plant_id=plant_id,
                        machine=machine,
                        defect=defect_name,
                        defect_score=score,
                        confidence=float(prediction.get("confidence", 0)),
                        severity=severity,
                    )
                    
                    # Mettre à jour le cache de déduplication
                    if machine not in self.last_alerts:
                        self.last_alerts[machine] = {}
                    self.last_alerts[machine][defect_name] = now
                    
                    self.socketio.emit("alert:new", alert.to_dict())
                    logger.info(f"Nouvelle alerte créée: {machine}/{defect_name} (sévérité: {severity})")

            except Exception:
                logger.exception("Error processing prediction")
                continue

    def start_consumer_thread(self):
        """Start the Redis consumer thread."""
        self.consumer_thread = threading.Thread(target=self.consume_predictions, daemon=True)
        self.consumer_thread.start()
