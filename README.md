# Ball-and-Plate System

基于视觉反馈的板球系统——低成本嵌入式实验平台。

西安电子科技大学 · 机电工程学院 · 自动化专业 · 本科毕业设计 (2026)

**演示地址：** <https://artanis333.github.io/Ball-and-Plate-System/>

---

## 系统概述

板球系统（Ball-and-Plate System）是一类典型的非线性、强耦合、欠驱动控制对象。本项目搭建了一套基于嵌入式视觉的低成本实验平台，完成了从视觉检测、控制计算到电机执行的完整闭环验证。

### 硬件架构

| 模块 | 型号 | 功能 |
|------|------|------|
| 视觉 | MaixCam | 端侧图像处理，LAB 色彩空间白球检测 |
| 主控 | MSPM0G3507 (TI) | 三环串级 PID 控制，STEP/DIR 脉冲输出 |
| 姿态 | JY931 (维特智能) | 平台倾角实时测量，角度内环反馈 |
| 驱动 | D36A (ATD5984) | 双路 32 细分步进电机驱动 |
| 执行 | 42 步进电机 ×2 | 经摇臂-连杆-万向节传动平台倾斜 |

### 控制策略

三环串级 PID（外环位置 → 中环速度 → 内环角度），采样周期 20 ms (50 Hz)，角度内环以 JY931 实测倾角为反馈。

---

## 仓库结构

```
├── index.html              # 毕业设计答辩演示文稿 (Reveal.js)
├── demo_video.mp4          # 实物闭环运行演示视频
├── images/                 # 演示文稿图片
├── firmware/               # MSPM0G3507 主控固件 (Code Composer Studio / TI Clang)
│   ├── main.c / main.h     #   主程序：定时中断、串口通信、控制逻辑
│   ├── pid.c / pid.h       #   三环串级 PID 实现
│   ├── mspm0-modules.syscfg #  TI SysConfig 外设配置
│   ├── Drivers/            #   传感器驱动 (JY931, MPU6050, BNO08X, OLED)
│   └── traj.awk            #   轨迹数据处理辅助脚本
├── vision/                 # MaixCam 视觉端代码 (MicroPython)
│   ├── cam.py              #   白球检测与坐标串口回传
│   └── maixcam_ball_tracker.py  # 备用追踪方案
├── simulink/               # Simulink 仿真模型
│   ├── BallControl3Loop_step.slx        # 定点阶跃响应
│   ├── BallControl3Loop_disturbance.slx # 扰动恢复
│   └── BallControl3Loop_cycle.slx       # 圆轨迹跟踪
├── mechanical/             # 机械结构
│   ├── 材料清单.xlsx        #   完整材料清单（含淘宝链接）
│   ├── 硬件BOM清单_待填写.xlsx # 硬件 BOM 表
│   ├── MAIXCAM支撑架.stl    #   3D 打印件
│   ├── 中心万向节连接件.stl
│   ├── 侧边万向节连接件.stl
│   └── 光轴底座.stl
├── analysis/               # 数据分析脚本
│   ├── analyze_ball_track.py           # 小球轨迹分析
│   └── draw_mechanical_structure.py    # 机械结构示意图绘制
└── data/
    └── ball_track_1777283591903.csv    # 实物实验轨迹样本数据
```

---

## 复现指南

### 硬件搭建

1. 按 `mechanical/材料清单.xlsx` 采购全部元器件（全部可淘宝购买）
2. 3D 打印 `mechanical/` 目录下的 STL 文件（支撑架、万向节连接件、光轴底座）
3. 组装铝型材框架，安装步进电机、摇臂连杆、万向节和平台面板
4. 将 MaixCam 摄像头安装于平台正上方约 340 mm 处，镜头垂直向下
5. 按引脚定义连接各模块（UART / GPIO）

### 软件部署

**主控端 (MSPM0G3507):**
1. 使用 Code Composer Studio (Theia) 导入 `firmware/` 目录
2. 编译并烧录到 MSPM0G3507

**视觉端 (MaixCam):**
1. 将 `vision/cam.py` 上传至 MaixCam
2. 确认串口通信参数：波特率 115200，6 字节自定义协议

**仿真环境:**
1. 使用 MATLAB/Simulink 打开 `simulink/` 目录下的 `.slx` 文件
2. 仿真参数已预设，可直接运行

### 联调验收

四项标准全部满足后进入性能测试：
1. **通信稳定** — 无连续丢帧或错误帧
2. **周期稳定** — 主控 20 ms 中断不被阻塞
3. **输出连续** — STEP/DIR 信号无异常跳变
4. **目标可收敛** — 给定固定目标点后系统稳定趋近

---

## 实验数据

实物实验在两种工况下验证了系统性能：

| 工况 | 关键指标 |
|------|----------|
| 定点控制 | 收敛时间 ≈ 5.84 s，稳态工作区间约 75 mm |
| 圆轨迹跟踪 | 双轴平均速度趋于零，Y/X 速度摆幅比 ≈ 1.18 |

仿真与实物差异的四个主要来源：像素量化噪声 (256×256) · 步进电机转矩脉动 · 双轴机械不对称 · 通信链路丢帧 (0.07%)

---

## 致谢

- 指导教师：秦红波 老师
- 西安电子科技大学 · 机电工程学院

## License

MIT License
