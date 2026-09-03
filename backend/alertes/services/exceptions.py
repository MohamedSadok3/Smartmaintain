class AlertNotFoundException(Exception):
    """L'alerte demandée n'existe pas."""


class UnauthorizedActionException(Exception):
    """L'utilisateur n'a pas le droit d'effectuer cette action."""


class InvalidStatusTransitionException(Exception):
    """La transition de statut demandée n'est pas valide."""


class TechnicianNotEligibleException(Exception):
    """Le technicien n'est pas éligible pour cette alerte."""
