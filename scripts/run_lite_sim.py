from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np


@dataclass
class Obstacle:
    position: np.ndarray
    velocity: np.ndarray
    radius: float


def normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm < 1e-8:
        return np.zeros_like(vec)
    return vec / norm


def update_obstacles(obstacles: list[Obstacle], bounds: float, dt: float) -> None:
    for obs in obstacles:
        obs.position = obs.position + obs.velocity * dt
        for idx in range(2):
            if abs(obs.position[idx]) > bounds - obs.radius:
                obs.velocity[idx] *= -1.0
                obs.position[idx] = np.clip(
                    obs.position[idx],
                    -bounds + obs.radius,
                    bounds - obs.radius,
                )


def nominal_policy(position: np.ndarray, velocity: np.ndarray, goal: np.ndarray) -> np.ndarray:
    direction = goal - position
    desired_velocity = normalize(direction) * 1.15
    return (desired_velocity - velocity) * 1.8


def apply_safety_shield(
    position: np.ndarray,
    velocity: np.ndarray,
    action: np.ndarray,
    obstacles: list[Obstacle],
    dt: float,
    shield_margin: float,
) -> tuple[np.ndarray, bool, float]:
    predicted_velocity = velocity + action * dt
    predicted_velocity = np.clip(predicted_velocity, -1.4, 1.4)
    predicted_position = position + predicted_velocity * dt

    repulsion = np.zeros(2, dtype=float)
    min_clearance = float("inf")
    triggered = False

    for horizon in range(1, 7):
        future_position = position + predicted_velocity * (dt * horizon)
        for obs in obstacles:
            obs_future = obs.position + obs.velocity * (dt * horizon)
            delta = future_position - obs_future
            distance = np.linalg.norm(delta)
            clearance = distance - obs.radius
            min_clearance = min(min_clearance, clearance)

            if clearance < shield_margin:
                triggered = True
                away = normalize(delta if distance > 1e-8 else np.array([1.0, 0.0]))
                tangent = np.array([-away[1], away[0]])
                repulsion += away * (shield_margin - clearance) * 1.8
                repulsion += tangent * 0.18

    if triggered:
        action = action + repulsion

    return np.clip(action, -2.5, 2.5), triggered, min_clearance


def rollout(seed: int, steps: int, dt: float) -> tuple[list[dict], dict]:
    rng = np.random.default_rng(seed)
    bounds = 6.0
    goal = np.array([4.8, 4.6], dtype=float)
    position = np.array([-4.8, -4.5], dtype=float)
    velocity = np.zeros(2, dtype=float)
    goal_radius = 0.35
    shield_margin = 0.95

    obstacles = [
        Obstacle(np.array([-0.5, 1.8], dtype=float), np.array([0.55, -0.15], dtype=float), 0.45),
        Obstacle(np.array([1.8, -1.2], dtype=float), np.array([-0.45, 0.30], dtype=float), 0.55),
        Obstacle(np.array([0.0, 0.0], dtype=float), np.array([0.15, 0.48], dtype=float), 0.60),
        Obstacle(np.array([3.5, 2.4], dtype=float), np.array([-0.35, -0.20], dtype=float), 0.50),
    ]

    frames: list[dict] = []
    shield_count = 0
    success = False
    collided = False
    min_clearance = float("inf")

    for step in range(steps):
        nominal_action = nominal_policy(position, velocity, goal)
        noisy_action = nominal_action + rng.normal(0.0, 0.07, size=2)
        safe_action, triggered, clearance = apply_safety_shield(
            position,
            velocity,
            noisy_action,
            obstacles,
            dt,
            shield_margin,
        )
        min_clearance = min(min_clearance, clearance)
        shield_count += int(triggered)

        velocity = np.clip(velocity + safe_action * dt, -1.4, 1.4)
        position = np.clip(position + velocity * dt, -bounds, bounds)
        update_obstacles(obstacles, bounds, dt)

        obstacle_snapshot = [
            {
                "position": obs.position.copy(),
                "velocity": obs.velocity.copy(),
                "radius": obs.radius,
            }
            for obs in obstacles
        ]

        distance_to_goal = np.linalg.norm(goal - position)
        if distance_to_goal <= goal_radius:
            success = True

        for obs in obstacles:
            if np.linalg.norm(position - obs.position) <= obs.radius + 0.16:
                collided = True

        frames.append(
            {
                "position": position.copy(),
                "velocity": velocity.copy(),
                "goal": goal.copy(),
                "obstacles": obstacle_snapshot,
                "shield": triggered,
                "clearance": clearance,
                "step": step,
            }
        )

        if success or collided:
            break

    summary = {
        "success": success,
        "collided": collided,
        "steps": len(frames),
        "shield_count": shield_count,
        "min_clearance": float(min_clearance),
    }
    return frames, summary


def render(frames: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    path_x = []
    path_y = []

    def draw(frame_idx: int) -> None:
        frame = frames[frame_idx]
        ax.clear()
        ax.set_xlim(-6.2, 6.2)
        ax.set_ylim(-6.2, 6.2)
        ax.set_aspect("equal")
        ax.grid(alpha=0.25)
        ax.set_title("UAV Dynamic Navigation with Safety Shield")

        goal = frame["goal"]
        ax.scatter(goal[0], goal[1], marker="*", s=260, c="#2a9d8f", label="Goal")

        path_x.append(frame["position"][0])
        path_y.append(frame["position"][1])
        ax.plot(path_x, path_y, color="#457b9d", linewidth=2.0, label="Trajectory")

        color = "#d62828" if frame["shield"] else "#1d3557"
        ax.scatter(
            frame["position"][0],
            frame["position"][1],
            s=140,
            c=color,
            edgecolors="white",
            linewidths=1.5,
            label="UAV",
            zorder=5,
        )

        for idx, obs in enumerate(frame["obstacles"]):
            circle = plt.Circle(
                obs["position"],
                obs["radius"],
                color="#f4a261",
                alpha=0.72,
            )
            ax.add_patch(circle)
            ax.arrow(
                obs["position"][0],
                obs["position"][1],
                obs["velocity"][0] * 0.35,
                obs["velocity"][1] * 0.35,
                width=0.02,
                color="#bc6c25",
                length_includes_head=True,
            )
            if idx == 0:
                circle.set_label("Dynamic obstacle")

        ax.text(
            -6.0,
            5.55,
            f"step={frame['step']}  clearance={frame['clearance']:.2f}",
            fontsize=10,
            bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "none"},
        )
        ax.text(
            -6.0,
            5.00,
            "shield=ON" if frame["shield"] else "shield=OFF",
            fontsize=10,
            color="#d62828" if frame["shield"] else "#1d3557",
            bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "none"},
        )
        ax.legend(loc="lower right")

    ani = animation.FuncAnimation(fig, draw, frames=len(frames), interval=80, repeat=False)
    ani.save(output_path, writer=animation.PillowWriter(fps=12))
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lightweight safe UAV navigation demo.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--steps", type=int, default=220)
    parser.add_argument("--dt", type=float, default=0.10)
    parser.add_argument(
        "--save-gif",
        type=Path,
        default=Path("assets/demo/safe_uav_nav.gif"),
        help="Output GIF path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frames, summary = rollout(seed=args.seed, steps=args.steps, dt=args.dt)
    render(frames, args.save_gif)

    print(f"success={summary['success']}")
    print(f"collided={summary['collided']}")
    print(f"steps={summary['steps']}")
    print(f"shield_count={summary['shield_count']}")
    print(f"min_clearance={summary['min_clearance']:.3f}")
    print(f"gif_saved_to={args.save_gif}")


if __name__ == "__main__":
    main()
