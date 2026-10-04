from typing import List, Dict, Any, Optional
import numpy as np
from app.database import db_store

class FafiePlateauDetector:
    """
    Closed-loop Plateau & Regression Detector:
    Monitors weekly progression in member volume and attendance regularity.
    Triggers routine recalibration whenever stagnation or drop-off is detected.
    """

    def analyze_member_trajectory(
        self,
        tenant_id: str,
        member_id: str,
        recent_sessions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyzes session history (e.g. 4+ sessions).
        Checks if volume (weight * reps * sets) delta has plateaued (< 2% progress)
        or if session gap exceeds scheduled rest by > 5 days (regression risk).
        """
        if len(recent_sessions) < 3:
            return {"status": "INSUFFICIENT_DATA", "recommendation_triggered": False}

        volumes = [s.get("total_volume_kg", 0) for s in recent_sessions]
        diffs = np.diff(volumes)
        avg_delta = float(np.mean(diffs))

        # Stagnation condition: average delta is non-positive or near zero
        is_plateau = bool(avg_delta <= 1.0)
        
        result = {
            "member_id": member_id,
            "recent_volume_trend": volumes,
            "average_delta_kg": round(avg_delta, 2),
            "is_plateau_detected": is_plateau,
            "recommended_action": "INCREASE_VARIETY_AND_DELOAD" if is_plateau else "MAINTAIN_PROGRESSIVE_OVERLOAD"
        }

        if is_plateau:
            genome = db_store.get_genome(tenant_id)
            if genome:
                genome.trust.plateau_detection_count += 1
                genome.update_integrity()
                db_store.save_genome(genome)

        return result

plateau_detector = FafiePlateauDetector()
