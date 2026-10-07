#!/usr/bin/env python3
"""Compile current Klaxoon staffing-board positions into Wrike assignment updates."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional


TASK_LINK_RE = re.compile(r"open\.htm\?[^\"'<>\s]*?id=(\d+)", re.IGNORECASE)
USER_ID_RE = re.compile(r"\bw:usr:(\d+)\b")
OPTION_RE = re.compile(r"^(?:option\s*)?([A-Z])$", re.IGNORECASE)


def extract_items(value: Any) -> list[dict[str, Any]]:
    """Extract board items from direct pages or common MCP result wrappers."""
    if isinstance(value, list):
        result: list[dict[str, Any]] = []
        for entry in value:
            result.extend(extract_items(entry))
        return result
    if not isinstance(value, dict):
        return []
    items = value.get("items")
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]
    for key in ("structuredContent", "data", "result"):
        nested = value.get(key)
        found = extract_items(nested)
        if found:
            return found
    return []


def flatten_shape(item: dict[str, Any]) -> Optional[dict[str, Any]]:
    if isinstance(item.get("item"), dict):
        item = item["item"]
    if str(item.get("type", "")).upper() != "SHAPE":
        return None
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    position = payload.get("position") if isinstance(payload.get("position"), dict) else item.get("position")
    geometry = payload.get("geometry") if isinstance(payload.get("geometry"), dict) else item.get("geometry")
    style = data.get("style") if isinstance(data.get("style"), dict) else item.get("style")
    content = data.get("content") if "content" in data else item.get("content")
    if not isinstance(position, dict) or not isinstance(geometry, dict):
        return None
    try:
        x, y = float(position.get("x")), float(position.get("y"))
        width, height = float(geometry.get("width")), float(geometry.get("height"))
        z = int(position.get("z", 0))
    except (TypeError, ValueError):
        return None
    return {
        "id": str(item.get("id") or ""), "x": x, "y": y, "z": z,
        "width": width, "height": height, "content": html.unescape(str(content or "")),
        "style": style if isinstance(style, dict) else {},
    }


def center(shape: dict[str, Any]) -> tuple[float, float]:
    return shape["x"] + shape["width"] / 2.0, shape["y"] + shape["height"] / 2.0


def contains(panel: dict[str, Any], shape: dict[str, Any]) -> bool:
    cx, cy = center(shape)
    return (panel["x"] <= cx <= panel["x"] + panel["width"]
            and panel["y"] <= cy <= panel["y"] + panel["height"])


def contains_horizontally(panel: dict[str, Any], shape: dict[str, Any]) -> bool:
    """Treat an option panel as a horizontal lane; task cards may overflow below it."""
    cx, _ = center(shape)
    return panel["x"] <= cx <= panel["x"] + panel["width"]


def panel_shapes(shapes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    panels = [shape for shape in shapes
              if shape["z"] == 0 and abs(shape["y"]) <= 2
              and shape["width"] >= 1000 and shape["height"] >= 500
              and not shape["content"].strip()]
    return sorted(panels, key=lambda shape: shape["x"])


def option_index(value: Any) -> Optional[int]:
    if value is None or not str(value).strip():
        return None
    match = OPTION_RE.fullmatch(str(value).strip())
    return ord(match.group(1).upper()) - ord("A") if match else -1


def compile_assignments(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    raw_items = extract_items(data.get("shapeResponses", []))
    expected_count = data.get("expectedShapeCount")
    if not isinstance(expected_count, int) or isinstance(expected_count, bool) or expected_count < 1:
        errors.append("expectedShapeCount must be the positive SHAPE total reported by the current board read.")

    shapes: list[dict[str, Any]] = []
    seen_item_ids: set[str] = set()
    for index, item in enumerate(raw_items, start=1):
        shape = flatten_shape(item)
        if shape is None:
            errors.append(f"Returned SHAPE item {index} has unreadable type, position, or geometry.")
            continue
        if not shape["id"]:
            errors.append(f"Returned SHAPE item {index} has no item id.")
        elif shape["id"] in seen_item_ids:
            errors.append(f'Duplicate returned SHAPE item id {shape["id"]!r}.')
        else:
            seen_item_ids.add(shape["id"])
        shapes.append(shape)
    if isinstance(expected_count, int) and not isinstance(expected_count, bool):
        if len(seen_item_ids) != expected_count:
            errors.append(
                f"Current board read is incomplete: expected {expected_count} unique SHAPE items "
                f"but received {len(seen_item_ids)}."
            )
    if not shapes:
        errors.append("No readable SHAPE items were found in shapeResponses.")
        return {"errors": errors}

    panels = panel_shapes(shapes)
    if not panels:
        return {"errors": ["No compiler-owned staffing option panels were found."]}

    requested = option_index(data.get("option"))
    if requested == -1:
        errors.append(f"Invalid option label {data.get('option')!r}; expected Option A, Option B, or Option C.")
    elif requested is None:
        if len(panels) == 1:
            requested = 0
        else:
            errors.append("The board contains multiple options; specify which option to apply.")
    elif requested >= len(panels):
        errors.append(f"Requested Option {chr(65 + requested)} is not present on this board.")
    if errors:
        return {"errors": errors, "optionCount": len(panels)}

    task_cards: list[dict[str, Any]] = []
    user_cards: list[dict[str, Any]] = []
    for shape in shapes:
        task_candidate = shape["z"] == 5 and abs(shape["width"] - 160) <= 2
        user_candidate = (shape["z"] == 1 and abs(shape["width"] - 160) <= 2
                          and abs(shape["height"] - 138) <= 2)
        if task_candidate:
            task_ids = TASK_LINK_RE.findall(shape["content"])
            if len(task_ids) != 1:
                errors.append(
                    f'Generated task card {shape["id"]!r} must contain exactly one Wrike task link; '
                    f"found {len(task_ids)}."
                )
                continue
            shape = dict(shape)
            shape["taskId"] = f"w:itm:{task_ids[0]}"
            task_cards.append(shape)
        elif user_candidate:
            user_ids = USER_ID_RE.findall(shape["content"])
            if len(user_ids) != 1:
                errors.append(
                    f'Generated assignee card {shape["id"]!r} must contain exactly one Wrike user id; '
                    f"found {len(user_ids)}."
                )
                continue
            shape = dict(shape)
            shape["userId"] = f"w:usr:{user_ids[0]}"
            user_cards.append(shape)

    for task in task_cards:
        if not any(contains_horizontally(panel, task) for panel in panels):
            errors.append(
                f'Task card {task["taskId"]} lies outside the horizontal span of every option.'
            )

    selected_panel = panels[requested]
    selected_users = [card for card in user_cards if contains(selected_panel, card)]
    selected_tasks = [card for card in task_cards if contains_horizontally(selected_panel, card)]
    if not selected_users:
        errors.append("The selected option contains no readable assignee cards.")
    if not selected_tasks:
        errors.append("The selected option contains no readable task cards.")

    seen_users: set[str] = set()
    for card in selected_users:
        if card["userId"] in seen_users:
            errors.append(f'Duplicate assignee card for {card["userId"]} in the selected option.')
        seen_users.add(card["userId"])

    ordered_users = sorted(selected_users, key=lambda user: center(user)[0])
    assignments: set[tuple[str, str]] = set()
    for task in selected_tasks:
        tx, _ = center(task)
        candidates: list[dict[str, Any]] = []
        if len(ordered_users) == 1:
            user = ordered_users[0]
            ux, _ = center(user)
            half_band = max(task["width"], user["width"]) * 1.5
            if ux - half_band <= tx <= ux + half_band:
                candidates.append(user)
        else:
            centers = [center(user)[0] for user in ordered_users]
            for index, user in enumerate(ordered_users):
                left = centers[index] - (centers[1] - centers[0]) / 2 if index == 0 else (centers[index - 1] + centers[index]) / 2 + 24
                right = centers[index] + (centers[-1] - centers[-2]) / 2 if index == len(centers) - 1 else (centers[index] + centers[index + 1]) / 2 - 24
                if left <= tx <= right:
                    candidates.append(user)
        if len(candidates) != 1:
            errors.append(f'Task card {task["taskId"]} is not clearly inside one assignee column.')
            continue
        owner = candidates[0]
        if task["y"] < owner["y"] + owner["height"] + 8:
            errors.append(f'Task card {task["taskId"]} is not positioned below its assignee card.')
            continue
        assignments.add((task["taskId"], owner["userId"]))

    if errors:
        return {"errors": errors, "optionCount": len(panels),
                "selectedOption": f"Option {chr(65 + requested)}"}

    ordered = sorted(assignments, key=lambda pair: (int(pair[1].split(":")[-1]), int(pair[0].split(":")[-1])))
    grouped: dict[str, list[str]] = defaultdict(list)
    for task_id, user_id in ordered:
        grouped[user_id].append(task_id)
    updates = [{"userId": user_id, "taskIds": task_ids}
               for user_id, task_ids in sorted(grouped.items(), key=lambda row: int(row[0].split(":")[-1]))]
    return {
        "errors": [], "optionCount": len(panels),
        "selectedOption": f"Option {chr(65 + requested)}",
        "taskCardCount": len(selected_tasks), "assigneeCardCount": len(selected_users),
        "assignments": [{"taskId": task_id, "userId": user_id} for task_id, user_id in ordered],
        "updates": updates,
    }


def write_plan(plan: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


def self_test() -> None:
    def shape(item_id: str, x: int, y: int, width: int, height: int, z: int,
              content: str = "") -> dict[str, Any]:
        return {"id": item_id, "type": "SHAPE", "position": {"x": x, "y": y, "z": z},
                "geometry": {"width": width, "height": height}, "content": content}

    items = [
        shape("panel-a", 0, 0, 2000, 2200, 0),
        shape("panel-b", 2060, 0, 2000, 2200, 0),
        shape("attention-a", 100, 376, 1760, 240, 1,
              '<h3>Partial match</h3><a href="https://www.wrike.com/open.htm?id=10">open in Wrike</a>'),
        shape("user-a1", 100, 700, 160, 138, 1, "<h4>Ada</h4><h6>w:usr:1</h6>"),
        shape("user-a2", 1700, 700, 160, 138, 1, "<h4>Grace</h4><h6>w:usr:2</h6>"),
        shape("task-a1", 110, 900, 160, 200, 5, '<a href="https://www.wrike.com/open.htm?id=10">Task 10</a>'),
        shape("task-a2", 1680, 900, 160, 200, 5, '<a href="https://www.wrike.com/open.htm?id=11">Task 11</a>'),
        shape("user-b1", 2160, 700, 160, 138, 1, "<h4>Ada</h4><h6>w:usr:1</h6>"),
        shape("task-b1", 2170, 900, 160, 200, 5, '<a href="https://www.wrike.com/open.htm?id=10">Task 10</a>'),
    ]
    wrapped = {"structuredContent": {"items": items}}
    plan = compile_assignments({"option": "Option A", "expectedShapeCount": len(items),
                                "shapeResponses": [wrapped]})
    assert not plan["errors"], plan["errors"]
    assert plan["taskCardCount"] == 2  # The attention link is not a task card.
    assert plan["assignments"] == [
        {"taskId": "w:itm:10", "userId": "w:usr:1"},
        {"taskId": "w:itm:11", "userId": "w:usr:2"},
    ]
    assert compile_assignments({"expectedShapeCount": len(items), "shapeResponses": [wrapped]})["errors"]
    single = {"items": [item for item in items if item["position"]["x"] < 2000]}
    single_plan = compile_assignments({"expectedShapeCount": len(single["items"]),
                                       "shapeResponses": [single]})
    assert not single_plan["errors"], single_plan["errors"]
    moved = json.loads(json.dumps(single))
    next(item for item in moved["items"] if item["id"] == "task-a1")["position"]["x"] = 1690
    next(item for item in moved["items"] if item["id"] == "task-a1")["position"]["y"] = 2300
    moved_plan = compile_assignments({"expectedShapeCount": len(moved["items"]),
                                      "shapeResponses": [moved]})
    assert not moved_plan["errors"], moved_plan["errors"]
    assert {tuple(row.values()) for row in moved_plan["assignments"]} == {
        ("w:itm:10", "w:usr:2"), ("w:itm:11", "w:usr:2")}
    below_second_panel = json.loads(json.dumps(items))
    next(item for item in below_second_panel if item["id"] == "task-b1")["position"]["y"] = 2300
    option_b = compile_assignments({"option": "Option B",
                                    "expectedShapeCount": len(below_second_panel),
                                    "shapeResponses": [{"items": below_second_panel}]})
    assert not option_b["errors"], option_b["errors"]
    assert option_b["assignments"] == [{"taskId": "w:itm:10", "userId": "w:usr:1"}]
    incomplete = compile_assignments({"expectedShapeCount": len(single["items"]) + 1,
                                      "shapeResponses": [single]})
    assert any("incomplete" in error for error in incomplete["errors"])
    missing_user_id = json.loads(json.dumps(single))
    next(item for item in missing_user_id["items"] if item["id"] == "user-a1")["content"] = "<h4>Ada</h4>"
    missing_plan = compile_assignments({"expectedShapeCount": len(missing_user_id["items"]),
                                        "shapeResponses": [missing_user_id]})
    assert any("exactly one Wrike user id" in error for error in missing_plan["errors"])
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "plan.json"
        write_plan(plan, path)
        assert json.loads(path.read_text(encoding="utf-8"))["selectedOption"] == "Option A"
    print("Assignment compiler self-test passed.")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, help="UTF-8 JSON input")
    parser.add_argument("--out", type=Path, help="output assignment-plan JSON")
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
        plan = compile_assignments(data)
        write_plan(plan, args.out)
        if plan.get("errors"):
            for error in plan["errors"]:
                print(f"ERROR: {error}", file=sys.stderr)
            return 2
        print(f'Compiled {len(plan["assignments"])} board assignments for {plan["selectedOption"]}.')
        print(str(args.out))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
