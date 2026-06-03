"""Feedback Learning Engine - adjusts user preferences based on feedback history."""


class FeedbackLearner:
    """Simple preference adjustment based on user feedback patterns."""

    ADJUSTMENTS = {
        "salary_too_low": {"field": "min_salary", "factor": 1.1, "trigger_count": 3},
        "location_mismatch": {"field": "city_weight", "factor": 0.7, "trigger_count": 1},
        "skill_mismatch": {"field": "skill_cluster_weight", "factor": 0.8, "trigger_count": 1},
        "not_interested": {"field": "interest_score", "factor": 0.75, "trigger_count": 1},
        "saved": {"field": "interest_score", "factor": 1.1, "trigger_count": 1},
    }

    @classmethod
    def apply(cls, reason: str, action: str) -> dict:
        key = reason if action == "ignored" else action
        adj = cls.ADJUSTMENTS.get(key)
        if adj:
            return {
                "field": adj["field"],
                "old_value": "1.0",
                "new_value": str(adj["factor"]),
                "note": f"基于{action}反馈自动调整",
            }
        return {}
