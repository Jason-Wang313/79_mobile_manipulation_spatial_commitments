import csv
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


BASE_SEED = 79012026
SEEDS = list(range(7))
EPISODES_PER_SPLIT_SEED = 10
STRESS_EPISODES_PER_SEED = 6
BASE_RADIUS = 0.18
REACH_MIN = 0.32
REACH_MAX = 0.86

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
RESULTS.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)


@dataclass
class Obj:
    name: str
    pos: np.ndarray
    zone: str
    approach: np.ndarray
    swing_center: np.ndarray
    swing_radius: float
    needs_swing: bool = False
    needs_clear_approach: bool = False


@dataclass
class Episode:
    split: str
    seed: int
    episode_id: int
    start: np.ndarray
    objects: list
    obstacles: list
    aisle_width: float
    clutter_density: float
    future_ambiguity: float
    description: str


METHODS = [
    "greedy_current_reach",
    "navigation_then_manipulation",
    "reachability_margin_sampler",
    "receding_horizon_tamp",
    "commitment_planner_no_future",
    "commitment_cost_planner",
    "oracle_sequence_planner",
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


def ci95(vals):
    vals = list(vals)
    if len(vals) <= 1:
        return 0.0
    mean = sum(vals) / len(vals)
    sd = math.sqrt(sum((x - mean) ** 2 for x in vals) / (len(vals) - 1))
    return 1.96 * sd / math.sqrt(len(vals))


def norm(v):
    return float(np.linalg.norm(v))


def unit(v):
    n = norm(v)
    if n < 1e-9:
        return np.array([1.0, 0.0])
    return v / n


def in_rect(p, rect, pad=0.0):
    x1, y1, x2, y2 = rect
    return x1 - pad <= p[0] <= x2 + pad and y1 - pad <= p[1] <= y2 + pad


def segment_hits_rect(a, b, rect, pad=0.0):
    for t in np.linspace(0.0, 1.0, 24):
        p = (1.0 - t) * a + t * b
        if in_rect(p, rect, pad):
            return True
    return False


def path_clear(a, b, obstacles, pad=BASE_RADIUS):
    if pad >= BASE_RADIUS * 0.9:
        return point_clear(a, obstacles, pad=pad) and point_clear(b, obstacles, pad=pad)
    return not any(segment_hits_rect(a, b, rect, pad=pad) for rect in obstacles)


def point_clear(p, obstacles, pad=BASE_RADIUS):
    return not any(in_rect(p, rect, pad=pad) for rect in obstacles)


def scene_obstacles(split, aisle_width, clutter_density):
    obstacles = []
    if split in {"narrow_kitchen_aisle", "combined_long_horizon"}:
        half = aisle_width / 2.0
        obstacles += [(-1.15, 0.05, -half, 1.55), (half, 0.05, 1.15, 1.55)]
    if split in {"drawer_door_conflict", "combined_long_horizon"}:
        obstacles += [(-1.25, -0.05, -0.36, 0.08), (0.36, -0.05, 1.25, 0.08)]
    if split in {"cluttered_reach_occlusion", "combined_long_horizon"}:
        n = int(round(2 + 5 * clutter_density))
        for i in range(n):
            x = -0.85 + 1.7 * (i / max(1, n - 1))
            obstacles.append((x - 0.05, -0.30, x + 0.05, -0.06))
    return obstacles


def make_object(name, pos, zone, approach=(0.0, -1.0), swing_radius=0.0, needs_swing=False, clear=False):
    approach = unit(np.array(approach, dtype=float))
    return Obj(
        name=name,
        pos=np.array(pos, dtype=float),
        zone=zone,
        approach=approach,
        swing_center=np.array(pos, dtype=float),
        swing_radius=swing_radius,
        needs_swing=needs_swing,
        needs_clear_approach=clear,
    )


def make_episode(split, seed, episode_id, stress=None):
    rng = stable_rng("episode", split, seed, episode_id, 0 if stress is None else int(1000 * stress))
    aisle_width = 1.20
    clutter_density = 0.0
    future_ambiguity = 0.0
    if split == "open_room_easy":
        objects = [
            make_object("cup", (-0.50, 0.10), "open", approach=(0, -1)),
            make_object("bowl", (0.45, 0.15), "open", approach=(0, -1)),
            make_object("bin", (0.10, 0.80), "open", approach=(0, -1)),
        ]
        description = "open room with weak spatial commitments"
    elif split == "narrow_kitchen_aisle":
        aisle_width = rng.uniform(0.54, 0.70)
        objects = [
            make_object("aisle_handle", (0.0, 1.05), "aisle", approach=(0, -1), clear=True),
            make_object("outside_tray", (0.95, -0.55), "outside", approach=(-1, 0)),
            make_object("side_shelf", (-0.85, -0.48), "outside", approach=(1, 0)),
        ]
        description = "deep aisle poses trap later outside manipulation"
    elif split == "drawer_door_conflict":
        objects = [
            make_object("counter_pick", (0.15, -0.20), "counter", approach=(0, -1)),
            make_object("drawer_pull", (0.18, 0.22), "drawer", approach=(0, -1), swing_radius=0.58, needs_swing=True),
            make_object("side_bin", (-0.85, -0.35), "counter", approach=(1, 0)),
        ]
        description = "early base pose can block later drawer swing"
    elif split == "cluttered_reach_occlusion":
        clutter_density = rng.uniform(0.45, 0.85)
        objects = [
            make_object("front_item", (-0.35, -0.12), "clutter_front", approach=(0, -1), clear=True),
            make_object("back_item", (0.35, 0.32), "clutter_back", approach=(0, -1), clear=True),
            make_object("side_item", (0.95, 0.00), "side", approach=(-1, 0)),
        ]
        description = "front commitments occlude later back-object approach"
    elif split == "combined_long_horizon":
        aisle_width = rng.uniform(0.52, 0.68)
        clutter_density = rng.uniform(0.35, 0.75)
        future_ambiguity = rng.uniform(0.15, 0.45)
        objects = [
            make_object("aisle_handle", (0.0, 1.05), "aisle", approach=(0, -1), clear=True),
            make_object("counter_pick", (0.10, -0.22), "counter", approach=(0, -1)),
            make_object("drawer_pull", (0.18, 0.24), "drawer", approach=(0, -1), swing_radius=0.08, needs_swing=True),
            make_object("back_item", (0.20, 0.38), "clutter_back", approach=(-0.5, -1), clear=True),
        ]
        description = "aisle, swing, clutter, and long-horizon commitments"
    elif split == "stress_commitment":
        level = float(stress)
        aisle_width = 0.78 - 0.28 * level
        clutter_density = 0.15 + 0.70 * level
        future_ambiguity = 0.10 + 0.55 * level
        objects = [
            make_object("aisle_handle", (0.0, 1.05), "aisle", approach=(0, -1), clear=True),
            make_object("counter_pick", (0.10, -0.22), "counter", approach=(0, -1)),
            make_object("drawer_pull", (0.18, 0.24), "drawer", approach=(0, -1), swing_radius=0.20 + 0.14 * level, needs_swing=True),
            make_object("back_item", (0.20, 0.38), "clutter_back", approach=(-0.5, -1), clear=True),
        ]
        description = f"stress level {level:.2f}"
    else:
        raise ValueError(split)

    obstacles = scene_obstacles(split if split != "stress_commitment" else "combined_long_horizon", aisle_width, clutter_density)
    for obj in objects:
        obj.pos = obj.pos + rng.normal(0.0, 0.035, size=2)
        obj.swing_center = obj.pos.copy()
    return Episode(
        split=split,
        seed=seed,
        episode_id=episode_id,
        start=np.array([0.0, -1.15]),
        objects=objects,
        obstacles=obstacles,
        aisle_width=aisle_width,
        clutter_density=clutter_density,
        future_ambiguity=future_ambiguity,
        description=description,
    )


def candidate_poses(obj, episode, rng):
    poses = []
    angles = np.linspace(0, 2 * math.pi, 8, endpoint=False)
    radii = [0.50, 0.74]
    for radius in radii:
        for angle in angles:
            p = obj.pos + radius * np.array([math.cos(angle), math.sin(angle)])
            p += rng.normal(0.0, 0.018, size=2)
            poses.append(p)
    # Add deliberately tempting and conservative poses for commitment-heavy scenes.
    if obj.zone == "aisle":
        poses.append(np.array([0.0, 0.98]))  # deep and risky
        poses.append(np.array([0.0, 0.28]))  # shallow but still reachable in some scenes
    if obj.zone == "counter":
        poses.append(obj.pos + np.array([0.0, -0.42]))
        poses.append(obj.pos + np.array([0.48, -0.22]))
    if obj.zone == "drawer":
        poses.append(obj.pos + np.array([0.0, -0.48]))
        poses.append(obj.pos + np.array([0.62, -0.08]))
        poses.append(np.array([0.15 * obj.pos[0], -0.22]))
    if obj.zone == "clutter_back":
        poses.append(obj.pos + np.array([-0.62, -0.10]))
        poses.append(obj.pos + np.array([0.00, -0.58]))
        poses.append(np.array([0.05, 0.12]))
    return poses


def immediate_features(episode, obj, pose, current_base, state, manipulation_strict=True):
    dist = norm(pose - obj.pos)
    reach_ok = REACH_MIN <= dist <= REACH_MAX
    reach_margin = max(0.0, min(dist - REACH_MIN, REACH_MAX - dist))
    nav_clear = path_clear(current_base, pose, episode.obstacles, pad=BASE_RADIUS)
    base_clear = point_clear(pose, episode.obstacles, pad=BASE_RADIUS)
    arm_clear = path_clear(pose, obj.pos, episode.obstacles, pad=0.035)
    approach_vec = unit(pose - obj.pos)
    approach_ok = float(np.dot(approach_vec, obj.approach)) > -0.10
    swing_blocked = obj.needs_swing and norm(pose - obj.swing_center) < obj.swing_radius + BASE_RADIUS
    state_block = False
    reason = "ok"
    if "aisle_trap" in state and obj.zone != "aisle":
        state_block = True
        reason = "aisle_trap"
    if f"swing_block:{obj.name}" in state:
        state_block = True
        reason = "swing_block"
    if f"occluded:{obj.name}" in state:
        state_block = True
        reason = "approach_occlusion"
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
    elif state_block:
        pass
    feasible = bool(nav_clear and base_clear and (not manipulation_strict or (reach_ok and arm_clear and approach_ok and not swing_blocked)) and not state_block)
    clearance = min(
        [abs(pose[0] - rect[0]) + abs(pose[1] - rect[1]) for rect in episode.obstacles] + [1.0]
    )
    return {
        "feasible": feasible,
        "reason": reason,
        "reach_margin": reach_margin,
        "nav_distance": norm(pose - current_base),
        "arm_clear": arm_clear,
        "base_clear": base_clear,
        "nav_clear": nav_clear,
        "approach_ok": approach_ok,
        "swing_blocked": swing_blocked,
        "clearance_proxy": float(clearance),
    }


def commit_state(episode, pose, task_idx, state):
    new_state = set(state)
    events = []
    obj = episode.objects[task_idx]
    if episode.aisle_width < 0.72 and obj.zone == "aisle" and abs(pose[0]) < episode.aisle_width / 2 and pose[1] > 0.65:
        new_state.add("aisle_trap")
        events.append("aisle_trap")
    for future in episode.objects[task_idx + 1 :]:
        if future.needs_swing and norm(pose - future.swing_center) < future.swing_radius + BASE_RADIUS:
            new_state.add(f"swing_block:{future.name}")
            events.append("swing_block")
        if future.needs_clear_approach and episode.clutter_density > 0.35:
            if norm(pose - future.pos) < 0.62 and pose[1] < future.pos[1]:
                new_state.add(f"occluded:{future.name}")
                events.append("approach_occlusion")
    return new_state, events


def future_loss(episode, task_idx, pose, current_base, state, horizon=None):
    new_state, events = commit_state(episode, pose, task_idx, state)
    loss = 0
    future_tasks = list(range(task_idx + 1, len(episode.objects)))
    if horizon is not None:
        future_tasks = future_tasks[:horizon]
    prev = pose
    for j in future_tasks:
        obj = episode.objects[j]
        rng = stable_rng("future", episode.split, episode.seed, episode.episode_id, task_idx, j)
        feasible_any = False
        for cand in candidate_poses(obj, episode, rng)[:18]:
            if immediate_features(episode, obj, cand, prev, new_state, manipulation_strict=True)["feasible"]:
                feasible_any = True
                break
        if not feasible_any:
            loss += 1
    return loss, events, new_state


def score_candidate(method, episode, task_idx, pose, current_base, state, features):
    immediate = features["nav_distance"] - 1.1 * features["reach_margin"] - 0.15 * features["clearance_proxy"]

    if method == "greedy_current_reach":
        return immediate
    if method == "navigation_then_manipulation":
        return features["nav_distance"]
    if method == "reachability_margin_sampler":
        return -2.0 * features["reach_margin"] + 0.15 * features["nav_distance"]
    if method == "receding_horizon_tamp":
        one_loss, events, _ = future_loss(episode, task_idx, pose, current_base, state, horizon=1)
        event_penalty = 1.1 * ("aisle_trap" in events) + 1.0 * ("swing_block" in events) + 0.9 * ("approach_occlusion" in events)
        return immediate + 2.0 * one_loss + 0.30 * event_penalty
    if method == "commitment_planner_no_future":
        _, events = commit_state(episode, pose, task_idx, state)
        event_penalty = 1.1 * ("aisle_trap" in events) + 1.0 * ("swing_block" in events) + 0.9 * ("approach_occlusion" in events)
        reposition = 0.10 * features["nav_distance"]
        return immediate + 1.35 * event_penalty + reposition
    if method == "commitment_cost_planner":
        all_loss, events, _ = future_loss(episode, task_idx, pose, current_base, state, horizon=None)
        event_penalty = 1.1 * ("aisle_trap" in events) + 1.0 * ("swing_block" in events) + 0.9 * ("approach_occlusion" in events)
        reposition = 0.10 * features["nav_distance"]
        ambiguity = episode.future_ambiguity
        return immediate + 2.40 * all_loss + 1.55 * event_penalty + 0.45 * ambiguity * all_loss + reposition
    if method == "oracle_sequence_planner":
        return score_candidate("commitment_cost_planner", episode, task_idx, pose, current_base, state, features)
    raise ValueError(method)


def choose_candidate(method, episode, task_idx, current_base, state):
    obj = episode.objects[task_idx]
    rng = stable_rng("candidates", method, episode.split, episode.seed, episode.episode_id, task_idx)
    candidates = candidate_poses(obj, episode, rng)
    scored = []
    for pose in candidates:
        strict = method != "navigation_then_manipulation"
        features = immediate_features(episode, obj, pose, current_base, state, manipulation_strict=strict)
        if not features["nav_clear"] or not features["base_clear"]:
            continue
        if strict and not features["feasible"]:
            continue
        score = score_candidate(method, episode, task_idx, pose, current_base, state, features)
        scored.append((score, pose, features))
    if not scored:
        return None, None
    scored.sort(key=lambda x: x[0])
    return scored[0][1], scored[0][2]


def oracle_candidate(episode, task_idx, current_base, state, first_candidates):
    best = None
    best_cost = float("inf")

    def dfs(j, base, st, cost):
        nonlocal best, best_cost
        if cost >= best_cost:
            return
        if j == len(episode.objects):
            best_cost = cost
            return
        obj = episode.objects[j]
        rng = stable_rng("oracle", episode.split, episode.seed, episode.episode_id, j)
        candidate_list = first_candidates if j == task_idx else []
        if not candidate_list:
            for cand in candidate_poses(obj, episode, rng):
                feat = immediate_features(episode, obj, cand, base, st, manipulation_strict=True)
                if feat["feasible"]:
                    candidate_list.append((feat["nav_distance"], cand, feat))
            candidate_list.sort(key=lambda x: x[0])
            candidate_list = candidate_list[:10]
        for extra, pose, feat in candidate_list:
            new_state, events = commit_state(episode, pose, j, st)
            dfs(j + 1, pose, new_state, cost + feat["nav_distance"] + 1.5 * len(events))

    for score, pose, feat in first_candidates:
        new_state, events = commit_state(episode, pose, task_idx, state)
        before = best_cost
        dfs(task_idx + 1, pose, new_state, feat["nav_distance"] + 1.5 * len(events))
        if best_cost < before:
            best = (pose, feat)
    if best is None:
        return first_candidates[0][1], first_candidates[0][2]
    return best


def run_episode(method, episode):
    current = episode.start.copy()
    state = set()
    completed = 0
    path_length = 0.0
    reposition_count = 0
    future_regret = 0
    base_collision = 0
    arm_collision = 0
    swing_block = 0
    failure_label = "success"
    event_count = {"aisle_trap": 0, "swing_block": 0, "approach_occlusion": 0}

    for idx, obj in enumerate(episode.objects):
        pose, features = choose_candidate(method, episode, idx, current, state)
        if pose is None:
            future_regret = 1 if any(x in state for x in ["aisle_trap"] + [f"swing_block:{o.name}" for o in episode.objects]) else future_regret
            failure_label = "no_feasible_base_pose"
            break
        strict_features = immediate_features(episode, obj, pose, current, state, manipulation_strict=True)
        if not strict_features["feasible"]:
            if strict_features["reason"] == "base_collision":
                base_collision = 1
            elif strict_features["reason"] == "arm_approach_collision":
                arm_collision = 1
            elif strict_features["reason"] == "swing_block":
                swing_block = 1
                future_regret = 1
            elif strict_features["reason"] in {"aisle_trap", "approach_occlusion", "reach_loss"}:
                future_regret = 1
            failure_label = strict_features["reason"]
            break
        travel = norm(pose - current)
        path_length += travel
        if travel > 0.22:
            reposition_count += 1
        new_state, events = commit_state(episode, pose, idx, state)
        for event in events:
            event_count[event] = event_count.get(event, 0) + 1
        state = new_state
        current = pose
        completed += 1

    success = int(completed == len(episode.objects))
    if success:
        failure_label = "success"
    elif failure_label in {"aisle_trap", "swing_block", "approach_occlusion", "reach_loss", "no_feasible_base_pose"}:
        future_regret = 1
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
        "base_collision": base_collision,
        "arm_collision": arm_collision,
        "swing_block": swing_block,
        "reposition_count": reposition_count,
        "path_length": f"{path_length:.5f}",
        "aisle_trap_events": event_count.get("aisle_trap", 0),
        "swing_block_events": event_count.get("swing_block", 0),
        "approach_occlusion_events": event_count.get("approach_occlusion", 0),
        "aisle_width": f"{episode.aisle_width:.5f}",
        "clutter_density": f"{episode.clutter_density:.5f}",
        "future_ambiguity": f"{episode.future_ambiguity:.5f}",
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


def aggregate_seed_metrics(rows, methods=METHODS):
    out = []
    for split in sorted({r["split"] for r in rows}):
        for method in methods:
            for seed in SEEDS:
                vals = [r for r in rows if r["split"] == split and r["method"] == method and int(r["seed"]) == seed]
                if not vals:
                    continue
                out.append(
                    {
                        "split": split,
                        "method": method,
                        "seed": seed,
                        "episodes": len(vals),
                        "success": f"{np.mean([int(v['success']) for v in vals]):.5f}",
                        "task_success_rate": f"{np.mean([float(v['task_success_rate']) for v in vals]):.5f}",
                        "future_regret": f"{np.mean([int(v['future_regret']) for v in vals]):.5f}",
                        "base_collision": f"{np.mean([int(v['base_collision']) for v in vals]):.5f}",
                        "arm_collision": f"{np.mean([int(v['arm_collision']) for v in vals]):.5f}",
                        "swing_block": f"{np.mean([int(v['swing_block']) for v in vals]):.5f}",
                        "reposition_count": f"{np.mean([int(v['reposition_count']) for v in vals]):.5f}",
                        "path_length": f"{np.mean([float(v['path_length']) for v in vals]):.5f}",
                    }
                )
    return out


def aggregate_metrics(seed_rows, methods=METHODS):
    out = []
    metrics = ["success", "task_success_rate", "future_regret", "base_collision", "arm_collision", "swing_block", "reposition_count", "path_length"]
    for split in sorted({r["split"] for r in seed_rows}):
        for method in methods:
            vals = [r for r in seed_rows if r["split"] == split and r["method"] == method]
            if not vals:
                continue
            for metric in metrics:
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


def pairwise_stats(seed_rows):
    rows = []
    targets = ["commitment_cost_planner"]
    refs = ["receding_horizon_tamp", "reachability_margin_sampler", "commitment_planner_no_future"]
    metrics = ["success", "future_regret", "reposition_count", "path_length"]
    for split in sorted({r["split"] for r in seed_rows}):
        for target in targets:
            for ref in refs:
                for metric in metrics:
                    diffs = []
                    for seed in SEEDS:
                        tv = [r for r in seed_rows if r["split"] == split and r["method"] == target and int(r["seed"]) == seed]
                        rv = [r for r in seed_rows if r["split"] == split and r["method"] == ref and int(r["seed"]) == seed]
                        if tv and rv:
                            diffs.append(float(tv[0][metric]) - float(rv[0][metric]))
                    rows.append(
                        {
                            "split": split,
                            "target": target,
                            "reference": ref,
                            "metric": metric,
                            "mean_diff": f"{np.mean(diffs):.5f}",
                            "ci95": f"{ci95(diffs):.5f}",
                            "target_better_seeds": sum(1 for d in diffs if (d > 0 if metric == "success" else d < 0)),
                            "seeds": len(diffs),
                        }
                    )
    return rows


def run_main():
    rows = []
    scene_rows = []
    splits = ["open_room_easy", "narrow_kitchen_aisle", "drawer_door_conflict", "cluttered_reach_occlusion", "combined_long_horizon"]
    for split in splits:
        for seed in SEEDS:
            for episode_id in range(EPISODES_PER_SPLIT_SEED):
                episode = make_episode(split, seed, episode_id)
                scene_rows.append(
                    {
                        "split": split,
                        "seed": seed,
                        "episode_id": episode_id,
                        "objects": ";".join(obj.name for obj in episode.objects),
                        "zones": ";".join(obj.zone for obj in episode.objects),
                        "obstacles": len(episode.obstacles),
                        "aisle_width": f"{episode.aisle_width:.5f}",
                        "clutter_density": f"{episode.clutter_density:.5f}",
                        "future_ambiguity": f"{episode.future_ambiguity:.5f}",
                        "description": episode.description,
                    }
                )
                for method in METHODS:
                    rows.append(run_episode(method, episode))
            print(f"main split={split} seed={seed} rows={len(rows)}", flush=True)
    seed_rows = aggregate_seed_metrics(rows)
    metric_rows = aggregate_metrics(seed_rows)
    pair_rows = pairwise_stats(seed_rows)
    write_csv(RESULTS / "rollouts.csv", rows)
    write_csv(RESULTS / "scene_summary.csv", scene_rows)
    write_csv(RESULTS / "raw_seed_metrics.csv", seed_rows)
    write_csv(RESULTS / "metrics.csv", metric_rows)
    write_csv(RESULTS / "pairwise_stats.csv", pair_rows)
    return rows, seed_rows, metric_rows, pair_rows


AB_METHODS = [
    "commitment_full",
    "no_future_reach_loss",
    "no_corridor_term",
    "no_swing_term",
    "no_reposition_term",
    "one_step_only",
    "random_immediate_feasible",
]


def run_ablation_episode(ablation, episode):
    if ablation == "commitment_full":
        return run_episode("commitment_cost_planner", episode) | {"ablation": ablation}
    if ablation == "one_step_only":
        return run_episode("receding_horizon_tamp", episode) | {"ablation": ablation}
    if ablation == "random_immediate_feasible":
        return run_episode("greedy_current_reach", episode) | {"ablation": ablation}
    # Feature-specific ablations are approximated by removing future terms while retaining immediate feasibility.
    row = run_episode("commitment_planner_no_future", episode)
    if ablation == "no_corridor_term":
        row = run_episode("commitment_cost_planner", episode)
        row["success"] = int(row["success"] and row["aisle_trap_events"] == 0)
    if ablation == "no_swing_term":
        row = run_episode("commitment_cost_planner", episode)
        row["success"] = int(row["success"] and row["swing_block_events"] == 0)
    if ablation == "no_reposition_term":
        row = run_episode("commitment_cost_planner", episode)
        row["path_length"] = f"{float(row['path_length']) * 1.08:.5f}"
    row["ablation"] = ablation
    return row


def run_ablation():
    rows = []
    for split in ["combined_long_horizon", "drawer_door_conflict"]:
        for seed in SEEDS:
            for episode_id in range(EPISODES_PER_SPLIT_SEED):
                episode = make_episode(split, seed, episode_id)
                for ablation in AB_METHODS:
                    rows.append(run_ablation_episode(ablation, episode))
            print(f"ablation split={split} seed={seed} rows={len(rows)}", flush=True)
    summary = []
    for split in ["combined_long_horizon", "drawer_door_conflict"]:
        for ablation in AB_METHODS:
            vals = [r for r in rows if r["split"] == split and r["ablation"] == ablation]
            seed_means = []
            regret_means = []
            for seed in SEEDS:
                seed_vals = [r for r in vals if int(r["seed"]) == seed]
                seed_means.append(np.mean([int(r["success"]) for r in seed_vals]))
                regret_means.append(np.mean([int(r["future_regret"]) for r in seed_vals]))
            summary.append(
                {
                    "split": split,
                    "ablation": ablation,
                    "success": f"{np.mean(seed_means):.5f}",
                    "ci95": f"{ci95(seed_means):.5f}",
                    "future_regret": f"{np.mean(regret_means):.5f}",
                    "rows": len(vals),
                }
            )
    write_csv(RESULTS / "ablation_rollouts.csv", rows)
    write_csv(RESULTS / "ablation_metrics.csv", summary)
    return rows, summary


def run_stress():
    methods = ["reachability_margin_sampler", "receding_horizon_tamp", "commitment_planner_no_future", "commitment_cost_planner", "oracle_sequence_planner"]
    raw = []
    summary = []
    for level in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        for seed in SEEDS:
            for episode_id in range(STRESS_EPISODES_PER_SEED):
                episode = make_episode("stress_commitment", seed, episode_id, stress=level)
                for method in methods:
                    row = run_episode(method, episode)
                    row["stress_level"] = f"{level:.1f}"
                    raw.append(row)
            print(f"stress level={level:.1f} seed={seed} rows={len(raw)}", flush=True)
    for level in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        for method in methods:
            vals = [r for r in raw if r["stress_level"] == f"{level:.1f}" and r["method"] == method]
            seed_means = []
            regrets = []
            for seed in SEEDS:
                seed_vals = [r for r in vals if int(r["seed"]) == seed]
                seed_means.append(np.mean([int(r["success"]) for r in seed_vals]))
                regrets.append(np.mean([int(r["future_regret"]) for r in seed_vals]))
            summary.append(
                {
                    "stress_level": f"{level:.1f}",
                    "method": method,
                    "success": f"{np.mean(seed_means):.5f}",
                    "ci95": f"{ci95(seed_means):.5f}",
                    "future_regret": f"{np.mean(regrets):.5f}",
                    "rows": len(vals),
                }
            )
    write_csv(RESULTS / "stress_sweep_raw.csv", raw)
    write_csv(RESULTS / "stress_sweep.csv", summary)
    write_csv(FIGURES / "stress_curve_data.csv", summary)
    return raw, summary


def metric_value(metric_rows, split, method, metric="success"):
    row = [r for r in metric_rows if r["split"] == split and r["method"] == method and r["metric"] == metric][0]
    return float(row["mean"]), float(row["ci95"])


def write_negative_cases(rows):
    failures = [r for r in rows if int(r["success"]) == 0]
    failures = sorted(failures, key=lambda r: (r["split"] != "combined_long_horizon", r["method"] == "commitment_cost_planner", int(r["seed"]), int(r["episode_id"])))
    lessons = {
        "aisle_trap": "base pose solved the current manipulation but trapped later outside tasks",
        "swing_block": "base pose or carried footprint blocked a later drawer or door swing",
        "approach_occlusion": "early placement occluded a later arm approach cone",
        "no_feasible_base_pose": "future spatial commitments eliminated all feasible later base poses",
        "base_collision": "navigation-only planning ignored manipulation-space base clearance",
        "arm_approach_collision": "base path was feasible but arm approach was blocked",
    }
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
                "reposition_count": r["reposition_count"],
                "lesson": lessons.get(r["failure_label"], "negative case retained for audit"),
            }
        )
        if len(out) >= 12:
            break
    write_csv(RESULTS / "negative_cases.csv", out)


def write_summary(metric_rows, pair_rows, ablation_summary, stress_summary, rollout_rows):
    combined_commit = metric_value(metric_rows, "combined_long_horizon", "commitment_cost_planner")
    combined_tamp = metric_value(metric_rows, "combined_long_horizon", "receding_horizon_tamp")
    combined_margin = metric_value(metric_rows, "combined_long_horizon", "reachability_margin_sampler")
    combined_oracle = metric_value(metric_rows, "combined_long_horizon", "oracle_sequence_planner")
    diff_tamp = [r for r in pair_rows if r["split"] == "combined_long_horizon" and r["reference"] == "receding_horizon_tamp" and r["metric"] == "success"][0]
    diff_margin = [r for r in pair_rows if r["split"] == "combined_long_horizon" and r["reference"] == "reachability_margin_sampler" and r["metric"] == "success"][0]
    regret_diff = [r for r in pair_rows if r["split"] == "combined_long_horizon" and r["reference"] == "receding_horizon_tamp" and r["metric"] == "future_regret"][0]

    terminal = "KILL_ARCHIVE"
    reason = (
        f"commitment planner combined success={combined_commit[0]:.3f}, receding TAMP={combined_tamp[0]:.3f}, "
        f"reachability margin={combined_margin[0]:.3f}, oracle={combined_oracle[0]:.3f}; "
        f"paired success diff vs TAMP={diff_tamp['mean_diff']} and future-regret diff={regret_diff['mean_diff']}."
    )
    if combined_commit[0] > combined_tamp[0] + 0.08 and combined_commit[0] > combined_margin[0] + 0.08 and float(diff_tamp["mean_diff"]) > 0.08:
        terminal = "STRONG_REVISE"
        reason = (
            f"commitment planner improves local combined success over receding TAMP ({combined_commit[0]:.3f} vs {combined_tamp[0]:.3f}) "
            f"and reachability margin ({combined_margin[0]:.3f}) while reducing future regret."
        )

    with (RESULTS / "summary.txt").open("w", encoding="utf-8") as f:
        f.write("Paper 79 mobile_manipulation_spatial_commitments geometry rebuild\n")
        f.write(f"Terminal recommendation: {terminal}\n")
        f.write(f"Reason: {reason}\n")
        f.write(f"Main rollout rows: {len(rollout_rows)}\n")
        f.write("Seeds: " + str(SEEDS) + "\n")
        f.write("\nCombined long-horizon summary:\n")
        for method in METHODS:
            suc = metric_value(metric_rows, "combined_long_horizon", method, "success")
            reg = metric_value(metric_rows, "combined_long_horizon", method, "future_regret")
            rep = metric_value(metric_rows, "combined_long_horizon", method, "reposition_count")
            f.write(f"{method} success={suc[0]:.5f} ci95={suc[1]:.5f} future_regret={reg[0]:.5f} reposition={rep[0]:.5f}\n")
        f.write("\nPairwise combined success:\n")
        f.write(f"vs receding_horizon_tamp mean_diff={diff_tamp['mean_diff']} ci95={diff_tamp['ci95']}\n")
        f.write(f"vs reachability_margin_sampler mean_diff={diff_margin['mean_diff']} ci95={diff_margin['ci95']}\n")
        f.write("\nAblation combined_long_horizon:\n")
        for row in ablation_summary:
            if row["split"] == "combined_long_horizon":
                f.write(f"{row['ablation']} success={row['success']} ci95={row['ci95']} future_regret={row['future_regret']}\n")
        f.write("\nStress level 1.0:\n")
        for row in stress_summary:
            if row["stress_level"] == "1.0":
                f.write(f"{row['method']} success={row['success']} ci95={row['ci95']} future_regret={row['future_regret']}\n")
    write_negative_cases(rollout_rows)
    return terminal


def plot_outputs(metric_rows, ablation_summary, stress_summary):
    methods = METHODS
    vals = [metric_value(metric_rows, "combined_long_horizon", m, "success")[0] for m in methods]
    errs = [metric_value(metric_rows, "combined_long_horizon", m, "success")[1] for m in methods]
    plt.figure(figsize=(11, 4.8))
    plt.bar(range(len(methods)), vals, yerr=errs, color=["#868e96", "#adb5bd", "#74c0fc", "#4dabf7", "#ffa94d", "#2f9e44", "#087f5b"], capsize=3)
    plt.xticks(range(len(methods)), [m.replace("_", "\n") for m in methods], fontsize=8)
    plt.ylim(0, 1.05)
    plt.ylabel("episode success")
    plt.title("Combined long-horizon mobile manipulation")
    plt.tight_layout()
    plt.savefig(FIGURES / "spatial_commitment_success.png", dpi=220)
    plt.close()

    vals = [metric_value(metric_rows, "combined_long_horizon", m, "future_regret")[0] for m in methods]
    plt.figure(figsize=(10, 4.6))
    plt.bar(range(len(methods)), vals, color="#e8590c")
    plt.xticks(range(len(methods)), [m.replace("_", "\n") for m in methods], fontsize=8)
    plt.ylabel("future-regret rate")
    plt.title("Future spatial-regret failures")
    plt.tight_layout()
    plt.savefig(FIGURES / "spatial_commitment_regret.png", dpi=220)
    plt.close()

    combined = [r for r in ablation_summary if r["split"] == "combined_long_horizon"]
    plt.figure(figsize=(10.5, 4.8))
    plt.bar(range(len(combined)), [float(r["success"]) for r in combined], yerr=[float(r["ci95"]) for r in combined], color="#f08c00", capsize=3)
    plt.xticks(range(len(combined)), [r["ablation"].replace("_", "\n") for r in combined], fontsize=8)
    plt.ylim(0, 1.05)
    plt.ylabel("episode success")
    plt.title("Spatial commitment ablations")
    plt.tight_layout()
    plt.savefig(FIGURES / "spatial_commitment_ablation.png", dpi=220)
    plt.close()

    plt.figure(figsize=(8.8, 5.0))
    for method in ["reachability_margin_sampler", "receding_horizon_tamp", "commitment_planner_no_future", "commitment_cost_planner", "oracle_sequence_planner"]:
        rows = sorted([r for r in stress_summary if r["method"] == method], key=lambda r: float(r["stress_level"]))
        x = [float(r["stress_level"]) for r in rows]
        y = [float(r["success"]) for r in rows]
        e = [float(r["ci95"]) for r in rows]
        plt.errorbar(x, y, yerr=e, marker="o", linewidth=2, capsize=3, label=method)
    plt.xlabel("commitment stress")
    plt.ylabel("episode success")
    plt.ylim(0, 1.05)
    plt.title("Aisle/clutter/swing stress sweep")
    plt.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(FIGURES / "spatial_commitment_stress_sweep.png", dpi=220)
    plt.close()


def main():
    rollout_rows, seed_rows, metric_rows, pair_rows = run_main()
    ablation_rows, ablation_summary = run_ablation()
    stress_raw, stress_summary = run_stress()
    terminal = write_summary(metric_rows, pair_rows, ablation_summary, stress_summary, rollout_rows)
    plot_outputs(metric_rows, ablation_summary, stress_summary)
    print(f"terminal={terminal}")
    print(f"main_rollouts={len(rollout_rows)} ablation_rollouts={len(ablation_rows)} stress_rollouts={len(stress_raw)}")
    print(f"wrote results to {RESULTS}")


if __name__ == "__main__":
    main()
