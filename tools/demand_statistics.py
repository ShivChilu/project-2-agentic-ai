"""Demand Statistics Tool.

Calculates book demand using synthetic circulation history according to:
    Demand Score = (Checkout Score * 0.70) + (Reservation Score * 0.30)
where:
    Checkout Score = (Checkouts / MAX_CHECKOUTS) * 100
    Reservation Score = (Reservations / MAX_RESERVATIONS) * 100
Reference constants:
    MAX_CHECKOUTS = 100
    MAX_RESERVATIONS = 30
Classification thresholds:
    HIGH: 70.0 - 100.0
    MEDIUM: 40.0 - 69.99
    LOW: 0.0 - 39.99
"""

from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd

MAX_CHECKOUTS: int = 100
MAX_RESERVATIONS: int = 30


def calculate_demand_score(checkouts: int, reservations: int) -> float:
    """Calculate normalized demand score between 0 and 100."""
    norm_checkouts = min(max(checkouts, 0) / MAX_CHECKOUTS, 1.0) * 100.0
    norm_reservations = min(max(reservations, 0) / MAX_RESERVATIONS, 1.0) * 100.0
    
    score = (norm_checkouts * 0.70) + (norm_reservations * 0.30)
    return round(score, 2)


def classify_demand(score: float) -> str:
    """Classify demand score into HIGH, MEDIUM, or LOW."""
    if score >= 70.0:
        return "HIGH"
    elif score >= 40.0:
        return "MEDIUM"
    else:
        return "LOW"


def lookup_circulation_history(
    title: str,
    category: Optional[str] = None,
    csv_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Lookup circulation history record for a book title or category.
    
    Returns structured circulation data or None if not found.
    """
    if csv_path is None:
        csv_path = str(Path(__file__).resolve().parent.parent / "data" / "circulation_history.csv")
    
    path = Path(csv_path)
    if not path.exists():
        return None
    
    df = pd.read_csv(path)
    clean_title = title.strip().lower()
    
    # 1. Exact or substring match in book_title
    for _, row in df.iterrows():
        row_title = str(row["book_title"]).strip().lower()
        if row_title == clean_title or row_title in clean_title or clean_title in row_title:
            checkouts = int(row["checkouts"])
            reservations = int(row["reservations"])
            score = calculate_demand_score(checkouts, reservations)
            level = classify_demand(score)
            return {
                "found": True,
                "book_title": str(row["book_title"]),
                "category": str(row["category"]),
                "checkouts": checkouts,
                "reservations": reservations,
                "demand_score": score,
                "demand_level": level,
                "time_period": str(row.get("time_period", "2025-2026")),
                "evidence_notes": str(row.get("historical_demand_notes", ""))
            }

    # If title is not found in historical circulation records, return None
    return None
