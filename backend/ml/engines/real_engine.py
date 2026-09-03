"""Compatibility adapter over the central ModelService."""
import sys
from pathlib import Path

SERVICES_DIR = Path(__file__).resolve().parents[1] / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))
from model_service import ModelService


class RealMLEngine:
    def __init__(self, model_service=None, models_dir=None):
        self.model_service = model_service or ModelService(models_dir=models_dir)
        self.models = {name: bundle.model for name, bundle in self.model_service.bundles.items()}
        self.metadata = {name: bundle.metadata for name, bundle in self.model_service.bundles.items()}

    def predict(self, machine, sensors):
        if isinstance(sensors, dict) and "features" in sensors:
            return self.model_service.predict(machine, features=sensors["features"])
        if isinstance(sensors, dict) and "series" in sensors:
            return self.model_service.predict(machine, series=sensors["series"])
        bundle = self.model_service.get_bundle(machine)
        if isinstance(sensors, dict) and all(name in sensors for name in bundle.feature_names):
            return self.model_service.predict(machine, features=sensors)
        return self.model_service.predict(machine, series=sensors)
