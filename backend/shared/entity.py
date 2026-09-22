
from datetime import date, datetime
from typing import Any, Optional


def mapping_from_row(row) -> Optional[dict]:
    if row is None:
        return None
    return dict(row)


def isoformat_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value
