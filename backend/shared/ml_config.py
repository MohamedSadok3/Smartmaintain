"""Configuration partagée du contrat temporel des modèles ML."""

WINDOW_SIZES = {
    "pompe": 20,
    "compresseur": 30,
    "echangeur": 30,
}

SUPPORTED_INPUT_TYPES = {
    "moteur": ["features"],
    "pompe": ["features", "series_complete_skab"],
    "compresseur": ["features", "series"],
    "echangeur": ["features", "series"],
}
