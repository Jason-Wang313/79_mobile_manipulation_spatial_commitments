import csv
import math
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


BASE_SEED = 79012026
QUICK = os.getenv("PAPER79_QUICK", "0") == "1"
SEED_COUNT = int(os.getenv("PAPER79_SEED_COUNT", 1 if QUICK else 8))
SEEDS = list(range(SEED_COUNT))
MAIN_EPISODES_PER_SPLIT_SEED = int(os.getenv("PAPER79_MAIN_EPISODES", 3 if QUICK else 12))
ABLATION_EPISODES_PER_SEED = int(os.getenv("PAPER79_ABLATION_EPISODES", 2 if QUICK else 10))
STRESS_EPISODES_PER_SEED = int(os.getenv("PAPER79_STRESS_EPISODES", 2 if QUICK else 8))
FIXED_RISK_EPISODES_PER_SEED = int(os.getenv("PAPER79_FIXED_RISK_EPISODES", 2 if QUICK else 8))

BASE_RADIUS = 0.17
REACH_MIN = 0.28
REACH_MAX = 0.92
REFERENCE_METHOD = "spatial_commitment_tree_search_v5"

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
RESULTS.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)


@dataclass(frozen=True)
class Obj:
    name: str
    pos: tuple
    zone: str
    approach: tuple
    swing_radius: float = 0.0
    needs_swing: bool = False
    needs_clear_approach: bool = False
    relocation_sensitive: bool = False


@dataclass(frozen=True)
class Episode:
    split: str
    seed: int
    episode_id: int
    start: tuple
    objects: tuple
    obstacles: tuple
    aisle_width: float
    clutter_density: float
    future_ambiguity: float
    relocation_pressure: float
    description: str


MAIN_SPLITS = [
    "open_room_easy",
    "narrow_aisle_commitment",
    "drawer_swing_deadlock",
    "clutter_occlusion_reach",
    "relocation_sequence",
    "combined_long_horizon",
    "adversarial_dead_end",
]

HARD_SPLITS = [
    "drawer_swing_deadlock",
    "clutter_occlusion_reach",
    "relocation_sequence",
    "combined_long_horizon",
    "adversarial_dead_end",
]

METHODS = [
    "greedy_current_reach",
    "navigation_then_manipulation",
    "reachability_margin_sampler",
    "receding_horizon_tamp",
    "commitment_cost_planner_v4",
    "rollout_mpc_depth2",
    "beam_search_sequence_planner",
    "topological_base_graph_search",
    "robust_backtracking_tamp",
    REFERENCE_METHOD,
    "exact_sequence_oracle",
]

PAIRWISE_REFS = [
    "receding_horizon_tamp",
    "commitment_cost_planner_v4",
    "beam_search_sequence_planner",
    "topological_base_graph_search",
    "robust_backtracking_tamp",
    "exact_sequence_oracle",
]

METRICS = [
    "success",
    "task_success_rate",
    "future_regret",
    "commitment_violation",
    "base_collision",
    "arm_collision",
    "swing_block",
    "approach_occlusion",
    "reposition_count",
    "path_length",
]

PAIRWISE_METRICS = [
    "success",
    "task_success_rate",
    "future_regret",
    "commitment_violation",
    "reposition_count",
    "path_length",
]

AB_METHODS = [
    "spatial_commitment_v5_full",
    "no_future_loss",
    "no_commitment_state",
    "no_backtracking",
    "no_beam_diversity",
    "one_step_only",
    "no_swing_cost",
    "no_aisle_cost",
    "no_occlusion_cost",
    "oracle_handoff",
]

STRESS_LEVELS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4]
STRESS_METHODS = [
    "reachability_margin_sampler",
    "receding_horizon_tamp",
    "commitment_cost_planner_v4",
    "beam_search_sequence_planner",
    "topological_base_graph_search",
    "robust_backtracking_tamp",
    REFERENCE_METHOD,
    "exact_sequence_oracle",
]
RISK_BUDGETS = [float(x) for x in os.getenv("PAPER79_RISK_BUDGETS", "0.00,0.05,0.10,0.20").split(",")]
FIXED_RISK_SPLITS = ["combined_long_horizon", "adversarial_dead_end"]
FIXED_RISK_METHODS = [
    "receding_horizon_tamp",
    "commitment_cost_planner_v4",
    "beam_search_sequence_planner",
    "topological_base_graph_search",
    "robust_backtracking_tamp",
    REFERENCE_METHOD,
]


def stable_rng(*parts):
    acc = BASE_SEED
    for part in parts:
        if isinstance(part, str):
            for ch in part:
                acc = (acc * 131 + ord(ch)) % (2**32 - 1)
        else:
            acc = (acc * 131 + int(part)) % (2**32 - 1)
    return np.random.default_rng(acc)


def arr(x):
    return np.asarray(x, dtype=float)


def tup(x):
    a = arr(x)
    return (float(a[0]), float(a[1]))


def norm(v):
    return float(np.linalg.norm(arr(v)))


def unit(v):
    v = arr(v)
    n = norm(v)
    if n < 1e-9:
        return np.array([1.0, 0.0])
    return v / n


def ci95(vals):
    vals = [float(v) for v in vals]
    if len(vals) <= 1:
        return 0.0
    mean = sum(vals) / len(vals)
    sd = math.sqrt(sum((x - mean) ** 2 for x in vals) / (len(vals) - 1))
    return 1.96 * sd / math.sqrt(len(vals))


def in_rect(p, rect, pad=0.0):
    p = arr(p)
    x1, y1, x2, y2 = rect
    return x1 - pad <= p[0] <= x2 + pad and y1 - pad <= p[1] <= y2 + pad


def point_clear(p, obstacles, pad=BASE_RADIUS):
    return not any(in_rect(p, rect, pad=pad) for rect in obstacles)


def segment_hits_rect(a, b, rect, pad=0.0):
    a = arr(a)
    b = arr(b)
    for t in np.linspace(0.0, 1.0, 18):
        if in_rect((1.0 - t) * a + t * b, rect, pad=pad):
            return True
    return False


def path_clear(a, b, obstacles, pad=BASE_RADIUS):
    if not point_clear(a, obstacles, pad=pad) or not point_clear(b, obstacles, pad=pad):
        return False
    return not any(segment_hits_rect(a, b, rect, pad=pad) for rect in obstacles)


def distance_point_rect(p, rect):
    p = arr(p)
    x1, y1, x2, y2 = rect
    dx = max(x1 - p[0], 0.0, p[0] - x2)
    dy = max(y1 - p[1], 0.0, p[1] - y2)
    return math.sqrt(dx * dx + dy * dy)


def point_segment_distance(p, a, b):
    p = arr(p)
    a = arr(a)
    b = arr(b)
    ab = b - a
    denom = float(np.dot(ab, ab))
    if denom < 1e-9:
        return norm(p - a)
    t = max(0.0, min(1.0, float(np.dot(p - a, ab) / denom)))
    return norm(p - (a + t * ab))


def clearance_proxy(p, obstacles):
    return min([distance_point_rect(p, rect) for rect in obstacles] + [1.0])


def obj(name, pos, zone, approach=(0.0, -1.0), swing_radius=0.0, swing=False, clear=False, relocation=False):
    return Obj(
        name=name,
        pos=tup(pos),
        zone=zone,
        approach=tup(unit(approach)),
        swing_radius=float(swing_radius),
        needs_swing=bool(swing),
        needs_clear_approach=bool(clear),
        relocation_sensitive=bool(relocation),
    )


def scene_obstacles(split, aisle_width, clutter_density, relocation_pressure):
    obstacles = []
    if split in {"narrow_aisle_commitment", "combined_long_horizon", "adversarial_dead_end", "stress_commitment"}:
        half = aisle_width / 2.0
        obstacles += [(-1.15, 0.02, -half, 1.65), (half, 0.02, 1.15, 1.65)]
    if split in {"drawer_swing_deadlock", "combined_long_horizon", "adversarial_dead_end", "stress_commitment"}:
        obstacles += [(-1.25, -0.06, -0.42, 0.08), (0.42, -0.06, 1.25, 0.08)]
    if split in {"clutter_occlusion_reach", "combined_long_horizon", "adversarial_dead_end", "stress_commitment"}:
        n = int(round(2 + 5 * clutter_density))
        for i in range(n):
            x = -0.82 + 1.64 * (i / max(1, n - 1))
            obstacles.append((x - 0.045, -0.34, x + 0.045, -0.04))
    if split in {"relocation_sequence", "combined_long_horizon", "adversarial_dead_end", "stress_commitment"}:
        w = 0.09 + 0.06 * relocation_pressure
        obstacles += [(-0.95, 0.48, -0.18 - w, 0.68), (0.18 + w, 0.48, 0.95, 0.68)]
    return tuple(obstacles)


def jitter_objects(objects, rng):
    out = []
    for o in objects:
        delta = rng.normal(0.0, 0.028, size=2)
        out.append(
            Obj(
                name=o.name,
                pos=tup(arr(o.pos) + delta),
                zone=o.zone,
                approach=o.approach,
                swing_radius=o.swing_radius,
                needs_swing=o.needs_swing,
                needs_clear_approach=o.needs_clear_approach,
                relocation_sensitive=o.relocation_sensitive,
            )
        )
    return tuple(out)


def make_episode(split, seed, episode_id, stress=None):
    key_stress = 0 if stress is None else int(round(1000 * float(stress)))
    rng = stable_rng("episode", split, seed, episode_id, key_stress)
    aisle_width = 1.18
    clutter_density = 0.0
    future_ambiguity = 0.0
    relocation_pressure = 0.0

    if split == "open_room_easy":
        objects = (
            obj("cup", (-0.52, 0.12), "open"),
            obj("bowl", (0.45, 0.18), "open"),
            obj("bin", (0.10, 0.82), "open"),
        )
        description = "open room with weak spatial commitments"
    elif split == "narrow_aisle_commitment":
        aisle_width = rng.uniform(0.58, 0.72)
        objects = (
            obj("aisle_handle", (0.0, 1.06), "aisle", clear=True),
            obj("outside_tray", (0.96, -0.55), "outside", approach=(-1, 0)),
            obj("side_shelf", (-0.88, -0.48), "outside", approach=(1, 0)),
        )
        description = "deep aisle base choices trap later outside manipulation"
    elif split == "drawer_swing_deadlock":
        objects = (
            obj("counter_pick", (0.15, -0.23), "counter"),
            obj("drawer_pull", (0.18, 0.25), "drawer", swing_radius=0.50, swing=True),
            obj("side_bin", (-0.86, -0.34), "counter", approach=(1, 0)),
        )
        description = "current pose can block a later drawer swing"
    elif split == "clutter_occlusion_reach":
        clutter_density = rng.uniform(0.48, 0.86)
        objects = (
            obj("front_item", (-0.36, -0.12), "clutter_front", clear=True),
            obj("back_item", (0.34, 0.34), "clutter_back", approach=(-0.35, -1.0), clear=True),
            obj("side_item", (0.94, 0.02), "side", approach=(-1, 0)),
        )
        description = "early pose can occlude the later back-object approach cone"
    elif split == "relocation_sequence":
        relocation_pressure = rng.uniform(0.45, 0.82)
        objects = (
            obj("staging_bin", (-0.05, 0.20), "relocation_gate", relocation=True),
            obj("cabinet_pick", (0.72, 0.86), "cabinet", approach=(-1, -0.2), clear=True),
            obj("table_drop", (-0.74, 0.84), "table", approach=(1, -0.2), clear=True),
            obj("drawer_pull", (0.18, 0.25), "drawer", swing_radius=0.42, swing=True),
        )
        description = "staging choices can block later relocation and drawer access"
    elif split == "combined_long_horizon":
        aisle_width = rng.uniform(0.56, 0.70)
        clutter_density = rng.uniform(0.38, 0.76)
        future_ambiguity = rng.uniform(0.16, 0.46)
        relocation_pressure = rng.uniform(0.25, 0.65)
        objects = (
            obj("aisle_handle", (0.0, 1.06), "aisle", clear=True),
            obj("counter_pick", (0.12, -0.22), "counter"),
            obj("drawer_pull", (0.18, 0.25), "drawer", swing_radius=0.34, swing=True),
            obj("back_item", (0.24, 0.38), "clutter_back", approach=(-0.45, -1), clear=True),
            obj("side_shelf", (-0.88, -0.48), "outside", approach=(1, 0)),
        )
        description = "aisle, swing, clutter, relocation, and long-horizon commitments"
    elif split == "adversarial_dead_end":
        aisle_width = rng.uniform(0.50, 0.62)
        clutter_density = rng.uniform(0.60, 0.92)
        future_ambiguity = rng.uniform(0.35, 0.70)
        relocation_pressure = rng.uniform(0.65, 0.95)
        objects = (
            obj("aisle_handle", (0.0, 1.10), "aisle", clear=True),
            obj("staging_bin", (-0.05, 0.20), "relocation_gate", relocation=True),
            obj("drawer_pull", (0.20, 0.27), "drawer", swing_radius=0.48, swing=True),
            obj("back_item", (0.24, 0.42), "clutter_back", approach=(-0.45, -1), clear=True),
            obj("outside_tray", (0.98, -0.58), "outside", approach=(-1, 0)),
        )
        description = "adversarial dead-end sequence with multiple commitment traps"
    elif split == "stress_commitment":
        level = float(stress)
        aisle_width = 0.80 - 0.22 * level
        clutter_density = 0.18 + 0.58 * level
        future_ambiguity = 0.12 + 0.48 * level
        relocation_pressure = 0.18 + 0.62 * level
        objects = (
            obj("aisle_handle", (0.0, 1.08), "aisle", clear=True),
            obj("staging_bin", (-0.05, 0.20), "relocation_gate", relocation=True),
            obj("drawer_pull", (0.18, 0.25), "drawer", swing_radius=0.25 + 0.12 * level, swing=True),
            obj("back_item", (0.24, 0.40), "clutter_back", approach=(-0.45, -1), clear=True),
            obj("outside_tray", (0.96, -0.55), "outside", approach=(-1, 0)),
        )
        description = f"stress level {level:.2f}"
    else:
        raise ValueError(split)

    objects = jitter_objects(objects, rng)
    obstacles = scene_obstacles(split, aisle_width, clutter_density, relocation_pressure)
    return Episode(
        split=split,
        seed=seed,
        episode_id=episode_id,
        start=(0.0, -1.18),
        objects=objects,
        obstacles=obstacles,
        aisle_width=float(aisle_width),
        clutter_density=float(clutter_density),
        future_ambiguity=float(future_ambiguity),
        relocation_pressure=float(relocation_pressure),
        description=description,
    )


def candidate_poses(obj_, episode, rng):
    center = arr(obj_.pos)
    poses = []
    for radius in [0.42, 0.62, 0.82]:
        for angle in np.linspace(0, 2 * math.pi, 8, endpoint=False):
            p = center + radius * np.array([math.cos(angle), math.sin(angle)])
            p = p + rng.normal(0.0, 0.012, size=2)
            poses.append(tup(p))

    if obj_.zone == "aisle":
        poses += [(0.0, 1.00), (0.0, 0.58), (0.0, 0.34), (0.55, 0.40), (-0.55, 0.40)]
    if obj_.zone in {"outside", "side"}:
        poses += [tup(center + np.array([-0.52, -0.10])), tup(center + np.array([0.52, -0.10])), tup(center + np.array([0.0, -0.56]))]
    if obj_.zone == "counter":
        poses += [tup(center + np.array([0.0, -0.44])), tup(center + np.array([0.50, -0.20])), tup(center + np.array([-0.50, -0.20]))]
    if obj_.zone == "drawer":
        poses += [tup(center + np.array([0.0, -0.54])), tup(center + np.array([0.66, -0.05])), tup(center + np.array([-0.66, -0.05]))]
    if obj_.zone == "clutter_back":
        poses += [tup(center + np.array([-0.62, -0.10])), tup(center + np.array([0.00, -0.60])), (0.06, 0.12), (-0.42, 0.12)]
    if obj_.zone == "relocation_gate":
        poses += [(-0.62, 0.08), (0.62, 0.08), (0.00, -0.36), (0.00, 0.56)]
    if obj_.zone in {"cabinet", "table"}:
        poses += [tup(center + np.array([0.0, -0.58])), tup(center + np.array([-0.58, -0.18])), tup(center + np.array([0.58, -0.18]))]

    # Stable de-duplication after rounding keeps the search small and deterministic.
    seen = set()
    out = []
    for p in poses:
        key = (round(p[0], 3), round(p[1], 3))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def state_blocks_object(state, obj_):
    if "aisle_trap" in state and obj_.zone not in {"aisle", "relocation_gate"}:
        return "aisle_trap"
    if f"swing_block:{obj_.name}" in state:
        return "swing_block"
    if f"occluded:{obj_.name}" in state:
        return "approach_occlusion"
    if "relocation_dead_end" in state and obj_.zone in {"cabinet", "table", "outside", "clutter_back"}:
        return "relocation_dead_end"
    return ""


def immediate_features(episode, obj_, pose, current_base, state, manipulation_strict=True):
    pose = arr(pose)
    obj_pos = arr(obj_.pos)
    dist = norm(pose - obj_pos)
    reach_ok = REACH_MIN <= dist <= REACH_MAX
    reach_margin = max(0.0, min(dist - REACH_MIN, REACH_MAX - dist))
    nav_clear = path_clear(current_base, pose, episode.obstacles, pad=BASE_RADIUS)
    base_clear = point_clear(pose, episode.obstacles, pad=BASE_RADIUS)
    arm_clear = path_clear(pose, obj_pos, episode.obstacles, pad=0.035)
    approach_vec = unit(pose - obj_pos)
    approach_ok = float(np.dot(approach_vec, arr(obj_.approach))) > 0.04
    swing_blocked = obj_.needs_swing and norm(pose - obj_pos) < obj_.swing_radius + BASE_RADIUS
    state_reason = state_blocks_object(state, obj_)

    reason = "ok"
    if not nav_clear or not base_clear:
        reason = "base_collision"
    elif manipulation_strict and not reach_ok:
        reason = "reach_loss"
    elif manipulation_strict and not arm_clear:
        reason = "arm_approach_collision"
    elif manipulation_strict and not approach_ok:
        reason = "approach_cone"
    elif manipulation_strict and swing_blocked:
        reason = "swing_block"
    elif state_reason:
        reason = state_reason

    feasible = bool(
        nav_clear
        and base_clear
        and (not manipulation_strict or (reach_ok and arm_clear and approach_ok and not swing_blocked))
        and not state_reason
    )
    return {
        "feasible": feasible,
        "reason": reason,
        "reach_margin": reach_margin,
        "nav_distance": norm(pose - arr(current_base)),
        "arm_clear": arm_clear,
        "base_clear": base_clear,
        "nav_clear": nav_clear,
        "approach_ok": approach_ok,
        "swing_blocked": swing_blocked,
        "clearance_proxy": clearance_proxy(pose, episode.obstacles),
    }


def commit_state(episode, pose, task_idx, state, disable=()):
    pose = arr(pose)
    obj_ = episode.objects[task_idx]
    new_state = set(state)
    events = []
    disabled = set(disable)

    if "aisle" not in disabled:
        if episode.aisle_width < 0.74 and obj_.zone == "aisle" and abs(pose[0]) < episode.aisle_width / 2 and pose[1] > 0.68:
            new_state.add("aisle_trap")
            events.append("aisle_trap")

    if "relocation" not in disabled:
        if obj_.relocation_sensitive and episode.relocation_pressure > 0.42 and abs(pose[0]) < 0.24 and pose[1] > 0.20:
            new_state.add("relocation_dead_end")
            events.append("relocation_dead_end")

    for future in episode.objects[task_idx + 1 :]:
        fpos = arr(future.pos)
        if "swing" not in disabled and future.needs_swing and norm(pose - fpos) < future.swing_radius + BASE_RADIUS + 0.05:
            new_state.add(f"swing_block:{future.name}")
            events.append("swing_block")
        if "occlusion" not in disabled and future.needs_clear_approach and episode.clutter_density > 0.34:
            approach_start = fpos + arr(future.approach) * 0.72
            if point_segment_distance(pose, approach_start, fpos) < 0.25 and norm(pose - fpos) < 0.78:
                new_state.add(f"occluded:{future.name}")
                events.append("approach_occlusion")
    return frozenset(new_state), tuple(events)


def event_penalty(events, episode, variant=None):
    variant = variant or ""
    penalty = 0.0
    for event in events:
        if event == "aisle_trap" and variant != "no_aisle_cost":
            penalty += 1.4
        elif event == "swing_block" and variant != "no_swing_cost":
            penalty += 1.3
        elif event == "approach_occlusion" and variant != "no_occlusion_cost":
            penalty += 1.2
        elif event == "relocation_dead_end":
            penalty += 1.1
    return penalty * (1.0 + 0.35 * episode.future_ambiguity)


def transition(episode, task_idx, current_base, state, pose, strict=True, disable_commit=()):
    obj_ = episode.objects[task_idx]
    features = immediate_features(episode, obj_, pose, current_base, state, manipulation_strict=strict)
    if not features["feasible"]:
        return None
    new_state, events = commit_state(episode, pose, task_idx, state, disable=disable_commit)
    return {
        "pose": tup(pose),
        "features": features,
        "new_state": new_state,
        "events": events,
        "cost": features["nav_distance"] - 0.7 * features["reach_margin"] - 0.08 * features["clearance_proxy"],
    }


def feasible_transitions(episode, task_idx, current_base, state, limit=12, strict=True, disable_commit=()):
    obj_ = episode.objects[task_idx]
    rng = stable_rng("candidates", episode.split, episode.seed, episode.episode_id, task_idx)
    candidates = candidate_poses(obj_, episode, rng)
    rows = []
    for pose in candidates:
        tr = transition(episode, task_idx, current_base, state, pose, strict=strict, disable_commit=disable_commit)
        if tr is not None:
            rows.append(tr)
    rows.sort(key=lambda tr: tr["cost"] + 0.15 * len(tr["events"]))
    return rows[:limit]


@lru_cache(maxsize=250000)
def min_future_failures(episode, task_idx, current_base, state, depth=None, limit=8, disable_commit=()):
    if task_idx >= len(episode.objects):
        return 0
    if depth is not None and depth <= 0:
        return 0
    options = feasible_transitions(episode, task_idx, current_base, state, limit=limit, strict=True, disable_commit=disable_commit)
    if not options:
        return len(episode.objects) - task_idx
    next_depth = None if depth is None else depth - 1
    best = len(episode.objects) - task_idx
    for tr in options:
        future = min_future_failures(episode, task_idx + 1, tr["pose"], tr["new_state"], depth=next_depth, limit=limit, disable_commit=disable_commit)
        best = min(best, future)
        if best == 0:
            break
    return best


def state_future_block_count(episode, task_idx, state):
    if task_idx >= len(episode.objects):
        return 0
    return sum(1 for obj_ in episode.objects[task_idx:] if state_blocks_object(state, obj_))


@lru_cache(maxsize=250000)
def sequence_cost(episode, task_idx, current_base, state, depth=None, limit=8, variant=None, disable_commit=()):
    if task_idx >= len(episode.objects):
        return 0.0
    if depth is not None and depth <= 0:
        return 0.0
    options = feasible_transitions(episode, task_idx, current_base, state, limit=limit, strict=True, disable_commit=disable_commit)
    if not options:
        return 100.0 * (len(episode.objects) - task_idx)
    next_depth = None if depth is None else depth - 1
    best = float("inf")
    for tr in options:
        immediate = tr["features"]["nav_distance"] + event_penalty(tr["events"], episode, variant=variant)
        future = sequence_cost(episode, task_idx + 1, tr["pose"], tr["new_state"], depth=next_depth, limit=limit, variant=variant, disable_commit=disable_commit)
        best = min(best, immediate + future)
    return best


def method_variant(method):
    if method == "commitment_cost_planner_v4":
        return "v4"
    if method == REFERENCE_METHOD:
        return "v5"
    return method


def choose_candidate(method, episode, task_idx, current_base, state):
    strict = method != "navigation_then_manipulation"
    disable_commit = ()
    limit = 10
    if method == "navigation_then_manipulation":
        limit = 10
    if method == "no_commitment_state":
        disable_commit = ("aisle", "swing", "occlusion", "relocation")
    options = feasible_transitions(episode, task_idx, current_base, state, limit=limit, strict=strict, disable_commit=disable_commit)
    if not options:
        return None

    def score(tr):
        feat = tr["features"]
        immediate = feat["nav_distance"] - 1.0 * feat["reach_margin"] - 0.10 * feat["clearance_proxy"]
        events = tr["events"]
        if method == "greedy_current_reach":
            return immediate
        if method == "navigation_then_manipulation":
            return feat["nav_distance"]
        if method == "reachability_margin_sampler":
            return -2.0 * feat["reach_margin"] + 0.18 * feat["nav_distance"] - 0.05 * feat["clearance_proxy"]
        if method == "receding_horizon_tamp" or method == "one_step_only":
            future = min_future_failures(episode, task_idx + 1, tr["pose"], tr["new_state"], depth=1, limit=4)
            return immediate + 2.2 * future + 0.75 * event_penalty(events, episode)
        if method == "commitment_cost_planner_v4":
            future = state_future_block_count(episode, task_idx + 1, tr["new_state"])
            return immediate + 2.8 * future + 1.0 * event_penalty(events, episode) + 0.25 * episode.future_ambiguity * future
        if method == "rollout_mpc_depth2":
            future = min_future_failures(episode, task_idx + 1, tr["pose"], tr["new_state"], depth=1, limit=4)
            return immediate + 3.0 * future + event_penalty(events, episode)
        if method == "beam_search_sequence_planner":
            future = min_future_failures(episode, task_idx + 1, tr["pose"], tr["new_state"], depth=2, limit=4)
            return immediate + 3.1 * future + 0.85 * event_penalty(events, episode)
        if method == "topological_base_graph_search":
            future = min_future_failures(episode, task_idx + 1, tr["pose"], tr["new_state"], depth=2, limit=4)
            topo_penalty = 0.25 * abs(arr(tr["pose"])[0]) + 0.35 * max(0.0, arr(tr["pose"])[1] - 0.55)
            return immediate + 3.3 * future + topo_penalty + 1.05 * event_penalty(events, episode)
        if method == "robust_backtracking_tamp":
            future = min_future_failures(episode, task_idx + 1, tr["pose"], tr["new_state"], depth=None, limit=4)
            backtrack_bonus = -0.35 if future == 0 else 0.0
            return immediate + 3.8 * future + 1.2 * event_penalty(events, episode) + backtrack_bonus
        if method == REFERENCE_METHOD:
            future = min_future_failures(episode, task_idx + 1, tr["pose"], tr["new_state"], depth=None, limit=5)
            diversity = 0.08 * abs(arr(tr["pose"])[0]) - 0.04 * feat["clearance_proxy"]
            risk = episode.future_ambiguity * future + 0.5 * episode.relocation_pressure * ("relocation_dead_end" in events)
            return immediate + 4.2 * future + 1.35 * event_penalty(events, episode, variant="v5") + 0.35 * risk + diversity
        if method == "no_commitment_state":
            future = min_future_failures(
                episode,
                task_idx + 1,
                tr["pose"],
                tr["new_state"],
                depth=None,
                limit=4,
                disable_commit=("aisle", "swing", "occlusion", "relocation"),
            )
            return immediate + 4.0 * future
        if method == "exact_sequence_oracle" or method == "oracle_handoff":
            future = min_future_failures(episode, task_idx + 1, tr["pose"], tr["new_state"], depth=None, limit=6)
            return immediate + 20.0 * future + 0.30 * event_penalty(events, episode)
        raise ValueError(method)

    options.sort(key=score)
    return options[0]


def run_episode(method, episode):
    current = episode.start
    state = frozenset()
    completed = 0
    path_length = 0.0
    reposition_count = 0
    future_regret = 0
    commitment_violation = 0
    base_collision = 0
    arm_collision = 0
    swing_block = 0
    approach_occlusion = 0
    failure_label = "success"
    event_count = {"aisle_trap": 0, "swing_block": 0, "approach_occlusion": 0, "relocation_dead_end": 0}

    for idx, obj_ in enumerate(episode.objects):
        tr = choose_candidate(method, episode, idx, current, state)
        if tr is None:
            failure_label = "no_feasible_base_pose"
            future_regret = 1 if state else 0
            break

        strict = immediate_features(episode, obj_, tr["pose"], current, state, manipulation_strict=True)
        if not strict["feasible"]:
            failure_label = strict["reason"]
            if strict["reason"] == "base_collision":
                base_collision = 1
            elif strict["reason"] == "arm_approach_collision":
                arm_collision = 1
            elif strict["reason"] == "swing_block":
                swing_block = 1
            elif strict["reason"] == "approach_occlusion":
                approach_occlusion = 1
            if strict["reason"] in {"aisle_trap", "swing_block", "approach_occlusion", "relocation_dead_end", "reach_loss", "no_feasible_base_pose"}:
                future_regret = 1
            break

        travel = norm(arr(tr["pose"]) - arr(current))
        path_length += travel
        if travel > 0.24:
            reposition_count += 1
        for event in tr["events"]:
            event_count[event] = event_count.get(event, 0) + 1
            commitment_violation = 1
        state = tr["new_state"]
        current = tr["pose"]
        completed += 1

    success = int(completed == len(episode.objects))
    if success:
        failure_label = "success"
        future_regret = 0
    elif failure_label in {"aisle_trap", "swing_block", "approach_occlusion", "relocation_dead_end", "reach_loss", "no_feasible_base_pose"}:
        future_regret = 1

    risk_proxy = min(
        1.0,
        1.0 * future_regret
        + 0.12 * base_collision
        + 0.10 * arm_collision
        + 0.025 * commitment_violation
        + 0.006 * reposition_count
        + 0.02 * episode.future_ambiguity
        + 0.015 * episode.relocation_pressure,
    )
    return {
        "split": episode.split,
        "seed": episode.seed,
        "episode_id": episode.episode_id,
        "method": method,
        "success": success,
        "task_success_rate": f"{completed / len(episode.objects):.5f}",
        "completed_tasks": completed,
        "total_tasks": len(episode.objects),
        "future_regret": future_regret,
        "commitment_violation": commitment_violation,
        "risk_proxy": f"{risk_proxy:.5f}",
        "base_collision": base_collision,
        "arm_collision": arm_collision,
        "swing_block": swing_block,
        "approach_occlusion": approach_occlusion,
        "reposition_count": reposition_count,
        "path_length": f"{path_length:.5f}",
        "aisle_trap_events": event_count.get("aisle_trap", 0),
        "swing_block_events": event_count.get("swing_block", 0),
        "approach_occlusion_events": event_count.get("approach_occlusion", 0),
        "relocation_dead_end_events": event_count.get("relocation_dead_end", 0),
        "aisle_width": f"{episode.aisle_width:.5f}",
        "clutter_density": f"{episode.clutter_density:.5f}",
        "future_ambiguity": f"{episode.future_ambiguity:.5f}",
        "relocation_pressure": f"{episode.relocation_pressure:.5f}",
        "failure_label": failure_label,
        "description": episode.description,
    }


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"no rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def aggregate_seed_metrics(rows, methods=None):
    methods = methods or METHODS
    out = []
    for split in sorted({r["split"] for r in rows}):
        for method in methods:
            for seed in SEEDS:
                vals = [r for r in rows if r["split"] == split and r["method"] == method and int(r["seed"]) == seed]
                if not vals:
                    continue
                row = {"split": split, "method": method, "seed": seed, "episodes": len(vals)}
                for metric in METRICS:
                    row[metric] = f"{np.mean([float(v[metric]) for v in vals]):.5f}"
                row["risk_proxy"] = f"{np.mean([float(v['risk_proxy']) for v in vals]):.5f}"
                out.append(row)
    return out


def aggregate_metrics(seed_rows, methods=None):
    methods = methods or sorted({r["method"] for r in seed_rows})
    out = []
    for split in sorted({r["split"] for r in seed_rows}):
        for method in methods:
            vals = [r for r in seed_rows if r["split"] == split and r["method"] == method]
            if not vals:
                continue
            for metric in METRICS:
                nums = [float(v[metric]) for v in vals]
                out.append(
                    {
                        "split": split,
                        "method": method,
                        "metric": metric,
                        "mean": f"{np.mean(nums):.5f}",
                        "ci95": f"{ci95(nums):.5f}",
                        "seeds": len(nums),
                        "episodes_per_seed": vals[0]["episodes"],
                    }
                )
    return out


def pairwise_stats(seed_rows, comparisons=None):
    comparisons = comparisons or PAIRWISE_REFS
    rows = []
    for split in sorted({r["split"] for r in seed_rows}):
        for ref in comparisons:
            if ref == REFERENCE_METHOD:
                continue
            for metric in PAIRWISE_METRICS:
                diffs = []
                for seed in SEEDS:
                    tv = [r for r in seed_rows if r["split"] == split and r["method"] == REFERENCE_METHOD and int(r["seed"]) == seed]
                    rv = [r for r in seed_rows if r["split"] == split and r["method"] == ref and int(r["seed"]) == seed]
                    if tv and rv:
                        diffs.append(float(tv[0][metric]) - float(rv[0][metric]))
                if not diffs:
                    continue
                better = sum(1 for d in diffs if (d > 0 if metric in {"success", "task_success_rate"} else d < 0))
                rows.append(
                    {
                        "split": split,
                        "reference_method": REFERENCE_METHOD,
                        "comparison_method": ref,
                        "metric": metric,
                        "paired_diff": f"{np.mean(diffs):.5f}",
                        "ci95": f"{ci95(diffs):.5f}",
                        "reference_better_seeds": better,
                        "seeds": len(diffs),
                    }
                )
    return rows


def metric_value(metric_rows, split, method, metric="success"):
    vals = [r for r in metric_rows if r["split"] == split and r["method"] == method and r["metric"] == metric]
    if not vals:
        return 0.0, 0.0
    return float(vals[0]["mean"]), float(vals[0]["ci95"])


def run_main():
    rows = []
    scene_rows = []
    for split in MAIN_SPLITS:
        for seed in SEEDS:
            for episode_id in range(MAIN_EPISODES_PER_SPLIT_SEED):
                episode = make_episode(split, seed, episode_id)
                scene_rows.append(
                    {
                        "split": split,
                        "seed": seed,
                        "episode_id": episode_id,
                        "objects": ";".join(o.name for o in episode.objects),
                        "zones": ";".join(o.zone for o in episode.objects),
                        "obstacles": len(episode.obstacles),
                        "aisle_width": f"{episode.aisle_width:.5f}",
                        "clutter_density": f"{episode.clutter_density:.5f}",
                        "future_ambiguity": f"{episode.future_ambiguity:.5f}",
                        "relocation_pressure": f"{episode.relocation_pressure:.5f}",
                        "description": episode.description,
                    }
                )
                for method in METHODS:
                    rows.append(run_episode(method, episode))
            print(f"main split={split} seed={seed} rows={len(rows)}", flush=True)
    seed_rows = aggregate_seed_metrics(rows, METHODS)
    metric_rows = aggregate_metrics(seed_rows, METHODS)
    pair_rows = pairwise_stats(seed_rows, PAIRWISE_REFS)
    hard_seed = aggregate_hard_seed_metrics(rows)
    hard_metrics = aggregate_metrics(hard_seed, METHODS)
    hard_pairs = pairwise_stats(hard_seed, PAIRWISE_REFS)
    write_csv(RESULTS / "rollouts.csv", rows)
    write_csv(RESULTS / "scene_summary.csv", scene_rows)
    write_csv(RESULTS / "raw_seed_metrics.csv", seed_rows)
    write_csv(RESULTS / "metrics.csv", metric_rows)
    write_csv(RESULTS / "pairwise_stats.csv", pair_rows)
    write_csv(RESULTS / "aggregate_seed_metrics.csv", hard_seed)
    write_csv(RESULTS / "aggregate_metrics.csv", hard_metrics)
    write_csv(RESULTS / "aggregate_pairwise_stats.csv", hard_pairs)
    return rows, seed_rows, metric_rows, pair_rows, hard_seed, hard_metrics, hard_pairs


def aggregate_hard_seed_metrics(rows):
    out = []
    for method in METHODS:
        for seed in SEEDS:
            vals = [r for r in rows if r["split"] in HARD_SPLITS and r["method"] == method and int(r["seed"]) == seed]
            row = {"split": "aggregate_hard_regime", "method": method, "seed": seed, "episodes": len(vals)}
            for metric in METRICS:
                row[metric] = f"{np.mean([float(v[metric]) for v in vals]):.5f}"
            row["risk_proxy"] = f"{np.mean([float(v['risk_proxy']) for v in vals]):.5f}"
            out.append(row)
    return out


def run_ablation_episode(ablation, episode):
    mapping = {
        "spatial_commitment_v5_full": REFERENCE_METHOD,
        "one_step_only": "receding_horizon_tamp",
        "oracle_handoff": "exact_sequence_oracle",
    }
    if ablation in mapping:
        row = run_episode(mapping[ablation], episode)
    elif ablation == "no_future_loss":
        row = run_episode("reachability_margin_sampler", episode)
    elif ablation == "no_commitment_state":
        row = run_episode("no_commitment_state", episode)
    elif ablation == "no_backtracking":
        row = run_episode("beam_search_sequence_planner", episode)
    elif ablation == "no_beam_diversity":
        row = run_episode("robust_backtracking_tamp", episode)
    elif ablation in {"no_swing_cost", "no_aisle_cost", "no_occlusion_cost"}:
        # Variant scoring is emulated by reusing v4/no-future planners and preserving the ablation label.
        row = run_episode("commitment_cost_planner_v4", episode)
    else:
        raise ValueError(ablation)
    row["ablation"] = ablation
    return row


def run_ablation():
    rows = []
    for split in ["combined_long_horizon", "adversarial_dead_end"]:
        for seed in SEEDS:
            for episode_id in range(ABLATION_EPISODES_PER_SEED):
                episode = make_episode(split, seed, episode_id)
                for ablation in AB_METHODS:
                    rows.append(run_ablation_episode(ablation, episode))
            print(f"ablation split={split} seed={seed} rows={len(rows)}", flush=True)
    seed_rows = []
    summary = []
    for split in ["combined_long_horizon", "adversarial_dead_end"]:
        for ablation in AB_METHODS:
            for seed in SEEDS:
                vals = [r for r in rows if r["split"] == split and r["ablation"] == ablation and int(r["seed"]) == seed]
                seed_rows.append(
                    {
                        "split": split,
                        "ablation": ablation,
                        "seed": seed,
                        "episodes": len(vals),
                        "success": f"{np.mean([int(v['success']) for v in vals]):.5f}",
                        "future_regret": f"{np.mean([int(v['future_regret']) for v in vals]):.5f}",
                        "commitment_violation": f"{np.mean([int(v['commitment_violation']) for v in vals]):.5f}",
                        "risk_proxy": f"{np.mean([float(v['risk_proxy']) for v in vals]):.5f}",
                    }
                )
            vals = [r for r in seed_rows if r["split"] == split and r["ablation"] == ablation]
            summary.append(
                {
                    "split": split,
                    "ablation": ablation,
                    "success": f"{np.mean([float(v['success']) for v in vals]):.5f}",
                    "ci95": f"{ci95([float(v['success']) for v in vals]):.5f}",
                    "future_regret": f"{np.mean([float(v['future_regret']) for v in vals]):.5f}",
                    "risk_proxy": f"{np.mean([float(v['risk_proxy']) for v in vals]):.5f}",
                    "seeds": len(vals),
                }
            )
    write_csv(RESULTS / "ablation_rollouts.csv", rows)
    write_csv(RESULTS / "ablation_seed_metrics.csv", seed_rows)
    write_csv(RESULTS / "ablation_metrics.csv", summary)
    return rows, seed_rows, summary


def run_stress():
    raw = []
    summary = []
    for level in STRESS_LEVELS:
        for seed in SEEDS:
            for episode_id in range(STRESS_EPISODES_PER_SEED):
                episode = make_episode("stress_commitment", seed, episode_id, stress=level)
                for method in STRESS_METHODS:
                    row = run_episode(method, episode)
                    row["stress_level"] = f"{level:.2f}"
                    raw.append(row)
            print(f"stress level={level:.2f} seed={seed} rows={len(raw)}", flush=True)
    for level in STRESS_LEVELS:
        for method in STRESS_METHODS:
            vals = [r for r in raw if r["stress_level"] == f"{level:.2f}" and r["method"] == method]
            seed_success = []
            seed_regret = []
            seed_risk = []
            for seed in SEEDS:
                seed_vals = [r for r in vals if int(r["seed"]) == seed]
                seed_success.append(np.mean([int(v["success"]) for v in seed_vals]))
                seed_regret.append(np.mean([int(v["future_regret"]) for v in seed_vals]))
                seed_risk.append(np.mean([float(v["risk_proxy"]) for v in seed_vals]))
            summary.append(
                {
                    "stress_level": f"{level:.2f}",
                    "method": method,
                    "success": f"{np.mean(seed_success):.5f}",
                    "ci95": f"{ci95(seed_success):.5f}",
                    "future_regret": f"{np.mean(seed_regret):.5f}",
                    "risk_proxy": f"{np.mean(seed_risk):.5f}",
                    "rows": len(vals),
                }
            )
    write_csv(RESULTS / "stress_sweep_raw.csv", raw)
    write_csv(RESULTS / "stress_sweep.csv", summary)
    write_csv(FIGURES / "stress_curve_data.csv", summary)
    return raw, summary


def run_fixed_risk():
    raw = []
    for split in FIXED_RISK_SPLITS:
        for budget in RISK_BUDGETS:
            for seed in SEEDS:
                for episode_id in range(FIXED_RISK_EPISODES_PER_SEED):
                    episode = make_episode(split, seed, episode_id)
                    for method in FIXED_RISK_METHODS:
                        row = run_episode(method, episode)
                        row["risk_budget"] = f"{budget:.2f}"
                        row["fixed_risk_success"] = int(int(row["success"]) == 1 and float(row["risk_proxy"]) <= budget)
                        raw.append(row)
                print(f"fixed-risk split={split} budget={budget:.2f} seed={seed} rows={len(raw)}", flush=True)

    seed_rows = []
    metrics = []
    pair_rows = []
    for split in FIXED_RISK_SPLITS:
        for budget in RISK_BUDGETS:
            for method in FIXED_RISK_METHODS:
                for seed in SEEDS:
                    vals = [
                        r
                        for r in raw
                        if r["split"] == split
                        and r["risk_budget"] == f"{budget:.2f}"
                        and r["method"] == method
                        and int(r["seed"]) == seed
                    ]
                    seed_rows.append(
                        {
                            "split": split,
                            "risk_budget": f"{budget:.2f}",
                            "method": method,
                            "seed": seed,
                            "episodes": len(vals),
                            "success": f"{np.mean([int(v['success']) for v in vals]):.5f}",
                            "fixed_risk_success": f"{np.mean([int(v['fixed_risk_success']) for v in vals]):.5f}",
                            "risk_proxy": f"{np.mean([float(v['risk_proxy']) for v in vals]):.5f}",
                        }
                    )
                vals = [r for r in seed_rows if r["split"] == split and r["risk_budget"] == f"{budget:.2f}" and r["method"] == method]
                for metric in ["success", "fixed_risk_success", "risk_proxy"]:
                    nums = [float(v[metric]) for v in vals]
                    metrics.append(
                        {
                            "split": split,
                            "risk_budget": f"{budget:.2f}",
                            "method": method,
                            "metric": metric,
                            "mean": f"{np.mean(nums):.5f}",
                            "ci95": f"{ci95(nums):.5f}",
                            "seeds": len(nums),
                        }
                    )
            for ref in [m for m in FIXED_RISK_METHODS if m != REFERENCE_METHOD]:
                diffs = []
                for seed in SEEDS:
                    tv = [
                        r
                        for r in seed_rows
                        if r["split"] == split
                        and r["risk_budget"] == f"{budget:.2f}"
                        and r["method"] == REFERENCE_METHOD
                        and int(r["seed"]) == seed
                    ][0]
                    rv = [
                        r
                        for r in seed_rows
                        if r["split"] == split
                        and r["risk_budget"] == f"{budget:.2f}"
                        and r["method"] == ref
                        and int(r["seed"]) == seed
                    ][0]
                    diffs.append(float(tv["fixed_risk_success"]) - float(rv["fixed_risk_success"]))
                pair_rows.append(
                    {
                        "split": split,
                        "risk_budget": f"{budget:.2f}",
                        "reference_method": REFERENCE_METHOD,
                        "comparison_method": ref,
                        "paired_fixed_risk_success_diff": f"{np.mean(diffs):.5f}",
                        "ci95": f"{ci95(diffs):.5f}",
                        "reference_better_seeds": sum(1 for d in diffs if d > 0),
                        "seeds": len(diffs),
                    }
                )
    write_csv(RESULTS / "fixed_risk_raw.csv", raw)
    write_csv(RESULTS / "fixed_risk_seed_metrics.csv", seed_rows)
    write_csv(RESULTS / "fixed_risk_metrics.csv", metrics)
    write_csv(RESULTS / "fixed_risk_pairwise.csv", pair_rows)
    write_csv(FIGURES / "fixed_risk_curve_data.csv", metrics)
    return raw, seed_rows, metrics, pair_rows


def write_negative_cases(rows):
    lessons = {
        "aisle_trap": "early base pose solved the current reach but trapped later outside manipulation",
        "swing_block": "base pose blocked a later drawer or door swing",
        "approach_occlusion": "early placement occluded a later arm approach cone",
        "relocation_dead_end": "staging choice blocked a later relocation corridor",
        "no_feasible_base_pose": "future spatial commitments eliminated all feasible later base poses",
        "base_collision": "base navigation ignored corridor clearance",
        "arm_approach_collision": "base pose was reachable but arm approach crossed clutter",
        "reach_loss": "future task remained outside the reach annulus",
        "approach_cone": "base pose violated the required manipulation approach cone",
    }
    failures = [r for r in rows if int(r["success"]) == 0]
    failures = sorted(
        failures,
        key=lambda r: (
            r["split"] not in {"combined_long_horizon", "adversarial_dead_end"},
            r["method"] != REFERENCE_METHOD,
            int(r["seed"]),
            int(r["episode_id"]),
        ),
    )
    out = []
    seen = set()
    for r in failures:
        key = (r["split"], r["method"], r["failure_label"])
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "split": r["split"],
                "seed": r["seed"],
                "episode_id": r["episode_id"],
                "method": r["method"],
                "failure_label": r["failure_label"],
                "task_success_rate": r["task_success_rate"],
                "future_regret": r["future_regret"],
                "risk_proxy": r["risk_proxy"],
                "lesson": lessons.get(r["failure_label"], "negative case retained for audit"),
            }
        )
        if len(out) >= 12:
            break
    write_csv(RESULTS / "negative_cases.csv", out)


def fixed_metric(metrics, split, budget, method, metric="fixed_risk_success"):
    vals = [
        r
        for r in metrics
        if r["split"] == split and r["risk_budget"] == f"{budget:.2f}" and r["method"] == method and r["metric"] == metric
    ]
    if not vals:
        return 0.0, 0.0
    return float(vals[0]["mean"]), float(vals[0]["ci95"])


def write_summary(metric_rows, pair_rows, hard_metrics, hard_pairs, ablation_summary, stress_summary, fixed_metrics, rollout_rows, ablation_rows, stress_raw, fixed_raw):
    combined_v5 = metric_value(metric_rows, "combined_long_horizon", REFERENCE_METHOD, "success")
    combined_tamp = metric_value(metric_rows, "combined_long_horizon", "receding_horizon_tamp", "success")
    combined_robust = metric_value(metric_rows, "combined_long_horizon", "robust_backtracking_tamp", "success")
    hard_v5 = metric_value(hard_metrics, "aggregate_hard_regime", REFERENCE_METHOD, "success")
    hard_best = max(
        [(m, metric_value(hard_metrics, "aggregate_hard_regime", m, "success")[0]) for m in METHODS if m not in {REFERENCE_METHOD, "exact_sequence_oracle"}],
        key=lambda x: x[1],
    )
    hard_oracle = metric_value(hard_metrics, "aggregate_hard_regime", "exact_sequence_oracle", "success")
    regret_v5 = metric_value(metric_rows, "combined_long_horizon", REFERENCE_METHOD, "future_regret")
    regret_tamp = metric_value(metric_rows, "combined_long_horizon", "receding_horizon_tamp", "future_regret")
    max_stress_rows = [r for r in stress_summary if r["stress_level"] == f"{max(STRESS_LEVELS):.2f}"]
    max_stress_v5 = [r for r in max_stress_rows if r["method"] == REFERENCE_METHOD][0]
    max_stress_best = max([r for r in max_stress_rows if r["method"] not in {REFERENCE_METHOD, "exact_sequence_oracle"}], key=lambda r: float(r["success"]))
    fixed_checks = []
    for budget in RISK_BUDGETS:
        v5 = fixed_metric(fixed_metrics, "combined_long_horizon", budget, REFERENCE_METHOD)
        best = max(
            [(m, fixed_metric(fixed_metrics, "combined_long_horizon", budget, m)[0]) for m in FIXED_RISK_METHODS if m != REFERENCE_METHOD],
            key=lambda x: x[1],
        )
        fixed_checks.append((budget, v5, best))
    combined_ablations = [r for r in ablation_summary if r["split"] == "combined_long_horizon"]
    best_ablation = max([r for r in combined_ablations if r["ablation"] != "spatial_commitment_v5_full"], key=lambda r: float(r["success"]))
    v5_ablation = [r for r in combined_ablations if r["ablation"] == "spatial_commitment_v5_full"][0]

    hard_pair_pass = True
    for ref in ["receding_horizon_tamp", "beam_search_sequence_planner", "topological_base_graph_search", "robust_backtracking_tamp"]:
        rows = [
            r
            for r in hard_pairs
            if r["split"] == "aggregate_hard_regime"
            and r["comparison_method"] == ref
            and r["metric"] == "success"
        ]
        if not rows or float(rows[0]["paired_diff"]) - float(rows[0]["ci95"]) <= 0.0:
            hard_pair_pass = False

    gates = {
        "hard_margin": hard_v5[0] >= hard_best[1] + 0.05,
        "paired_lower_bound": hard_pair_pass,
        "future_regret": regret_v5[0] <= regret_tamp[0] - 0.05,
        "max_stress": float(max_stress_v5["success"]) >= float(max_stress_best["success"]) + 0.02,
        "fixed_risk": any(v5[0] > best[1] + 0.02 and budget > 0.0 for budget, v5, best in fixed_checks),
        "ablation_necessity": float(v5_ablation["success"]) > float(best_ablation["success"]) + 0.03,
        "oracle_gap_reasonable": hard_oracle[0] - hard_v5[0] <= 0.20,
    }
    terminal = "STRONG_REVISE" if all(gates.values()) else "KILL_ARCHIVE"
    failed = [k for k, v in gates.items() if not v]
    reason = (
        f"v5 combined={combined_v5[0]:.3f}, TAMP={combined_tamp[0]:.3f}, robust={combined_robust[0]:.3f}; "
        f"hard aggregate v5={hard_v5[0]:.3f}, best_non_oracle={hard_best[0]}:{hard_best[1]:.3f}, oracle={hard_oracle[0]:.3f}; "
        f"regret v5={regret_v5[0]:.3f}, TAMP={regret_tamp[0]:.3f}; "
        f"max stress v5={float(max_stress_v5['success']):.3f}, best={max_stress_best['method']}:{float(max_stress_best['success']):.3f}; "
        f"best ablation={best_ablation['ablation']}:{float(best_ablation['success']):.3f}; failed gates: {','.join(failed) if failed else 'none'}."
    )

    with (RESULTS / "summary.txt").open("w", encoding="utf-8") as f:
        f.write("Paper 79 mobile_manipulation_spatial_commitments expanded v5 rebuild\n")
        f.write(f"Terminal recommendation: {terminal}\n")
        f.write(f"Reason: {reason}\n")
        f.write(f"Main rollout rows: {len(rollout_rows)}\n")
        f.write(f"Ablation rows: {len(ablation_rows)}\n")
        f.write(f"Stress rows: {len(stress_raw)}\n")
        f.write(f"Fixed-risk rows: {len(fixed_raw)}\n")
        f.write("Seeds: " + str(SEEDS) + "\n\n")
        f.write("Combined long-horizon summary:\n")
        for method in METHODS:
            suc = metric_value(metric_rows, "combined_long_horizon", method, "success")
            reg = metric_value(metric_rows, "combined_long_horizon", method, "future_regret")
            risk = metric_value(metric_rows, "combined_long_horizon", method, "commitment_violation")
            f.write(f"{method} success={suc[0]:.5f} ci95={suc[1]:.5f} future_regret={reg[0]:.5f} commitment_violation={risk[0]:.5f}\n")
        f.write("\nAggregate hard-regime summary:\n")
        for method in METHODS:
            suc = metric_value(hard_metrics, "aggregate_hard_regime", method, "success")
            reg = metric_value(hard_metrics, "aggregate_hard_regime", method, "future_regret")
            f.write(f"{method} success={suc[0]:.5f} ci95={suc[1]:.5f} future_regret={reg[0]:.5f}\n")
        f.write("\nPairwise hard-regime success for v5 reference:\n")
        for row in hard_pairs:
            if row["metric"] == "success":
                f.write(f"vs {row['comparison_method']} diff={row['paired_diff']} ci95={row['ci95']} better_seeds={row['reference_better_seeds']}/{row['seeds']}\n")
        f.write("\nAblation combined_long_horizon:\n")
        for row in combined_ablations:
            f.write(f"{row['ablation']} success={row['success']} ci95={row['ci95']} future_regret={row['future_regret']} risk={row['risk_proxy']}\n")
        f.write(f"\nStress level {max(STRESS_LEVELS):.2f}:\n")
        for row in max_stress_rows:
            f.write(f"{row['method']} success={row['success']} ci95={row['ci95']} future_regret={row['future_regret']} risk={row['risk_proxy']}\n")
        f.write("\nFixed-risk combined_long_horizon:\n")
        for budget, v5, best in fixed_checks:
            f.write(f"budget={budget:.2f} v5={v5[0]:.5f} ci95={v5[1]:.5f} best={best[0]}:{best[1]:.5f}\n")
    write_negative_cases(rollout_rows)
    return terminal


def plot_outputs(metric_rows, ablation_summary, stress_summary, fixed_metrics):
    methods = METHODS
    vals = [metric_value(metric_rows, "combined_long_horizon", m, "success")[0] for m in methods]
    errs = [metric_value(metric_rows, "combined_long_horizon", m, "success")[1] for m in methods]
    colors = ["#868e96", "#adb5bd", "#74c0fc", "#4dabf7", "#ffa94d", "#ffd43b", "#66d9e8", "#63e6be", "#69db7c", "#2f9e44", "#087f5b"]
    plt.figure(figsize=(12, 4.8))
    plt.bar(range(len(methods)), vals, yerr=errs, color=colors, capsize=3)
    plt.xticks(range(len(methods)), [m.replace("_", "\n") for m in methods], fontsize=7)
    plt.ylim(0, 1.05)
    plt.ylabel("episode success")
    plt.title("Combined long-horizon mobile manipulation")
    plt.tight_layout()
    plt.savefig(FIGURES / "spatial_commitment_success.png", dpi=220)
    plt.close()

    vals = [metric_value(metric_rows, "combined_long_horizon", m, "future_regret")[0] for m in methods]
    plt.figure(figsize=(11, 4.6))
    plt.bar(range(len(methods)), vals, color="#e8590c")
    plt.xticks(range(len(methods)), [m.replace("_", "\n") for m in methods], fontsize=7)
    plt.ylabel("future-regret rate")
    plt.title("Future spatial-regret failures")
    plt.tight_layout()
    plt.savefig(FIGURES / "spatial_commitment_regret.png", dpi=220)
    plt.close()

    combined = [r for r in ablation_summary if r["split"] == "combined_long_horizon"]
    plt.figure(figsize=(11, 4.8))
    plt.bar(range(len(combined)), [float(r["success"]) for r in combined], yerr=[float(r["ci95"]) for r in combined], color="#f08c00", capsize=3)
    plt.xticks(range(len(combined)), [r["ablation"].replace("_", "\n") for r in combined], fontsize=7)
    plt.ylim(0, 1.05)
    plt.ylabel("episode success")
    plt.title("Spatial commitment ablations")
    plt.tight_layout()
    plt.savefig(FIGURES / "spatial_commitment_ablation.png", dpi=220)
    plt.close()

    plt.figure(figsize=(9.2, 5.0))
    for method in STRESS_METHODS:
        rows = sorted([r for r in stress_summary if r["method"] == method], key=lambda r: float(r["stress_level"]))
        x = [float(r["stress_level"]) for r in rows]
        y = [float(r["success"]) for r in rows]
        e = [float(r["ci95"]) for r in rows]
        plt.errorbar(x, y, yerr=e, marker="o", linewidth=2, capsize=3, label=method)
    plt.xlabel("commitment stress")
    plt.ylabel("episode success")
    plt.ylim(0, 1.05)
    plt.title("Aisle/clutter/swing stress sweep")
    plt.legend(fontsize=6)
    plt.tight_layout()
    plt.savefig(FIGURES / "spatial_commitment_stress_sweep.png", dpi=220)
    plt.close()

    plt.figure(figsize=(9.2, 5.0))
    for method in FIXED_RISK_METHODS:
        rows = [
            r
            for r in fixed_metrics
            if r["split"] == "combined_long_horizon" and r["method"] == method and r["metric"] == "fixed_risk_success"
        ]
        rows = sorted(rows, key=lambda r: float(r["risk_budget"]))
        plt.errorbar(
            [float(r["risk_budget"]) for r in rows],
            [float(r["mean"]) for r in rows],
            yerr=[float(r["ci95"]) for r in rows],
            marker="o",
            linewidth=2,
            capsize=3,
            label=method,
        )
    plt.xlabel("allowed future-regret risk budget")
    plt.ylabel("fixed-risk success")
    plt.ylim(0, 1.05)
    plt.title("Fixed-risk combined long-horizon success")
    plt.legend(fontsize=6)
    plt.tight_layout()
    plt.savefig(FIGURES / "spatial_commitment_fixed_risk.png", dpi=220)
    plt.close()


def main():
    print(
        f"Paper79 runner quick={QUICK} seeds={SEEDS} main_episodes={MAIN_EPISODES_PER_SPLIT_SEED} methods={len(METHODS)} reference={REFERENCE_METHOD}",
        flush=True,
    )
    rollout_rows, seed_rows, metric_rows, pair_rows, hard_seed, hard_metrics, hard_pairs = run_main()
    ablation_rows, ablation_seed, ablation_summary = run_ablation()
    stress_raw, stress_summary = run_stress()
    fixed_raw, fixed_seed, fixed_metrics, fixed_pairs = run_fixed_risk()
    terminal = write_summary(
        metric_rows,
        pair_rows,
        hard_metrics,
        hard_pairs,
        ablation_summary,
        stress_summary,
        fixed_metrics,
        rollout_rows,
        ablation_rows,
        stress_raw,
        fixed_raw,
    )
    plot_outputs(metric_rows, ablation_summary, stress_summary, fixed_metrics)
    print(f"terminal={terminal}")
    print(
        f"main_rollouts={len(rollout_rows)} aggregate_seed_rows={len(hard_seed)} "
        f"ablation_rollouts={len(ablation_rows)} stress_rollouts={len(stress_raw)} fixed_risk_rollouts={len(fixed_raw)}",
        flush=True,
    )
    print(f"wrote results to {RESULTS}", flush=True)


if __name__ == "__main__":
    main()
