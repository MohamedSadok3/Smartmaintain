"""Application service for model inference and Redis streaming."""

import json
import logging
from datetime import datetime, timezone

import redis

from shared.config import get_env
from shared.constants import MACHINE_TYPES, REDIS_DEFAULT_URL, REDIS_ML_PREDICTIONS_CHANNEL, REDIS_SENSOR_CHANNEL
from engines.unified_engine import MLEngine
from model_service import ModelServiceError

logger = logging.getLogger(__name__)


class MLService:
    """Expose model inference with V7 models."""

    def __init__(self, engine=None, redis_client=None):
        self.redis_client = redis_client or redis.from_url(
            get_env("REDIS_URL", REDIS_DEFAULT_URL), decode_responses=True
        )
        
        self.engine = engine or MLEngine()
        self.supported_models = MACHINE_TYPES

    @staticmethod
    def _build_prediction_payload(machine, prediction, timestamp=None, plant_id=None, sensors=None, source_type=None):
        payload = {
            "machine": machine,
            "equipment_type": prediction.get("equipment_type", machine),
            "defect": prediction["defect"],
            "predicted_class": prediction.get("predicted_class", prediction["defect"]),
            "defect_score": prediction["defect_score"],
            "anomaly_score": prediction["defect_score"],
            "defect_scores": prediction.get("defect_scores", {}),
            "probabilities": prediction.get("probabilities", prediction.get("defect_scores", {})),
            "confidence": prediction["confidence"],
            "status": prediction.get("status"),
            "recommendation": prediction.get("recommendation"),
            "recommendation_status": prediction.get("recommendation_status"),
            "model_version": prediction.get("model_version", "v7"),
            "model_release": prediction.get("model_release"),
            "estimator_type": prediction.get("estimator_type"),
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        }
        if source_type:
            payload["source_type"] = source_type
        if sensors:
            payload["sensors"] = sensors
        if plant_id is not None:
            payload["plant_id"] = plant_id
        return payload

    def predict_for_machine(self, machine, model_input, plant_id=None, component_id=None):
        del component_id  # Retained in the HTTP contract; predictions are no longer persisted.
        if machine not in self.supported_models:
            return {"error": "unknown_equipment", "equipment_type": machine}, 422
        
        try:
            prediction = self.engine.predict(machine, model_input)
            return self._build_prediction_payload(
                machine, prediction, 
                plant_id=plant_id, 
                sensors=model_input
            ), 200
        except ModelServiceError as exc:
            return exc.to_dict(), exc.status_code
        except Exception as exc:
            logger.exception("Prediction failed for '%s'", machine)
            return {"error": "prediction_error", "message": str(exc)}, 500

    def get_status(self):
        """Get status of ML models."""
        status = self.engine.get_status()
        status["supported_models"] = self.supported_models
        return status

    def consume_sensor_data(self):
        """Consume sensor data from Redis and publish predictions."""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(REDIS_SENSOR_CHANNEL)
        for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            try:
                source = json.loads(message.get("data", "{}"))
                machine = source.get("machine")
                if machine not in self.supported_models:
                    continue
                
                model_input = source.get("sensors", {})
                prediction = self.engine.predict(machine, model_input)
                output = self._build_prediction_payload(
                    machine,
                    prediction,
                    timestamp=source.get("timestamp"),
                    plant_id=source.get("plant_id"),
                    sensors=source.get("display_sensors") or model_input,
                    source_type=source.get("source_type")
                )
                self.redis_client.publish(REDIS_ML_PREDICTIONS_CHANNEL, json.dumps(output))
            except ModelServiceError as exc:
                logger.info("Prediction deferred or rejected: %s", exc.to_dict())
                output = {
                    **exc.to_dict(),
                    "machine": locals().get("machine"),
                    "timestamp": locals().get("source", {}).get("timestamp"),
                    "source_type": locals().get("source", {}).get("source_type"),
                    "model_version": "v7",
                }
                self.redis_client.publish(REDIS_ML_PREDICTIONS_CHANNEL, json.dumps(output))
            except Exception:
                logger.exception("Unexpected error while consuming sensor data")
