#!/usr/bin/env python3
"""Compute pmo-li-v1 derived values only. No network or evidence inference."""
import argparse
import json

POLICY = "pmo-li-v1"

def score(likelihood, impact):
    for name, value in (("likelihood", likelihood), ("impact", impact)):
        if value is not None and (type(value) is not int or not 1 <= value <= 5):
            raise ValueError(f"{name} must be an integer 1..5 or null")
    escalation = impact == 5
    if likelihood is None or impact is None:
        return dict(policy=POLICY, score=None, priority="Unassessed",
                    rag=None, severity_escalation=escalation)
    product = likelihood * impact
    band, rag = next((b, c) for end, b, c in (
        (3, "Negligible", "green"), (7, "Low", "amber"),
        (11, "Moderate", "amber"), (19, "High", "red"),
        (25, "Critical", "red")) if product <= end)
    return dict(policy=POLICY, score=product, priority=band,
                rag=rag, severity_escalation=escalation)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("likelihood", help="1..5 or unknown")
    p.add_argument("impact", help="1..5 or unknown")
    a = p.parse_args()
    def parse(x):
        return None if x.lower() in {"unknown", "null"} else int(x)
    try:
        print(json.dumps(score(parse(a.likelihood), parse(a.impact)), indent=2))
    except ValueError as e:
        p.error(str(e))
