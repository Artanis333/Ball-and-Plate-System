import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Arc
import numpy as np

plt.rcParams['font.family'] = ['SimHei', 'Microsoft YaHei', 'sans-serif']
plt.rcParams['mathtext.fontset'] = 'stix'

fig, ax = plt.subplots(1, 1, figsize=(11, 6.5))
ax.set_xlim(-0.5, 12.5)
ax.set_ylim(-1.5, 8.2)
ax.set_aspect('equal')
ax.axis('off')

# Base plate
base = FancyBboxPatch((0.5, -0.5), 11.5, 0.35, boxstyle="round,pad=0.02",
                       facecolor='#DDDDDD', edgecolor='#222', linewidth=2.5)
ax.add_patch(base)
ax.text(6.25, -0.9, '底座安装板', ha='center', va='top', fontsize=12, color='#222')

# Stepper motor
motor_w = 2.4
motor_h = 1.8
motor_x = 1.0
motor_y = -0.15
motor_cx = motor_x + motor_w / 2   # center x
motor_cy = motor_y + motor_h / 2   # center y
motor = FancyBboxPatch((motor_x, motor_y), motor_w, motor_h, boxstyle="round,pad=0.05",
                        facecolor='#CCDDEE', edgecolor='#222', linewidth=2)
ax.add_patch(motor)
ax.text(motor_cx, motor_y + motor_h + 0.3, '步进电机（X 轴）', ha='center', va='bottom', fontsize=11, color='#222')

# Motor shaft: a small filled circle at the center of the motor (axis end view)
shaft_x = motor_cx
shaft_y = motor_cy
shaft_r = 0.22
ax.add_patch(plt.Circle((shaft_x, shaft_y), shaft_r, facecolor='#444', edgecolor='#222', linewidth=2))
ax.text(shaft_x - 0.35, shaft_y - 0.55, '电机轴', ha='center', va='top', fontsize=10, color='#222')

# Rocker arm - horizontal, pivoting at shaft center
rocker_len = 2.2
rocker_start_x = shaft_x
rocker_start_y = shaft_y
rocker_end_x = rocker_start_x + rocker_len
rocker_end_y = shaft_y

ax.plot([rocker_start_x, rocker_end_x], [rocker_start_y, rocker_end_y],
        color='#444', linewidth=5, solid_capstyle='round')
ax.add_patch(plt.Circle((rocker_end_x, rocker_end_y), 0.18, facecolor='#888', edgecolor='#222', linewidth=2))

# Rotation arc around shaft
arc = Arc((shaft_x, shaft_y), 1.0, 0.5, angle=0, theta1=-12, theta2=12,
          color='#999', linewidth=1.2, linestyle='--')
ax.add_patch(arc)
ax.text(shaft_x + 1.1, shaft_y + 0.5, '摇臂', ha='center', va='bottom', fontsize=11, color='#222')

# Working plane
platform_y = 7.0
platform_left = 2.5
platform_right = 11.0
platform = FancyBboxPatch((platform_left, platform_y), platform_right - platform_left, 0.28,
                           boxstyle="round,pad=0.03",
                           facecolor='#E8E8E8', edgecolor='#222', linewidth=2.5)
ax.add_patch(platform)
ax.text((platform_left + platform_right)/2, platform_y + 0.55, '工作平面', ha='center', va='bottom',
        fontsize=12, fontweight='bold', color='#222')

# Universal joint under platform
uj_size = 0.35
uj_x = rocker_end_x
uj_y = platform_y - uj_size
ax.add_patch(plt.Circle((uj_x, uj_y), uj_size, facecolor='#FFFFFF', edgecolor='#222', linewidth=2.5))
ax.plot([uj_x-0.22, uj_x+0.22], [uj_y, uj_y], color='#222', linewidth=2)
ax.plot([uj_x, uj_x], [uj_y-0.22, uj_y+0.22], color='#222', linewidth=2)
ax.text(uj_x + 0.7, uj_y, '万向节', ha='left', va='center', fontsize=11, color='#222')

# Connecting rod: from rocker end to u-joint bottom
rod_bottom_x = rocker_end_x
rod_bottom_y = rocker_end_y
rod_top_x = uj_x
rod_top_y = uj_y - uj_size
ax.plot([rod_bottom_x, rod_top_x], [rod_bottom_y, rod_top_y],
        color='#444', linewidth=4.5, solid_capstyle='round')
ax.text(rod_bottom_x + 0.55, (rod_bottom_y + rod_top_y)/2, '连杆', ha='left', va='center', fontsize=11, color='#222')

# Ball on platform
ball_cx = 6.0
ball_cy = platform_y + 0.5
ball_radius = 0.35
ball = plt.Circle((ball_cx, ball_cy), ball_radius, facecolor='#FFFFFF', edgecolor='#222', linewidth=2.5)
ax.add_patch(ball)
ax.text(ball_cx, ball_cy + ball_radius + 0.3, '小球', ha='center', va='bottom', fontsize=11, color='#222')

# Central support column
col_x = 7.5
col_bottom = -0.15
col_top = platform_y
ax.plot([col_x, col_x], [col_bottom, col_top], color='#777', linewidth=3.5, linestyle='-', zorder=1)
ax.add_patch(plt.Circle((col_x, col_bottom), 0.22, facecolor='#999', edgecolor='#222', linewidth=2, zorder=2))
ax.add_patch(plt.Circle((col_x, col_top), 0.18, facecolor='#999', edgecolor='#222', linewidth=2, zorder=2))
ax.text(col_x + 0.55, (col_bottom + col_top)/2, '中心支撑柱', ha='left', va='center', fontsize=11, color='#222')

plt.tight_layout(pad=0.3)
plt.savefig(r'c:\Users\Lenovo\workspace_ccstheia\路一凡的毕业设计相关图片\mechanical_structure.pdf',
            dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.savefig(r'c:\Users\Lenovo\workspace_ccstheia\路一凡的毕业设计相关图片\mechanical_structure.png',
            dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print("Mechanical structure diagram (v4) saved.")
