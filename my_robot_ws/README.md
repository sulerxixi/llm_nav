# 自动移动机器人与 3D 激光雷达 (Livox MID-360) 仿真

## 1. 项目介绍

本项目基于 ROS 2 Humble 和 Gazebo Classic 设计了一个集成了固态激光雷达（Livox MID-360）的移动机器人仿真环境。
机器人本体采用差速驱动控制（`ros2_controllers`），通过加载 `ros2_livox_simulation` 插件在 Gazebo 中真实模拟 Livox 激光雷达的非重复扫描花瓣形点云特性，并通过 `FAST_LIO` (Lidar-Inertial Odometry) 算法实现高精度的 3D 建图和位姿估计。

各功能包功能如下：
- **`my_robot_description`**: 机器人核心描述文件，包含 URDF/xacro 模型定义、Gazebo 仿真配置项以及底盘差速控制器的配置。
- **`my_robot_navigation2`**: 导航相关配置及启动文件。
- **`my_robot_slam`**: 传统 2D SLAM 相关的配置及启动文件。
- **`livox_ros_driver2`**: 固态激光雷达 Livox 的官方 ROS 2 驱动，提供特有的 `CustomMsg` 消息类型支持。
- **`ros2_livox_simulation`**: 社区维护的 Livox 雷达 Gazebo 仿真插件，生成高逼真度的点云和 IMU 数据。
- **`fast_lio`**: 针对 Livox 等雷达深度优化的紧耦合激光雷达惯性里程计算法（FAST-LIO2），用于 3D 建图。

## 2. 环境与依赖

本项目开发平台信息如下：
- 系统版本： Ubuntu 22.04 LTS
- ROS 版本： ROS 2 Humble
- 关键底层依赖： `PCL >= 1.8`, `Eigen >= 3.3.4`

### 2.1 依赖安装

1. **安装控制与仿真底层工具**
```bash
sudo apt update
sudo apt install ros-humble-gazebo-ros-pkgs ros-humble-ros2-controllers ros-humble-xacro ros-humble-robot-state-publisher ros-humble-joint-state-publisher
```

2. **安装键盘控制工具**
```bash
sudo apt install ros-humble-teleop-twist-keyboard
```

3. **Livox SDK2 (需从源码编译)**
此环境依赖 Livox-SDK2 ，请在此工作空间外预先克隆并走 CMake 编译构建底层库。

## 3. 使用方法

### 3.1 构建功能包 (编译)

在工作空间 `my_robot_ws` 目录下运行：
```bash
colcon build --symlink-install
```

### 3.2 运行核心节点

请开启多个终端，并在每个终端下执行 `source install/setup.bash`。

**1. 启动 Gazebo 仿真环境**
加载基于 URDF 的差速小车并启动 Livox 激光雷达仿真插件。
```bash
ros2 launch my_robot_description gazebo_sim.launch.py
```

**2. 启动 FAST-LIO 进行 3D 建图**
通过 FAST-LIO 节点接收雷达扫描点或 IMU 数据，生成高精度的点云地图和 Odom 数据。
```bash
ros2 launch fast_lio mapping.launch.py config_file:=mid360.yaml
```

**3. 键盘控制小车移动**
使用键盘操作机器人在环境中漫游，配合 FAST-LIO 观察建图效果。
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
*(提示：使用 `i`、`,`、`j`、`l` 来控制前进、后退、左转与右转。若底盘不响应该控制，请在启动时重映射至正确的 /cmd_vel 话题)*
