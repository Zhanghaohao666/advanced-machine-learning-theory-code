import argparse
from pathlib import Path
import random

import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(description="Simple NavRL goal-navigation demo.")
    parser.add_argument("--save-gif", type=str, default=None, help="Optional output path for a demo GIF.")
    parser.add_argument("--frames", type=int, default=300, help="Number of simulation frames.")
    parser.add_argument("--interval", type=int, default=20, help="Animation interval in milliseconds.")
    parser.add_argument("--no-show", action="store_true", help="Run without opening a matplotlib window.")
    return parser.parse_args()


ARGS = parse_args()

if ARGS.save_gif or ARGS.no_show:
    import matplotlib
    matplotlib.use("Agg")

import matplotlib.pyplot as plt
import torch
from matplotlib import animation
from matplotlib.patches import Circle

from agent import Agent
from env import generate_obstacles_grid
from utils import get_robot_state, get_ray_cast

# === Set random seed ===
SEED = 0 
random.seed(SEED)
np.random.seed(SEED)

# === Device ===
if torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")

print("Using device:", device)

# === Constants ===
MAP_HALF_SIZE = 20
OBSTACLE_REGION_MIN = -15
OBSTACLE_REGION_MAX = 15
MIN_RADIUS = 0.5
MAX_RADIUS = 1.0
MAX_RAY_LENGTH = 4.0
DT = 0.1
GOAL_REACHED_THRESHOLD = 0.3
HRES_DEG = 10.0
VFOV_ANGLES_DEG = [-10.0, 0.0, 10.0, 20.0]
GRID_DIV = 7


# === Setup ===
obstacles = generate_obstacles_grid(GRID_DIV, OBSTACLE_REGION_MIN, OBSTACLE_REGION_MAX, MIN_RADIUS, MAX_RADIUS)
robot_vel = np.array([0.0, 0.0])
goal = np.array([5.0, 18.0])
robot_pos = np.array([0.0, -18.0])
start_pos = robot_pos.copy()
target_dir = goal - robot_pos 
trajectory = []

# === NavRL Agent ===
agent = Agent(device=device)


# === Visualization setup ===
fig, ax = plt.subplots(figsize=(10, 10))
fig.patch.set_facecolor('#fefcfb')  # Light warm figure background
ax.set_facecolor('#fdf6e3')         # Slightly warm off-white axes background
ax.set_xlim(-MAP_HALF_SIZE, MAP_HALF_SIZE)
ax.set_ylim(-MAP_HALF_SIZE, MAP_HALF_SIZE)
ax.set_aspect('equal')
ax.set_title("NavRL Goal Navigation")
# ax.add_patch(Rectangle(
#                     (-MAP_HALF_SIZE, OBSTACLE_REGION_MIN),
#                     2 * MAP_HALF_SIZE,
#                     OBSTACLE_REGION_MAX - OBSTACLE_REGION_MIN,
#                     edgecolor='black',
#                     facecolor='lightgray',
#                     alpha=0.3,          # Slightly stronger for contrast
#                     linewidth=1.0,      # Thinner edge
#                     linestyle='--'      # Dotted border looks more natural
#                 ))
robot_dot, = ax.plot([], [], 'o', markersize=6, color="royalblue" , label='Robot', zorder=5)
goal_dot, = ax.plot([], [], marker='*', markersize=15, color='red', linestyle='None', label='Goal')
start_dot, = ax.plot([], [], marker='s', markersize=8, color='navy', label='Start', linestyle='None', zorder=3)
trajectory_line, = ax.plot([], [], '-', linewidth=1.5, color="lime", label='Trajectory')
ray_lines = [ax.plot([], [], 'r--', linewidth=0.5)[0] for _ in range(int(360 / HRES_DEG))]
ax.legend(loc='upper left')

for obs in obstacles:
    ax.add_patch(Circle((obs[0], obs[1]), obs[2], color='gray'))



# === Simulation update ===
def update(frame):
    global robot_pos, robot_vel, goal, trajectory, target_dir, start_pos

    # Goal reach check
    to_goal = goal - robot_pos
    dist = np.linalg.norm(to_goal)
    if dist < GOAL_REACHED_THRESHOLD:
        return


    # Get robot internal states
    robot_state = get_robot_state(robot_pos, goal, robot_vel, target_dir, device=device)

    # Get static obstacle representations
    static_obs_input, range_matrix, ray_segments = get_ray_cast(robot_pos, obstacles, max_range=MAX_RAY_LENGTH,
                                                       hres_deg=HRES_DEG,
                                                       vfov_angles_deg=VFOV_ANGLES_DEG,
                                                       start_angle_deg=np.degrees(np.arctan2(target_dir[1], target_dir[0])),
                                                       device=device)
    # Get dynamic obstacle representations (assume zero)
    dyn_obs_input = torch.zeros((1, 1, 5, 10), dtype=torch.float, device=device)

    # Target direction in tensor
    target_dir_tensor = torch.tensor(np.append(target_dir[:2], 0.0), dtype=torch.float, device=device).unsqueeze(0).unsqueeze(0)

    # Output the planned velocity
    velocity = agent.plan(robot_state, static_obs_input, dyn_obs_input, target_dir_tensor)

    # ---Visualizaton update---
    robot_dot.set_data([robot_pos[0]], [robot_pos[1]])
    start_dot.set_data([start_pos[0]], [start_pos[1]])
    goal_dot.set_data([goal[0]], [goal[1]])
    trajectory.append(robot_pos.copy())
    trajectory_np = np.array(trajectory)
    trajectory_line.set_data(trajectory_np[:, 0], trajectory_np[:, 1])

    # Update simulation states
    robot_pos += velocity * DT
    robot_vel = velocity.copy()

    return [robot_dot, goal_dot, trajectory_line, start_dot] + ray_lines

ani = animation.FuncAnimation(fig, update, frames=ARGS.frames, interval=ARGS.interval, blit=False)

if ARGS.save_gif:
    output_path = Path(ARGS.save_gif)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fps = max(1, int(round(1000 / max(ARGS.interval, 1))))
    ani.save(output_path, writer=animation.PillowWriter(fps=fps))
    print(f"Saved demo GIF to: {output_path}")

if not ARGS.no_show:
    plt.show()
else:
    plt.close(fig)
