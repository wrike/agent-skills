#!/usr/bin/env python3
"""Compile Wrike recommendation JSON into deterministic Klaxoon item batches.

This standalone program uses only the Python standard library. It performs no network
access and owns no credentials; the calling agent handles MCP calls and recovery.
"""

from __future__ import annotations

import argparse
import ast
import html
import json
import math
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional


COLORS = {
    "panel": "#e5f2ff", "blue": "#416dd1", "blue_fill": "#d6e6ff",
    "white": "#ffffff", "green_fill": "#d9fad2", "green": "#41ab37",
    "orange_fill": "#fbe3c2", "orange_widget": "#ffefd5", "orange": "#e8850c",
    "red_fill": "#ffe1e2", "red": "#f76673", "red_text": "#e5484d",
    "track": "#cae2ff", "committed": "#5c5c5c", "proposal": "#8db7fc",
    "over": "#ff99a2", "primary": "#0d0d0d", "black": "#000000", "secondary": "#545454",
    "muted": "#bbbbbb",
}
ALLOWED_COLORS = set(COLORS.values())
WR_ID = re.compile(r"^w:(?:itm|usr|cp):([^\s]+)$")


def assert_standard_library_imports() -> None:
    """Fail the self-test if the compiler gains a non-stdlib dependency."""
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    relative: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                relative.append(node.module or "<relative>")
            elif node.module:
                imported.add(node.module.split(".", 1)[0])

    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    if not stdlib:
        stdlib = {
            "argparse", "ast", "collections", "html", "json", "math", "pathlib",
            "re", "sys", "tempfile", "typing",
        }
    third_party = sorted(imported - stdlib - {"__future__"})
    assert not relative, f"Relative imports are not allowed: {relative}"
    assert not third_party, f"Non-standard-library imports found: {third_party}"


def rnd(value: float) -> int:
    return int(math.floor(value + 0.5))


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def symbol_codes(value: str) -> str:
    """Use Klaxoon-safe numeric entities for the skill's canonical symbols."""
    replacements = {
        "✅": "&#x2705;", "❌": "&#x274C;",
        "🟥": "&#x1F7E5;", "🟨": "&#x1F7E8;", "⚠️": "&#x26A0;&#xFE0F;",
        "⛔": "&#x26D4;", "▮": "&#x25AE;", "┃": "&#x2503;",
    }
    for symbol, code in replacements.items():
        value = value.replace(symbol, code)
    return value


def safe_wrike_url(value: Any) -> str:
    """Return an escaped HTTPS Wrike URL, or an empty string for unsafe input."""
    raw = str(value or "").strip()
    if not re.match(r"^https://(?:[a-z0-9-]+\.)*wrike\.com(?:/|$)", raw, re.IGNORECASE):
        return ""
    return esc(raw)


def amount(value: Any, time_unit: str) -> float:
    try:
        raw = float(value or 0)
        return round(raw / 60.0 if time_unit == "MINUTES" else raw, 1)
    except (TypeError, ValueError):
        return 0.0


def fh(value: float) -> str:
    return f"{value:.1f}"


def unit_label(time_unit: str) -> str:
    return "h" if time_unit == "MINUTES" else time_unit.lower()


def amount_text(value: float, label: str) -> str:
    separator = "" if label == "h" else " "
    return f"{fh(value)}{separator}{label}"


def unassigned_explanation(flags: Any) -> tuple[str, str]:
    values = {str(flag) for flag in (flags or [])}
    if "NO_MATCH_REQUIREMENTS" in values:
        return "no one meets the requirements", "requirements"
    if "NO_MATCH_AVAILABILITY" in values:
        return "no one has availability", "availability"
    return "no suitable assignee was found", "unknown"


def overload_explanation(reason: Any) -> str:
    if reason == "PROPOSAL":
        return "caused by this recommendation"
    if reason == "EXISTING":
        return "already present before this recommendation"
    return ""


def truncate_words(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    prefix = text[:limit]
    cut = prefix.rfind(" ")
    if cut > 0:
        prefix = prefix[:cut]
    return prefix.rstrip() + "…"


def value_text(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(value_text(v) for v in value)
    if isinstance(value, dict):
        return " · ".join(f"{k} {value_text(v)}" for k, v in value.items())
    return str(value)


def attr_parts(row: dict[str, Any], names: dict[str, str]) -> tuple[str, str]:
    field = ""
    if row.get("id"):
        field = names.get(str(row["id"]), "")
    elif row.get("kind"):
        kind = str(row["kind"])
        field = "Job role" if kind == "jobRole" else re.sub(r"(?<!^)([A-Z])", r" \1", kind).capitalize()
    value = value_text(row.get("value", ""))
    plain = f"{field}: {value}" if field else value
    rich = f"<strong>{esc(field)}:</strong> {esc(value)}" if field else esc(value)
    return plain, rich


def unwrap(value: Any) -> Any:
    current = value
    for _ in range(5):
        if not isinstance(current, dict):
            return current
        for key in ("structuredContent", "data", "result"):
            candidate = current.get(key)
            if isinstance(candidate, dict) and (
                "solutions" in candidate or "recommendations" in candidate or "users" in candidate
            ):
                current = candidate
                break
        else:
            return current
    return current


def extract_runs(raw_entries: list[Any]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for raw in raw_entries:
        obj = unwrap(raw)
        if not isinstance(obj, dict):
            continue
        if isinstance(obj.get("solutions"), list):
            runs.append(obj)
            continue
        nested = obj.get("recommendations")
        if isinstance(nested, list):
            for entry in nested:
                entry = unwrap(entry)
                if isinstance(entry, dict) and isinstance(entry.get("solutions"), list):
                    runs.append(entry)
    return runs


def extract_users(raw_entries: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in raw_entries:
        obj = unwrap(raw)
        if isinstance(obj, dict) and isinstance(obj.get("users"), list):
            rows.extend(x for x in obj["users"] if isinstance(x, dict))
        elif isinstance(obj, dict) and obj.get("id"):
            rows.append(obj)
    return rows


def shape(x: float, y: float, z: int, width: float, height: float, fill: str,
          stroke: Optional[str] = None, thickness: float = 2,
          content: Optional[str] = None, font_size: Optional[int] = None) -> dict[str, Any]:
    data: dict[str, Any] = {
        "shapeType": "rectangle",
        "style": {"fillColor": fill, "strokeColor": stroke or fill, "strokeThickness": thickness},
    }
    if content is not None:
        data["content"] = content
    if font_size is not None:
        data["fontSize"] = font_size
    return {"type": "SHAPE", "payload": {
        "position": {"x": rnd(x), "y": rnd(y), "z": z},
        "geometry": {"width": rnd(width), "height": rnd(height)}, "data": data}}


def text_item(x: float, y: float, content: str, size: int, width: float, z: int = 4) -> dict[str, Any]:
    return {"type": "TEXT", "payload": {
        "position": {"x": rnd(x), "y": rnd(y), "z": z},
        "data": {"content": content, "fontSize": size, "maxLineWidth": rnd(width)}}}


def ptext(text: str, color: str = COLORS["primary"], bold: bool = False,
          italic: bool = False, center: bool = False) -> str:
    body = symbol_codes(esc(text))
    if bold:
        body = f"<strong>{body}</strong>"
    if italic:
        body = f"<em>{body}</em>"
    out = f'<p><span style="color: {color}">{body}</span></p>'
    return f'<div style="text-align: center">{out}</div>' if center else out


def display_name(row: dict[str, Any]) -> str:
    name = str(row.get("name") or "").strip()
    if name:
        return name
    full_name = " ".join(str(row.get(k, "")).strip() for k in ("firstName", "lastName")).strip()
    return full_name


def display_role(row: dict[str, Any]) -> str:
    # Wrike's generic `role` is an account permission level (for example,
    # "User"), not the person's job title. Never render it on an assignee card.
    for key in ("jobTitle", "jobRole"):
        if row.get(key):
            return str(row[key])
    if row.get("title") and (row.get("name") or row.get("firstName") or row.get("lastName")):
        return str(row["title"])
    return ""


def normalize_input(data: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    errors: list[str] = []
    runs = extract_runs(data.get("recommendations", []))
    if not runs:
        errors.append("No recommend_resources run with solutions was found under recommendations.")

    user_rows = extract_users(data.get("users", []))
    users: dict[str, dict[str, str]] = {}
    names = {str(k): str(v) for k, v in (data.get("attributeNames") or {}).items()}
    for row in user_rows:
        uid = str(row.get("id", ""))
        if uid:
            users[uid] = {"name": display_name(row), "role": display_role(row)}
        for cf in row.get("customFields", []) or []:
            if isinstance(cf, dict) and cf.get("id") and cf.get("name"):
                names[str(cf["id"])] = str(cf["name"])

    scenarios: list[dict[str, Any]] = []
    labels = list(data.get("parameterLabels") or [])
    label_index = 0
    display_units: set[str] = set()
    referenced_user_ids: set[str] = set()
    for run_index, run in enumerate(runs):
        unit = str(run.get("timeUnit", "")).strip().upper()
        if not unit:
            errors.append(f"Recommendation run {run_index + 1} has no timeUnit.")
            continue
        display_units.add("HOURS" if unit == "MINUTES" else unit)
        period = run.get("affectedPeriod") or {}
        metadata = run.get("solutionsMetadata") or {}
        task_rows = ((metadata.get("tasks") or {}).get("tasks") or [])
        resource_rows = ((metadata.get("resources") or {}).get("resources") or [])
        task_names = {str(x.get("id")): str(x.get("name") or x.get("title") or x.get("id"))
                      for x in task_rows if isinstance(x, dict) and x.get("id")}
        fallback_users = {str(x.get("id")): str(x.get("name") or x.get("id"))
                          for x in resource_rows if isinstance(x, dict) and x.get("id")}
        sols = sorted((x for x in run.get("solutions", []) if isinstance(x, dict)),
                      key=lambda x: x.get("index", 0))
        for sol in sols:
            referenced_user_ids.update(
                str(row.get("responsibleId")) for row in (sol.get("assignments") or [])
                if isinstance(row, dict) and row.get("responsibleId")
            )
            referenced_user_ids.update(str(uid) for uid in (sol.get("resourceWorkloads") or {}))
            scenario = normalize_scenario(sol, period, task_names, fallback_users, users, names,
                                          str(run.get("effortEstimationPrecision") or "DAYS"), unit)
            scenario["runIndex"] = run_index
            raw_label = labels[label_index] if label_index < len(labels) else ""
            scenario["label"] = str(raw_label).strip() if raw_label is not None else ""
            scenarios.append(scenario)
            label_index += 1

    if len(display_units) > 1:
        errors.append("Recommendation runs use incompatible timeUnit values; compared options must use one compatible unit.")
    missing_user_rows = sorted(referenced_user_ids - set(users))
    if missing_user_rows:
        errors.append(
            "Compiler input is missing get_users rows for referenced assignees: "
            + ", ".join(missing_user_rows)
            + ". Reuse the saved get_users result under users; call get_users again only if that result was incomplete."
        )
    invalid_user_names = sorted(
        uid for uid in (referenced_user_ids & set(users))
        if not users[uid]["name"] or users[uid]["name"] == uid
        or re.fullmatch(r"w:usr:\S+", users[uid]["name"])
    )
    if invalid_user_names:
        errors.append(
            "Compiler user rows have an invalid display name for referenced assignees: "
            + ", ".join(invalid_user_names)
            + ". Reparse the saved get_users result; names cannot be blank or a Wrike user id."
        )
    if not scenarios:
        errors.append("No eligible items were found to staff.")
    return scenarios, {"errors": errors, "attributeNames": names, "users": users}


def normalize_scenario(sol: dict[str, Any], period: dict[str, Any], task_names: dict[str, str],
                       fallback_users: dict[str, str], users: dict[str, dict[str, str]],
                       names: dict[str, str], precision: str, time_unit: str) -> dict[str, Any]:
    def resolved_name(uid: str) -> str:
        # A present get_users row is authoritative. Recommendation metadata is
        # only a fallback when that row is genuinely absent.
        return users[uid]["name"] if uid in users else fallback_users.get(uid, uid)

    assignments: list[dict[str, Any]] = []
    all_titles = dict(task_names)
    for row in sol.get("assignments", []) or []:
        if not isinstance(row, dict):
            continue
        tid, uid = str(row.get("taskId", "")), str(row.get("responsibleId", ""))
        if not tid or not uid:
            continue
        reason = row.get("reasoning") or {}
        percent = reason.get("matchPercent")
        if percent is None:
            category, fit = "no_requirements", None
        else:
            try:
                fit = int(round(float(percent)))
            except (TypeError, ValueError):
                fit = 0
            category = "full" if fit == 100 else "partial" if fit > 0 else "zero"
        matched = [attr_parts(x, names) for x in reason.get("matchedAttributes", []) or [] if isinstance(x, dict)]
        missing = [attr_parts(x, names) for x in reason.get("missingAttributes", []) or [] if isinstance(x, dict)]
        assignments.append({
            "taskId": tid, "title": all_titles.get(tid, tid), "userId": uid,
            "name": resolved_name(uid),
            "role": users.get(uid, {}).get("role", ""), "fit": fit, "category": category,
            "matched": matched, "missing": missing,
        })

    unassigned: list[dict[str, Any]] = []
    for row in sol.get("unassignedItems", []) or []:
        if not isinstance(row, dict):
            continue
        tid = str(row.get("taskId", ""))
        reason = row.get("reasoning") or {}
        explanation, reason_kind = unassigned_explanation(reason.get("flags"))
        required = [attr_parts(x, names) for x in reason.get("requiredAttributes", []) or [] if isinstance(x, dict)]
        unassigned.append({"taskId": tid, "title": all_titles.get(tid, tid), "reason": explanation,
                           "reasonKind": reason_kind, "required": required})

    assigned_task_ids = {row["taskId"] for row in assignments}
    for row in unassigned:
        row["partiallyStaffed"] = row["taskId"] in assigned_task_ids

    workloads: dict[str, dict[str, Any]] = {}
    raw_workloads = sol.get("resourceWorkloads") or {}
    for uid, raw in raw_workloads.items():
        raw = raw or {}
        totals = raw.get("periodTotals") or {}
        cap = amount(totals.get("capacity"), time_unit)
        committed = amount(totals.get("outOfScopeAllocation"), time_unit)
        new = amount(totals.get("proposedAllocation"), time_unit)
        projected = amount(totals.get("projectedWorkload"), time_unit)
        positive_overloads = []
        for interval in raw.get("overload", []) if isinstance(raw.get("overload"), list) else []:
            if not isinstance(interval, dict):
                continue
            value = amount(interval.get("amount") or interval.get("overload") or interval.get("value"), time_unit)
            if value <= 0:
                continue
            positive_overloads.append({
                "label": str(interval.get("date") or interval.get("weekStart") or ""),
                "amount": value,
                "explanation": overload_explanation(interval.get("reason")),
            })
        has_overload = bool(positive_overloads)
        over = amount(totals.get("overload"), time_unit) if has_overload else 0.0
        if has_overload and over <= 0:
            over = round(sum(x["amount"] for x in positive_overloads), 1)
        if projected == 0 and (committed or new):
            projected = round(committed + new, 1)
        workloads[str(uid)] = {
            "userId": str(uid), "name": resolved_name(str(uid)),
            "role": users.get(str(uid), {}).get("role", ""), "capacity": cap, "committed": committed,
            "proposed": new, "projected": projected, "overload": over, "hasOverload": has_overload,
            "unitLabel": unit_label(time_unit),
            "pct": rnd(projected / cap * 100) if cap else 0,
            "overloadIntervals": positive_overloads,
        }
    for assignment in assignments:
        uid = assignment["userId"]
        workloads.setdefault(uid, {"userId": uid, "name": assignment["name"], "role": assignment["role"],
                                   "capacity": 0.0, "committed": 0.0, "proposed": 0.0, "projected": 0.0,
                                   "overload": 0.0, "hasOverload": False, "unitLabel": unit_label(time_unit),
                                   "pct": 0, "overloadIntervals": []})

    tasks_by_user: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for assignment in assignments:
        tasks_by_user[assignment["userId"]].append(assignment)
    for uid, person in workloads.items():
        owned = tasks_by_user.get(uid, [])
        person["taskCount"] = len(owned)
        person["hasGap"] = any(x["category"] != "full" for x in owned)
        person["state"] = "red" if person["hasOverload"] else "orange" if person["hasGap"] else "green"

    staffed_ids = {x["taskId"] for x in assignments}
    unassigned_ids = {x["taskId"] for x in unassigned}
    gaps = {x["taskId"] for x in assignments if x["category"] != "full"}
    declared = sol.get("taskCount")
    total = int(declared) if isinstance(declared, (int, float)) else len(staffed_ids | unassigned_ids)
    unassigned_count = len(unassigned_ids)
    staffed = max(0, total - unassigned_count)
    return {
        "period": {"start": str(period.get("start", "")), "end": str(period.get("end", ""))},
        "precision": precision, "timeUnit": time_unit, "unitLabel": unit_label(time_unit),
        "assignments": assignments, "unassigned": unassigned,
        "workloads": workloads, "tasksByUser": tasks_by_user, "taskNames": all_titles,
        "staffed": staffed, "unassignedCount": unassigned_count, "total": total,
        "people": len(workloads), "over": sum(1 for x in workloads.values() if x["hasOverload"]),
        "gaps": len(gaps), "taskCountConsistent": total == len(staffed_ids | unassigned_ids) and total >= unassigned_count,
    }


def assignment_wrap_extras(a: dict[str, Any]) -> int:
    extras = 0
    for plain, _ in a["matched"] + a["missing"]:
        length = len(plain)
        extras += 2 if length > 56 else 1 if length > 40 else 0
    return extras


def wrap_rich(attrs: list[tuple[str, str]], limit: int, prefix: str = "") -> list[str]:
    if not attrs:
        return [esc(prefix.rstrip())] if prefix else []
    lines: list[str] = []
    plain_line, rich_line = prefix, esc(prefix)
    for plain, rich in attrs:
        sep = "" if not plain_line else " · "
        if plain_line and len(plain_line) + len(sep) + len(plain) > limit:
            lines.append(rich_line)
            plain_line, rich_line = plain, rich
        else:
            plain_line += sep + plain
            rich_line += sep + rich
    if rich_line:
        lines.append(rich_line)
    return lines


def compute_layout(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(scenarios)
    P = max((s["people"] for s in scenarios), default=1)
    P = max(P, 1)
    T = max((max((len(v) for v in s["tasksByUser"].values()), default=0) for s in scenarios), default=0)
    T = max(T, 1)
    gap_rows = [sum(1 for a in s["assignments"] if a["category"] != "full") for s in scenarios]
    R = max([len(s["unassigned"]) for s in scenarios] + gap_rows + [0])
    O = max((s["over"] for s in scenarios), default=0)
    A_max = max((len(a["matched"]) + len(a["missing"]) for s in scenarios for a in s["assignments"]), default=0)
    extra_wrap = max((assignment_wrap_extras(a) for s in scenarios for a in s["assignments"]), default=0)
    CARD_H = 164 + 32 * A_max + 16 * extra_wrap
    PITCH = CARD_H + 24
    STICKY_W, PANEL_PAD, COL_GAP_MIN, PANEL_W_MIN = 160, 32, 40, 2000
    inner_w = max(PANEL_W_MIN - 2 * PANEL_PAD,
                  P * STICKY_W + max(0, P - 1) * COL_GAP_MIN)
    GRID_W = inner_w
    PANEL_W = GRID_W + 2 * PANEL_PAD
    CARD_W = (GRID_W - 32) / 2
    BOARD_W = n * PANEL_W + max(0, n - 1) * 60

    E = 0
    for s in scenarios:
        for width, rows, prefix_key in ((CARD_W, s["unassigned"], "required"), (CARD_W, [a for a in s["assignments"] if a["category"] != "full"], "missing")):
            limit = max(1, math.floor((width - 68) / 8))
            extras = 0
            for row in rows:
                attrs = row.get(prefix_key, [])
                prefix = "Needs: " if prefix_key == "required" and attrs else "Missing " if attrs else ""
                extras += max(0, len(wrap_rich(attrs, limit, prefix)) - 1)
            E = max(E, extras)

    if R == 0 and O == 0:
        DEC_H = 40
    else:
        DEC_H = (80 + 64 * R + 20 * E if R else 0) + (32 if R and O else 0) + (80 + 64 * O if O else 0)
    SECTION_GAP, TITLE_TO_CONTENT, LEGEND_H = 100, 56, 18
    # Multi-option header ends at y=128; keep 40 px clear before KPI cards.
    # Single-option panels have no option title or scenario subheader.
    KPI_TOP, KPI_H = (64 if n == 1 else 168), 136
    attention_drawn = not (n == 1 and R == 0 and O == 0)
    attention_title = KPI_TOP + KPI_H + SECTION_GAP
    attention_top = attention_title + TITLE_TO_CONTENT
    risk_h = 80 + 64 * R + 20 * E if R else 0
    OC = attention_top if R == 0 else attention_top + risk_h + (32 if O else 0)
    attention_bottom = attention_top + DEC_H
    workload_title = (attention_bottom + SECTION_GAP if attention_drawn
                      else KPI_TOP + KPI_H + SECTION_GAP)
    workload_row_top = workload_title + 104
    legend_top = workload_title + 108 + 60 * P
    assignee_title = legend_top + LEGEND_H + SECTION_GAP
    cardTop = assignee_title + TITLE_TO_CONTENT
    taskTop = cardTop + 162
    PANEL_H = taskTop + PITCH * T + 8
    BASE = workload_title - 32
    max_value = max((max(p["capacity"], p["projected"]) for s in scenarios for p in s["workloads"].values()), default=1.0)
    scale = 1000 / max(max_value, 0.1)
    layout = {"n": n, "P": P, "T": T, "R": R, "E": E, "O": O, "A_max": A_max,
              "extraWrap": extra_wrap, "CARD_H": CARD_H, "PITCH": PITCH, "PANEL_W": PANEL_W,
              "GRID_W": GRID_W, "CARD_W": rnd(CARD_W), "BOARD_W": BOARD_W, "DEC_H": DEC_H,
              "STICKY_W": STICKY_W, "PANEL_PAD": PANEL_PAD, "SECTION_GAP": SECTION_GAP,
              "KPI_TOP": KPI_TOP, "KPI_H": KPI_H, "attentionDrawn": attention_drawn,
              "attentionTitle": attention_title, "attentionTop": attention_top,
              "workloadTitle": workload_title, "workloadRowTop": workload_row_top,
              "legendTop": legend_top, "legendHeight": LEGEND_H, "assigneeTitle": assignee_title,
              "BASE": BASE, "OC": OC, "cardTop": cardTop, "taskTop": taskTop,
              "PANEL_H": PANEL_H, "maxValue": max_value, "scale": scale}
    if n >= 2:
        d, identical, never, diff_ids = comparison_groups(scenarios)
        TABLE_W, DIFF_W = 560 + 468 * n, 768 + 468 * n
        SUM_H, TTOP = 130 + 62 * n, 170 + 62 * n
        DIFF_H = 200 if d == 0 else 408 + 92 * d
        layout.update({"DX": BOARD_W + 100, "DL": BOARD_W + 204, "TABLE_W": TABLE_W,
                       "DIFF_W": DIFF_W, "SUM_H": SUM_H, "TTOP": TTOP, "DIFF_H": DIFF_H,
                       "d": d, "identical": identical, "never": never, "diffTaskIds": diff_ids})
    return layout


def outcome_map(s: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for a in s["assignments"]:
        by_task[a["taskId"]].append(a)
    out: dict[str, dict[str, Any]] = {}
    for tid, rows in by_task.items():
        owners = tuple(sorted(x["name"] for x in rows))
        numeric = [x["fit"] for x in rows if x["fit"] is not None]
        fit = max(numeric) if numeric else None
        category = "no_requirements" if not numeric else "full" if fit == 100 else "partial" if fit > 0 else "zero"
        missing = rows[0]["missing"] if rows else []
        out[tid] = {"assigned": True, "fullyStaffed": True, "owners": owners, "fit": fit,
                    "category": category, "missing": missing}
    for u in s["unassigned"]:
        existing = out.get(u["taskId"])
        if existing:
            existing["fullyStaffed"] = False
            existing["reason"] = u["reason"]
        else:
            out[u["taskId"]] = {"assigned": False, "fullyStaffed": False, "reason": u["reason"],
                                 "owners": (), "fit": None, "category": "unassigned", "missing": []}
    return out


def comparison_groups(scenarios: list[dict[str, Any]]) -> tuple[int, int, int, list[str]]:
    maps = [outcome_map(s) for s in scenarios]
    tids = sorted(set().union(*(set(m) for m in maps)), key=lambda t: next((s["taskNames"].get(t, t) for s in scenarios if t in s["taskNames"]), t).lower())
    diff, identical, never = [], 0, 0
    for tid in tids:
        rows = [m.get(tid, {"assigned": False, "fullyStaffed": False, "owners": (),
                            "category": "unassigned", "fit": None}) for m in maps]
        if not any(x["assigned"] for x in rows):
            never += 1
        elif (any(not x["assigned"] for x in rows)
              or len({x.get("fullyStaffed", False) for x in rows}) > 1
              or len({x["owners"] for x in rows}) > 1
              or len({(x["category"], x["fit"]) for x in rows}) > 1):
            diff.append(tid)
        else:
            identical += 1
    return len(diff), identical, never, diff


def task_number(task_id: str) -> str:
    match = re.fullmatch(r"w:itm:(\d+)", task_id)
    if not match:
        raise ValueError(f"Invalid Wrike task id: {task_id!r}")
    return match.group(1)


def person_columns(s: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(s["workloads"].values(), key=lambda p: (-p["pct"], p["name"].lower()))


def column_x(layout: dict[str, Any], px: int, index: int) -> int:
    left, P = px + layout["PANEL_PAD"], layout["P"]
    if P == 1:
        return rnd(left + (layout["GRID_W"] - 160) / 2)
    return rnd(left + index * (layout["GRID_W"] - 160) / (P - 1))


def widget_specs(s: dict[str, Any]) -> list[tuple[str, int, str]]:
    rows = [("Tasks staffed", s["staffed"], "red" if s["unassignedCount"] else "blue"),
            ("Assignees proposed", s["people"], "blue"),
            ("Assignees over capacity", s["over"], "red" if s["over"] else "green")]
    if s["gaps"]:
        rows.append(("Tasks with missing skills", s["gaps"], "orange"))
    if s["unassignedCount"]:
        rows.append(("Tasks not assigned", s["unassignedCount"], "red"))
    return rows


def widget_colors(kind: str) -> tuple[str, str, str]:
    if kind == "green": return COLORS["green_fill"], COLORS["green"], COLORS["green"]
    if kind == "orange": return COLORS["orange_widget"], COLORS["orange"], COLORS["orange"]
    if kind == "red": return COLORS["red_fill"], COLORS["red"], COLORS["red_text"]
    return COLORS["blue_fill"], COLORS["blue"], COLORS["blue"]


def task_card(a: dict[str, Any], x: int, y: int, card_h: int) -> dict[str, Any]:
    title = esc(truncate_words(a["title"], 60))
    url = f"https://www.wrike.com/open.htm?id={esc(task_number(a['taskId']))}"
    head = f'<p>&nbsp;</p><h4><a target="_blank" href="{url}">{title}</a></h4>'
    if a["category"] == "no_requirements":
        content = head + f'<p><span style="color: {COLORS["orange"]}"><strong>No requirements</strong></span></p>'
        fill = COLORS["orange_fill"]
    else:
        fill = COLORS["green_fill"] if a["category"] == "full" else COLORS["orange_fill"] if a["category"] == "partial" else COLORS["red_fill"]
        attrs = "".join(f"<p>&#x2705; {rich}</p>" for _, rich in a["matched"])
        attrs += "".join(f"<p>&#x274C; {rich}</p>" for _, rich in a["missing"])
        content = head + f'<div style="text-align: right"><p><strong>{a["fit"]}% fit</strong></p></div>'
        if a["matched"] or a["missing"]:
            content += f'<div style="text-align: left"><p>Skills and attributes</p>{attrs}</div>'
    return shape(x, y, 5, 160, card_h, fill, fill, 0.5, content, 12)


def assignee_card(p: dict[str, Any], x: int, y: int) -> dict[str, Any]:
    fill, stroke = ((COLORS["red_fill"], COLORS["red"]) if p["state"] == "red" else
                    (COLORS["orange_fill"], COLORS["orange"]) if p["state"] == "orange" else
                    (COLORS["green_fill"], COLORS["green"]))
    overloaded = f'<h5><span style="color: {COLORS["red_text"]}">overloaded</span></h5>' if p["state"] == "red" else ""
    content = f'<h4><strong>{esc(p["name"])}</strong></h4><p>{esc(p["role"])}</p>{overloaded}'
    content += f'<h6><span style="color: {COLORS["muted"]}">{esc(p["userId"])}</span></h6>'
    return shape(x, y, 1, 160, 138, fill, stroke, 2, content, 12)


def link_for(tid: str) -> str:
    return f"https://www.wrike.com/open.htm?id={esc(task_number(tid))}"


def attention_rows(s: dict[str, Any], kind: str, width: int) -> tuple[list[str], int]:
    limit1, limit2 = max(12, math.floor((width - 68) / 11)), max(12, math.floor((width - 68) / 8))
    rows: list[str] = []
    continuation = 0
    if kind == "unassigned":
        unique_unassigned: dict[str, dict[str, Any]] = {}
        for row in s["unassigned"]:
            unique_unassigned.setdefault(row["taskId"], row)
        source = sorted(unique_unassigned.values(), key=lambda x: x["title"].lower())
        for u in source:
            reason = "not fully staffed" if u["partiallyStaffed"] else u["reason"]
            suffix = f" · {reason}"
            title = truncate_words(u["title"], max(8, limit1 - len(suffix)))
            line1 = f'<p>&#x1F7E5;&nbsp;&nbsp;<a href="{link_for(u["taskId"])}"><strong>{esc(title)}</strong></a> · {esc(reason)}</p>'
            if u["reasonKind"] == "requirements":
                rich_lines = wrap_rich(u["required"], limit2, "Needs: ") or ["Needs:"]
            elif u["reasonKind"] == "availability":
                lead = "No additional suitable assignee has free capacity" if u["partiallyStaffed"] else "Requirements can be met, but no candidate has free capacity"
                rich_lines = [f'{lead} in {esc(s["period"]["start"])} – {esc(s["period"]["end"])}']
            else:
                rich_lines = ["No additional matching details were returned"]
            line2 = "".join(f'<h6>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color: {COLORS["secondary"]}">{x}</span></h6>' for x in rich_lines)
            continuation += max(0, len(rich_lines) - 1)
            rows.append(line1 + line2)
    elif kind == "gaps":
        source = [a for a in s["assignments"] if a["category"] != "full"]
        source.sort(key=lambda a: (0 if a["category"] == "zero" else 1 if a["category"] == "no_requirements" else 2,
                                   a["fit"] if a["fit"] is not None else 0, a["title"].lower()))
        for a in source:
            label = "requirements not set" if a["category"] == "no_requirements" else f'{a["fit"]}% fit'
            suffix = f" → {a['name']} · {label}"
            title = truncate_words(a["title"], max(8, limit1 - len(suffix)))
            line1 = f'<p>&#x1F7E8;&nbsp;&nbsp;<a href="{link_for(a["taskId"])}"><strong>{esc(title)}</strong></a> → <strong>{esc(a["name"])}</strong> · {esc(label)}</p>'
            if a["category"] == "no_requirements":
                rich_lines = ["No skills or attributes set on the task · assigned on availability only"]
            else:
                rich_lines = wrap_rich(a["missing"], limit2, "Missing ") or ["Missing"]
            line2 = "".join(f'<h6>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color: {COLORS["secondary"]}">{x}</span></h6>' for x in rich_lines)
            continuation += max(0, len(rich_lines) - 1)
            rows.append(line1 + line2)
    else:
        source = sorted((p for p in s["workloads"].values() if p["hasOverload"]), key=lambda p: (-p["overload"], p["name"].lower()))
        take = 4 if s["precision"] == "WEEKS" else 6
        for p in source:
            bits = []
            for interval in p["overloadIntervals"][:take]:
                reason = f' · {esc(interval["explanation"])}' if interval["explanation"] else ""
                bits.append(f'{esc(interval["label"])} +{amount_text(interval["amount"], p["unitLabel"])}{reason}')
            if len(p["overloadIntervals"]) > take:
                bits.append(f'+{len(p["overloadIntervals"]) - take} more')
            detail = f'{amount_text(p["projected"], p["unitLabel"])} of {amount_text(p["capacity"], p["unitLabel"])}' + (" · " + " · ".join(bits) if bits else "")
            rows.append(f'<p>&#x1F7E5;&nbsp;&nbsp;<strong>{esc(p["name"])}</strong> · over capacity by {amount_text(p["overload"], p["unitLabel"])}</p><h6>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color: {COLORS["secondary"]}">{detail}</span></h6>')
    return rows, continuation


def attention_card(kind: str, rows: list[str], x: int, y: int, width: int, height: int,
                   R: int, E: int, O: int) -> dict[str, Any]:
    count = len(rows)
    if kind == "unassigned":
        title, color, fill, stroke, pad = "Items with no match found", COLORS["red_text"], COLORS["red_fill"], COLORS["red"], 3 * R + E + 4
    elif kind == "gaps":
        title, color, fill, stroke, pad = "Items with partial match", COLORS["orange"], COLORS["orange_widget"], COLORS["orange"], 3 * R + E + 4
    else:
        title, color, fill, stroke, pad = "Overload assignees", COLORS["red_text"], COLORS["red_fill"], COLORS["red"], 3 * O + 4
    joined = '<p>&nbsp;</p>'.join(rows)
    content = f'<div style="text-align: left"><p>&nbsp;</p><h3><span style="color: {color}"><strong>{title} ({count})</strong></span></h3><p>&nbsp;</p>{joined}' + '<p>&nbsp;</p>' * pad + '</div>'
    return shape(x, y, 1, width, height, fill, stroke, 2, content, 17)


def scenario_summary(s: dict[str, Any]) -> str:
    base = f'{s["staffed"]} of {s["total"]} tasks staffed across {s["people"]} assignees'
    return base + (f' ({s["unassignedCount"]} unassigned)' if s["unassignedCount"] else "")


def option_letter(index: int) -> str:
    return f"Option {chr(65 + index)}"


def tradeoff(scenarios: list[dict[str, Any]], index: int, diff_ids: list[str]) -> str:
    s = scenarios[index]
    gains, giveups = [], []
    staffed_counts = [x["staffed"] for x in scenarios]
    if staffed_counts.count(max(staffed_counts)) == 1 and s["staffed"] == max(staffed_counts): gains.append("Most tasks staffed")
    if s["staffed"] == s["total"] and any(x["staffed"] < x["total"] for i, x in enumerate(scenarios) if i != index): gains.append("Every task staffed")
    if s["gaps"] == 0 and any(x["gaps"] > 0 for i, x in enumerate(scenarios) if i != index): gains.append("Only 100% fits")
    if s["over"] == 0 and any(x["over"] > 0 for i, x in enumerate(scenarios) if i != index): gains.append("No one over capacity")
    if s["unassignedCount"]:
        giveups.append(f'{s["unassignedCount"]} task' + (" still requires staffing" if s["unassignedCount"] == 1 else "s still require staffing"))
    zero = sum(1 for a in s["assignments"] if a["category"] == "zero")
    nr = sum(1 for a in s["assignments"] if a["category"] == "no_requirements")
    if zero: giveups.append(f"{zero} assigned at 0% fit")
    if nr: giveups.append(f"{nr} assigned with requirements not set")
    if gains or giveups:
        return (gains[0] if gains else "") + (" — but " if gains and giveups else "") + (" and ".join(giveups[:2]) if giveups else "")
    return f"Different people at the same fit on {len(diff_ids)} tasks" if diff_ids else "Same people on the same tasks as the other options"


def build_items(data: dict[str, Any], scenarios: list[dict[str, Any]], layout: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    steps: dict[int, list[dict[str, Any]]] = {i: [] for i in range(1, 8)}
    n, P = layout["n"], layout["P"]
    selected = bool(data.get("selectedTasks")) or not str(data.get("scopeTitle") or "").strip()
    scope = str(data.get("scopeTitle") or "selected Wrike tasks")
    scope_url = safe_wrike_url(data.get("scopeUrl"))
    if selected:
        subtitle_content = ptext("for selected Wrike tasks", center=True)
    else:
        linked_scope = (f'<a target="_blank" href="{scope_url}">{esc(scope)}</a>'
                        if scope_url else f'<span style="color: {COLORS["black"]}">{esc(scope)}</span>')
        subtitle_content = (f'<div style="text-align: center"><p>'
                            f'<span style="color: {COLORS["black"]}">for </span>{linked_scope}</p></div>')

    for i, s in enumerate(scenarios):
        px = i * (layout["PANEL_W"] + 60)
        left = px + layout["PANEL_PAD"]
        steps[1].append(shape(px, 0, 0, layout["PANEL_W"], layout["PANEL_H"], COLORS["panel"], COLORS["blue"], 2))
    steps[1].append(text_item(layout["BOARD_W"] / 2 - 600, -206, ptext("Assignee suggestions", bold=True, center=True), 64, 1200))
    steps[1].append(text_item(layout["BOARD_W"] / 2 - 800, -107, subtitle_content, 36, 1600))
    if n >= 2:
        dx = layout["DX"]
        steps[1].append(text_item(dx, -206, ptext("Comparison of options", bold=True, center=True), 64, layout["DIFF_W"]))
        summary_lines = ['<h2><strong>Summary</strong></h2>']
        for i, s in enumerate(scenarios):
            label = f' ({esc(s["label"])})' if s["label"] else ""
            summary_lines.append(f'<p><strong>{option_letter(i)}{label}</strong> — {s["staffed"]} of {s["total"]} tasks staffed · {s["people"]} assignees · {s["over"]} over capacity · {s["gaps"]} with missing skills · {s["unassignedCount"]} not assigned</p>')
        summary_lines.append('<p><strong>Choose the option that best fits your priorities, or adjust the assignments.</strong></p>')
        steps[1].append(shape(dx, 0, 1, layout["DIFF_W"], layout["SUM_H"], COLORS["panel"], COLORS["blue"], 2, "".join(summary_lines), 24))

    for i, s in enumerate(scenarios):
        px = i * (layout["PANEL_W"] + 60)
        left = px + layout["PANEL_PAD"]
        if n >= 2:
            steps[2].append(shape(left + layout["GRID_W"] / 2 - 40, 32, 2, 80, 6, COLORS["blue"], COLORS["blue"], 0.5))
            steps[2].append(text_item(
                left, 56,
                ptext(option_letter(i), COLORS["primary"], bold=True, center=True),
                36, layout["GRID_W"],
            ))
            option_subheader = s["label"] or tradeoff(scenarios, i, layout["diffTaskIds"])
            steps[2].append(text_item(left, 104, ptext(truncate_words(option_subheader, 100), center=True), 18, layout["GRID_W"]))
        drawn = layout["attentionDrawn"]
        titles = [("Your attention needed", layout["attentionTitle"])] if drawn else []
        titles += [("Workload and capacity", layout["workloadTitle"]),
                   ("Assignees and task recommendations", layout["assigneeTitle"])]
        for title, y in titles:
            steps[2].append(text_item(left, y, ptext(title, bold=True), 36, layout["GRID_W"]))
        widgets = widget_specs(s)
        k = len(widgets)
        wid_w = (layout["GRID_W"] - 25 * (k - 1)) / k
        for wi, (label, number, kind) in enumerate(widgets):
            x = left + rnd(wi * (wid_w + 25))
            fill, stroke, num_color = widget_colors(kind)
            steps[2].append(shape(x, layout["KPI_TOP"], 1, wid_w, layout["KPI_H"], fill, stroke, 2))
            steps[2].append(text_item(x + 24, layout["KPI_TOP"] + 18, ptext(label, COLORS["secondary"]), 18, wid_w - 48))
            steps[2].append(text_item(x + 24, layout["KPI_TOP"] + 44, ptext(str(number), num_color, bold=True), 56, 200))
            if label == "Tasks staffed":
                steps[2].append(text_item(x + 24 + 38 * len(str(number)), layout["KPI_TOP"] + 78, ptext(f'of {s["total"]}', COLORS["secondary"]), 24, 200))

        un_rows, _ = attention_rows(s, "unassigned", layout["CARD_W"])
        gap_rows, _ = attention_rows(s, "gaps", layout["CARD_W"])
        over_rows, _ = attention_rows(s, "over", layout["GRID_W"])
        if un_rows or gap_rows:
            only = bool(un_rows) ^ bool(gap_rows)
            width = layout["GRID_W"] if only else layout["CARD_W"]
            if un_rows:
                rows, _ = attention_rows(s, "unassigned", width)
                steps[3].append(attention_card("unassigned", rows, left, layout["attentionTop"], width, 80 + 64 * layout["R"] + 20 * layout["E"], layout["R"], layout["E"], layout["O"]))
            if gap_rows:
                x = left if only else left + layout["CARD_W"] + 32
                rows, _ = attention_rows(s, "gaps", width)
                steps[3].append(attention_card("gaps", rows, x, layout["attentionTop"], width, 80 + 64 * layout["R"] + 20 * layout["E"], layout["R"], layout["E"], layout["O"]))
        if over_rows:
            steps[3].append(attention_card("over", over_rows, left, layout["OC"], layout["GRID_W"], 80 + 64 * layout["O"], layout["R"], layout["E"], layout["O"]))
        if n >= 2 and s["unassignedCount"] == 0 and not (gap_rows or over_rows):
            steps[3].append(text_item(left, layout["attentionTop"], ptext(f'No staffing risks — all {s["total"]} tasks staffed at 100% fit, no one over capacity', italic=True), 20, layout["GRID_W"]))

        period = (f'<p><span style="color: {COLORS["primary"]}"><strong>Period:</strong> '
                  f'{esc(s["period"]["start"])} – {esc(s["period"]["end"])}</span></p>')
        steps[4].append(text_item(left, layout["workloadTitle"] + 56, period, 16, layout["GRID_W"]))
        people = person_columns(s)
        for r, person in enumerate(people):
            ry = layout["workloadRowTop"] + 60 * r
            track_w = rnd(person["capacity"] * layout["scale"])
            committed_w = rnd(person["committed"] * layout["scale"])
            projected_w = rnd(person["projected"] * layout["scale"])
            new_w = max(0, projected_w - committed_w)
            if track_w:
                steps[4].append(shape(left + 200, ry, 1, track_w, 40, COLORS["track"], COLORS["track"], 0.5))
            if committed_w:
                steps[4].append(shape(left + 200, ry, 2, committed_w, 40, COLORS["committed"], COLORS["committed"], 0.5))
            if new_w:
                fill = COLORS["over"] if person["hasOverload"] else COLORS["proposal"]
                steps[4].append(shape(left + 200 + committed_w, ry, 2, new_w, 40, fill, fill, 0.5))
            if track_w:
                steps[4].append(shape(left + 200 + track_w - 2, ry - 4, 4, 4, 48, COLORS["blue"], COLORS["blue"], 0.5))
            task_count_text = "No tasks" if person["taskCount"] == 0 else "1 task" if person["taskCount"] == 1 else f'{person["taskCount"]} tasks'
            row_content = f'<p><span style="color: {COLORS["primary"]}"><strong>{esc(person["name"])}</strong></span></p><p><span style="color: {COLORS["secondary"]}">{task_count_text}</span></p>'
            steps[4].append(text_item(left, ry - 4, row_content, 16, 180))
            figures = f'{amount_text(person["proposed"], person["unitLabel"])} new + {amount_text(person["committed"], person["unitLabel"])} already assigned = {amount_text(person["projected"], person["unitLabel"])} of {amount_text(person["capacity"], person["unitLabel"])} · {person["pct"]}%'
            if person["hasOverload"]:
                figures += f' · Overload {amount_text(person["overload"], person["unitLabel"])}'
            steps[4].append(text_item(left + 1224, ry + 12, ptext(figures, COLORS["secondary"]), 14, layout["GRID_W"] - 1224))
        legend = f'<p><span style="color: {COLORS["committed"]}"><strong>&#x25AE;</strong></span><span style="color: {COLORS["secondary"]}"> – already assigned effort, </span><span style="color: {COLORS["proposal"]}"><strong>&#x25AE;</strong></span><span style="color: {COLORS["secondary"]}"> – effort in this proposal, </span><span style="color: {COLORS["over"]}"><strong>&#x25AE;</strong></span><span style="color: {COLORS["secondary"]}"> – over capacity, </span><span style="color: {COLORS["track"]}"><strong>&#x25AE;</strong></span><span style="color: {COLORS["secondary"]}"> – free capacity, </span><span style="color: {COLORS["blue"]}"><strong>&#x2503;</strong></span><span style="color: {COLORS["secondary"]}"> – total capacity</span></p>'
        legend_top = layout["workloadTitle"] + 108 + 60 * len(people)
        steps[4].append(text_item(left + 200, legend_top, legend, 14, 1000))

        columns = [column_x(layout, px, c) for c in range(P)]
        for c, person in enumerate(people):
            steps[5].append(assignee_card(person, columns[c], layout["cardTop"]))
        for c, person in enumerate(people):
            owned = sorted(s["tasksByUser"].get(person["userId"], []), key=lambda a: a["title"].lower())
            for j, a in enumerate(owned):
                steps[7].append(task_card(a, columns[c], layout["taskTop"] + layout["PITCH"] * j, layout["CARD_H"]))

    if n >= 2:
        build_comparison(steps[6], scenarios, layout)
    return steps


def cell_content(lines: list[tuple[str, str, bool]], center: bool = True) -> str:
    align = "center" if center else "left"
    body = "".join(f'<p><span style="color: {color}">{"<strong>" if bold else ""}{symbol_codes(esc(line))}{"</strong>" if bold else ""}</span></p>' for line, color, bold in lines)
    return f'<div style="text-align: {align}">{body}</div>'


def build_comparison(items: list[dict[str, Any]], scenarios: list[dict[str, Any]], layout: dict[str, Any]) -> None:
    n, dx, dl, ttop = layout["n"], layout["DX"], layout["DL"], layout["TTOP"]
    items.append(shape(dx, ttop, 0, layout["DIFF_W"], layout["DIFF_H"], COLORS["panel"], COLORS["blue"], 2))
    items.append(text_item(dl, ttop + 48, ptext("What changes between options", bold=True, center=True), 36, layout["TABLE_W"]))
    if layout["d"] == 0:
        subtitle = "All options assign the same people to the same tasks"
    else:
        parts = [f'{layout["d"]} of {max(s["total"] for s in scenarios)} tasks differ between options']
        if layout["identical"]: parts.append(f'{layout["identical"]} are identical')
        if layout["never"]: parts.append(f'{layout["never"]} not staffed in any option')
        subtitle = " · ".join(parts)
    items.append(text_item(dl, ttop + 100, ptext(subtitle, center=True), 18, layout["TABLE_W"]))
    legend = "✅ 100% fit · ⚠️ assigned with missing skills or requirements not set · ⛔ assigned at 0% fit · — not assigned"
    items.append(text_item(dl, ttop + 136, ptext(legend, center=True), 16, layout["TABLE_W"]))
    headers = [("Task", dl, 560)] + [(option_letter(i), dl + 568 + 468 * i, 460) for i in range(n)]
    for label, x, width in headers:
        items.append(shape(x, ttop + 192, 1, width, 56, COLORS["blue_fill"], COLORS["blue"], 2, cell_content([(label, COLORS["primary"], True)]), 20))
    maps = [outcome_map(s) for s in scenarios]
    for row_index, tid in enumerate(layout["diffTaskIds"]):
        y = ttop + 256 + 92 * row_index
        title = next((s["taskNames"].get(tid) for s in scenarios if s["taskNames"].get(tid)), tid)
        items.append(shape(dl, y, 1, 560, 84, COLORS["white"], COLORS["blue"], 1, cell_content([(title, COLORS["primary"], True)], False), 18))
        for i, omap in enumerate(maps):
            outcome = omap.get(tid, {"assigned": False, "fullyStaffed": False,
                                     "reason": "no one has availability", "category": "unassigned",
                                     "owners": (), "fit": None, "missing": []})
            if not outcome["assigned"]:
                reason = outcome.get("reason") or "no suitable assignee was found"
                lines, fill, stroke = [("— Not assigned", COLORS["primary"], True), (reason, COLORS["secondary"], False)], COLORS["red_fill"], COLORS["red"]
            else:
                owners = ", ".join(outcome["owners"])
                if not outcome.get("fullyStaffed", True):
                    reason = outcome.get("reason") or "additional staffing is still needed"
                    lines, fill, stroke = [(f"⚠️ {owners} · not fully staffed", COLORS["primary"], True),
                                           (reason, COLORS["secondary"], False)], COLORS["red_fill"], COLORS["red"]
                elif outcome["category"] == "full":
                    lines, fill, stroke = [(f"✅ {owners} · 100% fit", COLORS["primary"], True)], COLORS["green_fill"], COLORS["green"]
                elif outcome["category"] == "zero":
                    miss = "missing " + " · ".join(x[0] for x in outcome["missing"])
                    lines, fill, stroke = [(f"⛔ {owners} · 0% fit", COLORS["primary"], True), (truncate_words(miss, 80), COLORS["secondary"], False)], COLORS["orange_widget"], COLORS["orange"]
                elif outcome["category"] == "no_requirements":
                    lines, fill, stroke = [(f"⚠️ {owners}", COLORS["primary"], True), ("requirements not set", COLORS["secondary"], False)], COLORS["orange_widget"], COLORS["orange"]
                else:
                    miss = "missing " + " · ".join(x[0] for x in outcome["missing"])
                    lines, fill, stroke = [(f'⚠️ {owners} · {outcome["fit"]}% fit', COLORS["primary"], True), (truncate_words(miss, 80), COLORS["secondary"], False)], COLORS["orange_widget"], COLORS["orange"]
            items.append(shape(dl + 568 + 468 * i, y, 1, 460, 84, fill, stroke, 1, cell_content(lines), 18))
    totals_y = ttop + 264 + 92 * layout["d"]
    total_tasks = max(s["total"] for s in scenarios)
    items.append(shape(dl, totals_y, 1, 560, 84, COLORS["white"], COLORS["blue"], 2,
                       cell_content([(f"Totals across all {total_tasks} tasks", COLORS["primary"], True)], False), 18))
    for i, s in enumerate(scenarios):
        lines = [(f'{s["staffed"]} staffed · {s["people"]} assignees · {s["over"]} over capacity', COLORS["primary"], True),
                 (f'{s["gaps"]} with missing skills · {s["unassignedCount"]} not assigned', COLORS["secondary"], False)]
        items.append(shape(dl + 568 + 468 * i, totals_y, 1, 460, 84, COLORS["white"], COLORS["blue"], 2, cell_content(lines), 18))


def validate_items(steps: dict[int, list[dict[str, Any]]]) -> list[str]:
    errors: list[str] = []
    seen_task_links = 0
    for step, items in steps.items():
        for idx, item in enumerate(items):
            if item.get("type") not in {"SHAPE", "TEXT"}:
                errors.append(f"step {step} item {idx}: unsupported type {item.get('type')!r}")
            payload = item.get("payload") or {}
            pos = payload.get("position") or {}
            if not all(k in pos for k in ("x", "y", "z")) or not isinstance(pos.get("z"), int):
                errors.append(f"step {step} item {idx}: missing integer x/y/z position")
            if item.get("type") == "SHAPE":
                geom = payload.get("geometry") or {}
                if geom.get("width", 0) <= 0 or geom.get("height", 0) <= 0:
                    errors.append(f"step {step} item {idx}: non-positive shape geometry")
                style = ((payload.get("data") or {}).get("style") or {})
                if style.get("fillColor") not in ALLOWED_COLORS or style.get("strokeColor") not in ALLOWED_COLORS:
                    errors.append(f"step {step} item {idx}: color outside approved palette")
            content = str((payload.get("data") or {}).get("content") or "")
            if "open.htm?id=" in content:
                seen_task_links += 1
                if "w:itm:" in content:
                    errors.append(f"step {step} item {idx}: canonical prefix leaked into Wrike URL")
    if any(steps.values()) and seen_task_links == 0:
        errors.append("No Wrike task links were generated.")
    return errors


def batches_for(steps: dict[int, list[dict[str, Any]]], board_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for step in range(1, 8):
        items = steps[step]
        for offset in range(0, len(items), 50):
            result.append({"step": step, "part": offset // 50 + 1,
                           "args": {"boardId": board_id or "__BOARD_ID__", "items": items[offset:offset + 50]}})
    return result


def compile_plan(data: dict[str, Any], board_id: str = "") -> tuple[dict[str, Any], list[dict[str, Any]]]:
    scenarios, meta = normalize_input(data)
    errors = list(meta["errors"])
    if errors or not scenarios:
        return {"errors": errors}, []
    layout = compute_layout(scenarios)
    steps = build_items(data, scenarios, layout)
    errors.extend(validate_items(steps))
    counts = Counter(item["type"] for items in steps.values() for item in items)
    batches = batches_for(steps, board_id)
    if any(len(b["args"]["items"]) > 50 for b in batches):
        errors.append("A batch exceeds Klaxoon's 50-item limit.")
    selected = bool(data.get("selectedTasks")) or not str(data.get("scopeTitle") or "").strip()
    scope = str(data.get("scopeTitle") or "selected Wrike tasks")
    board_title = "Recommend assignees — selected Wrike tasks" if selected else f"Recommend assignees — {scope}"
    manifest = {
        "errors": errors, "board": {"title": board_title}, "layout": layout,
        "expectedTotals": {"SHAPE": counts["SHAPE"], "TEXT": counts["TEXT"], "IDEA": 0},
        "itemCount": sum(counts.values()),
        "scenarioSummaries": [{k: s[k] for k in ("staffed", "total", "people", "over", "gaps", "unassignedCount", "taskCountConsistent")} | {"option": option_letter(i), "label": s["label"]} for i, s in enumerate(scenarios)],
        "batches": [],
    }
    return manifest, batches


def write_plan(manifest: dict[str, Any], batches: list[dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    batch_dir = out_dir / "batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    for old in batch_dir.glob("*.json"):
        old.unlink()
    records = []
    for seq, batch in enumerate(batches, start=1):
        name = f'{seq:02d}-step{batch["step"]}-{batch["part"]:02d}.json'
        path = batch_dir / name
        path.write_text(json.dumps(batch["args"], ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        records.append({"file": f"batches/{name}", "step": batch["step"], "part": batch["part"], "items": len(batch["args"]["items"])})
    manifest["batches"] = records
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def self_test() -> None:
    assert_standard_library_imports()
    sample = {
        "scopeTitle": "Demo project",
        "scopeUrl": "https://www.wrike.com/workspace.htm?acc=123",
        "recommendations": [{
            "affectedPeriod": {"start": "2026-10-01", "end": "2026-10-31"},
            "timeUnit": "MINUTES", "effortEstimationPrecision": "DAYS",
            "solutionsMetadata": {
                "tasks": {"tasks": [{"id": "w:itm:123456789", "name": "Design landing page"}, {"id": "w:itm:987654321", "name": "Implement analytics"}, {"id": "w:itm:555555555", "name": "Legal review"}]},
                "resources": {"resources": [{"id": "w:usr:1", "name": "Ada Lovelace"}, {"id": "w:usr:2", "name": "Grace Hopper"}]},
            },
            "solutions": [{
                "index": 0, "taskCount": 3,
                "assignments": [
                    {"taskId": "w:itm:123456789", "responsibleId": "w:usr:1", "reasoning": {"matchPercent": 100, "matchedAttributes": [{"id": "w:cp:10", "value": "Design"}]}},
                    {"taskId": "w:itm:987654321", "responsibleId": "w:usr:2", "reasoning": {"matchPercent": 50, "missingAttributes": [{"kind": "jobRole", "value": "Analyst"}]}},
                ],
                "unassignedItems": [{"taskId": "w:itm:555555555", "reasoning": {"flags": ["NO_MATCH_REQUIREMENTS"], "requiredAttributes": [{"id": "w:cp:10", "value": "Legal"}]}}],
                "resourceWorkloads": {
                    "w:usr:1": {"periodTotals": {"capacity": 2400, "outOfScopeAllocation": 600, "proposedAllocation": 600, "projectedWorkload": 1200, "overload": 0}, "overload": []},
                    "w:usr:2": {"periodTotals": {"capacity": 1200, "outOfScopeAllocation": 900, "proposedAllocation": 600, "projectedWorkload": 1500, "overload": 300}, "overload": [{"date": "2026-10-12", "amount": 300, "reason": "PROPOSAL"}]},
                },
            }],
        }],
        "users": [{"id": "w:usr:1", "name": "Ada Lovelace", "title": "Designer", "customFields": [{"id": "w:cp:10", "name": "Skill"}]}, {"id": "w:usr:2", "name": "Grace Hopper", "title": "Engineer"}],
    }
    manifest, batches = compile_plan(sample, "board-demo")
    assert not manifest["errors"], manifest["errors"]
    assert manifest["scenarioSummaries"][0]["staffed"] == 2
    assert manifest["scenarioSummaries"][0]["unassignedCount"] == 1
    assert manifest["expectedTotals"]["IDEA"] == 0
    assert manifest["expectedTotals"]["SHAPE"] > 0 and manifest["expectedTotals"]["TEXT"] > 0
    assert all(len(b["args"]["items"]) <= 50 for b in batches)
    assert any("123456789" in json.dumps(b, ensure_ascii=False) for b in batches)
    rendered = json.dumps(batches, ensure_ascii=False)
    items = [item for batch in batches for item in batch["args"]["items"]]
    assert "caused by this recommendation" in rendered
    assert "PROPOSAL" not in rendered and "NO_MATCH_REQUIREMENTS" not in rendered
    assert not any(symbol in rendered for symbol in ("✅", "❌", "🟥", "🟨", "⚠️", "⛔", "▮", "┃"))
    assert "https://www.wrike.com/workspace.htm?acc=123" in rendered
    scope_header = next(
        item for item in items
        if "workspace.htm?acc=123" in str((item["payload"].get("data") or {}).get("content") or "")
    )
    assert f'<span style="color: {COLORS["black"]}">for </span>' in scope_header["payload"]["data"]["content"]
    assert '<a target="_blank" href="https://www.wrike.com/workspace.htm?acc=123">Demo project</a>' in scope_header["payload"]["data"]["content"]
    assert '<a target="_blank" href="https://www.wrike.com/workspace.htm?acc=123" style=' not in scope_header["payload"]["data"]["content"]
    assert "for &quot;Demo project&quot;" not in rendered
    assert "Designer" in rendered and "Engineer" in rendered
    assert "Skill:" in rendered and "Job role:" in rendered
    assert "Items with no match found (1)" in rendered
    assert "Items with partial match (1)" in rendered
    assert "Overload assignees (1)" in rendered
    assert "worst fit first" not in rendered
    for title, expected_fill in (("Items with no match found (1)", COLORS["red_fill"]),
                                 ("Items with partial match (1)", COLORS["orange_widget"]),
                                 ("Overload assignees (1)", COLORS["red_fill"])):
        card = next(item for item in items if title in str((item["payload"].get("data") or {}).get("content") or ""))
        assert card["payload"]["data"]["style"]["fillColor"] == expected_fill
    assert f'<strong>Period:</strong> 2026-10-01 – 2026-10-31' in rendered
    assert not any(
        item["type"] == "SHAPE"
        and item["payload"]["data"]["style"]["fillColor"] == COLORS["white"]
        and item["payload"]["data"]["style"]["strokeColor"] == COLORS["white"]
        and (item["payload"]["geometry"]["width"] <= 4 or item["payload"]["geometry"]["height"] <= 4)
        for item in items
    )
    assert not any(
        item["type"] == "SHAPE"
        and item["payload"]["geometry"] == {"width": 80, "height": 6}
        and item["payload"]["data"]["style"]["fillColor"] == COLORS["blue"]
        for item in items
    )
    layout = manifest["layout"]
    assert layout["KPI_TOP"] == 64
    assert layout["PANEL_PAD"] == 32
    assert layout["PANEL_W"] - layout["GRID_W"] == 2 * layout["PANEL_PAD"]
    assert layout["attentionTitle"] - (layout["KPI_TOP"] + layout["KPI_H"]) == layout["SECTION_GAP"]
    assert layout["workloadTitle"] - (layout["attentionTop"] + layout["DEC_H"]) == layout["SECTION_GAP"]
    assert layout["assigneeTitle"] - (layout["legendTop"] + layout["legendHeight"]) == layout["SECTION_GAP"]
    assert layout["PANEL_H"] == layout["taskTop"] + layout["PITCH"] * layout["T"] + 8
    assert amount(120, "MINUTES") == 2.0
    assert amount(120, "HOURS") == 120.0
    assert amount_text(2.0, "h") == "2.0h"
    assert amount_text(2.0, "hours") == "2.0 hours"

    missing_users = json.loads(json.dumps(sample))
    missing_users["users"] = []
    missing_user_manifest, missing_user_batches = compile_plan(missing_users, "board-demo")
    assert not missing_user_batches
    assert any("missing get_users rows" in error for error in missing_user_manifest["errors"])

    blank_name = json.loads(json.dumps(sample))
    blank_name["users"][0]["name"] = "   "
    blank_name_manifest, blank_name_batches = compile_plan(blank_name, "board-demo")
    assert not blank_name_batches
    assert any("invalid display name" in error for error in blank_name_manifest["errors"])

    id_as_name = json.loads(json.dumps(sample))
    id_as_name["users"][0]["name"] = "w:usr:1"
    id_as_name_manifest, id_as_name_batches = compile_plan(id_as_name, "board-demo")
    assert not id_as_name_batches
    assert any("invalid display name" in error for error in id_as_name_manifest["errors"])

    no_title = json.loads(json.dumps(sample))
    no_title["users"][0] = {
        "id": "w:usr:1", "name": "Gordon Spencer", "title": "", "role": "User"
    }
    no_title_manifest, no_title_batches = compile_plan(no_title, "board-demo")
    assert not no_title_manifest["errors"], no_title_manifest["errors"]
    no_title_rendered = json.dumps(no_title_batches, ensure_ascii=False)
    assert "Gordon Spencer" in no_title_rendered
    assert "User" not in no_title_rendered

    no_solutions = json.loads(json.dumps(sample))
    no_solutions["recommendations"][0]["solutions"] = []
    no_solutions_manifest, no_solutions_batches = compile_plan(no_solutions, "board-demo")
    assert not no_solutions_batches
    assert any("No eligible items" in error for error in no_solutions_manifest["errors"])

    selected_tasks = json.loads(json.dumps(sample))
    selected_tasks["selectedTasks"] = True
    selected_manifest, selected_batches = compile_plan(selected_tasks, "board-demo")
    assert not selected_manifest["errors"], selected_manifest["errors"]
    selected_rendered = json.dumps(selected_batches, ensure_ascii=False)
    assert "for selected Wrike tasks" in selected_rendered
    assert "workspace.htm?acc=123" not in selected_rendered

    no_attributes = json.loads(json.dumps(sample))
    no_attributes["recommendations"][0]["solutions"][0]["assignments"][0]["reasoning"] = {"matchPercent": 75}
    no_attr_manifest, no_attr_batches = compile_plan(no_attributes, "board-demo")
    assert not no_attr_manifest["errors"], no_attr_manifest["errors"]
    no_attr_items = [item for batch in no_attr_batches for item in batch["args"]["items"]]
    no_attr_card = next(
        item for item in no_attr_items
        if "Design landing page" in str((item["payload"].get("data") or {}).get("content") or "")
    )
    no_attr_content = str(no_attr_card["payload"]["data"]["content"])
    assert "75% fit" in no_attr_content
    assert "Skills and attributes" not in no_attr_content

    partial = json.loads(json.dumps(sample))
    partial["recommendations"][0]["solutions"] = [partial["recommendations"][0]["solutions"][0]]
    for _ in range(2):
        partial["recommendations"][0]["solutions"][0]["unassignedItems"].append(
            {"taskId": "w:itm:987654321", "reasoning": {"flags": ["NO_MATCH_AVAILABILITY"]}}
        )
    more_complete = json.loads(json.dumps(partial["recommendations"][0]["solutions"][0]))
    more_complete["index"] = 1
    more_complete["unassignedItems"] = more_complete["unassignedItems"][:1]
    partial["recommendations"][0]["solutions"].append(more_complete)
    partial_manifest, partial_batches = compile_plan(partial, "board-demo")
    assert not partial_manifest["errors"], partial_manifest["errors"]
    assert partial_manifest["scenarioSummaries"][0]["staffed"] == 1
    assert partial_manifest["scenarioSummaries"][0]["unassignedCount"] == 2
    assert partial_manifest["scenarioSummaries"][0]["gaps"] == 1
    assert partial_manifest["layout"]["d"] >= 1
    partial_rendered = json.dumps(partial_batches, ensure_ascii=False)
    assert "not fully staffed" in partial_rendered
    assert "Items with no match found (2)" in partial_rendered
    normalized_partial, _ = normalize_input(partial)
    unassigned_rows, _ = attention_rows(
        normalized_partial[0], "unassigned", partial_manifest["layout"]["GRID_W"]
    )
    assert len(unassigned_rows) == 2
    assert unassigned_explanation(["UNRECOGNIZED"])[1] == "unknown"

    mixed_units = json.loads(json.dumps(sample))
    other_run = json.loads(json.dumps(mixed_units["recommendations"][0]))
    other_run["timeUnit"] = "DAYS"
    mixed_units["recommendations"].append(other_run)
    mixed_manifest, _ = compile_plan(mixed_units, "board-demo")
    assert any("incompatible timeUnit" in error for error in mixed_manifest["errors"])

    alternative = json.loads(json.dumps(sample["recommendations"][0]["solutions"][0]))
    alternative["index"] = 1
    alternative["assignments"][1]["responsibleId"] = "w:usr:1"
    alternative["resourceWorkloads"].pop("w:usr:2")
    sample["recommendations"][0]["solutions"].append(alternative)
    multi_manifest, multi_batches = compile_plan(sample, "board-demo")
    assert not multi_manifest["errors"], multi_manifest["errors"]
    assert multi_manifest["layout"]["n"] == 2
    assert multi_manifest["layout"]["d"] >= 1
    assert any(b["step"] == 6 for b in multi_batches)
    multi_items = [item for batch in multi_batches for item in batch["args"]["items"]]
    option_titles = [
        item for item in multi_items
        if item["type"] == "TEXT"
        and item["payload"]["position"]["y"] == 56
        and "Option " in str((item["payload"].get("data") or {}).get("content") or "")
    ]
    assert len(option_titles) == 2
    assert all(item["payload"]["data"]["fontSize"] == 36 for item in option_titles)
    assert all('text-align: center' in item["payload"]["data"]["content"] for item in option_titles)
    assert all(f'color: {COLORS["primary"]}' in item["payload"]["data"]["content"] for item in option_titles)
    assert multi_manifest["layout"]["KPI_TOP"] == 168
    assert multi_manifest["layout"]["KPI_TOP"] - (104 + round(18 * 1.3)) >= 40
    default_subheaders = [
        item for item in multi_items
        if item["type"] == "TEXT" and item["payload"]["position"]["y"] == 104
    ]
    assert len(default_subheaders) == 2
    default_content = [item["payload"]["data"]["content"] for item in default_subheaders]
    normalized_multi, normalized_multi_meta = normalize_input(sample)
    assert not normalized_multi_meta["errors"], normalized_multi_meta["errors"]
    expected_subheaders = []
    for i in range(2):
        expected = truncate_words(
            tradeoff(normalized_multi, i, multi_manifest["layout"]["diffTaskIds"]), 100
        )
        expected_subheaders.append(expected)
        assert any(expected in content for content in default_content)

    labeled = json.loads(json.dumps(sample))
    labeled["parameterLabels"] = ["All skills required", "Up to 20% missing skills allowed"]
    labeled_manifest, labeled_batches = compile_plan(labeled, "board-demo")
    assert not labeled_manifest["errors"], labeled_manifest["errors"]
    labeled_subheaders = [
        item for batch in labeled_batches for item in batch["args"]["items"]
        if item["type"] == "TEXT" and item["payload"]["position"]["y"] == 104
    ]
    labeled_content = [item["payload"]["data"]["content"] for item in labeled_subheaders]
    assert len(labeled_content) == 2
    assert any("All skills required" in content for content in labeled_content)
    assert any("Up to 20% missing skills allowed" in content for content in labeled_content)
    assert all(not any(default in content for default in expected_subheaders)
               for content in labeled_content)
    comparison_texts = [
        item for item in multi_items
        if item["type"] == "TEXT"
        and item["payload"]["position"]["x"] >= multi_manifest["layout"]["DX"]
        and any(marker in str((item["payload"].get("data") or {}).get("content") or "")
                for marker in ("What changes between options", "tasks differ between options", "100% fit"))
    ]
    assert comparison_texts
    assert all('text-align: center' in item["payload"]["data"]["content"] for item in comparison_texts)
    workload_legends = [
        item for item in multi_items
        if item["type"] == "TEXT"
        and "already assigned effort" in str((item["payload"].get("data") or {}).get("content") or "")
    ]
    assert len(workload_legends) == 2
    assert len({item["payload"]["position"]["y"] for item in workload_legends}) == 2
    assert any(
        item["type"] == "SHAPE"
        and item["payload"]["geometry"] == {"width": 80, "height": 6}
        and item["payload"]["data"]["style"]["fillColor"] == COLORS["blue"]
        for item in multi_items
    )
    with tempfile.TemporaryDirectory() as tmp:
        write_plan(manifest, batches, Path(tmp))
        assert (Path(tmp) / "manifest.json").exists()
        assert list((Path(tmp) / "batches").glob("*.json"))
    print("Self-test passed.")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, help="UTF-8 JSON input")
    parser.add_argument("--out", type=Path, help="output plan directory")
    parser.add_argument("--board-id", default="", help="Klaxoon board UUID for ready-to-send batch files")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    if not args.input or not args.out:
        parser.error("INPUT and --out are required unless --self-test is used")
    try:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError("input root must be a JSON object")
        manifest, batches = compile_plan(data, args.board_id)
        write_plan(manifest, batches, args.out)
        if manifest.get("errors"):
            for error in manifest["errors"]:
                print(f"ERROR: {error}", file=sys.stderr)
            return 2
        print(f'Compiled {manifest["itemCount"]} items into {len(batches)} batches.')
        print(str(args.out / "manifest.json"))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
