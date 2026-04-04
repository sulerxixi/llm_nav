# 自动移动机器人

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

### 3.2 核心系统架构与 TF 坐标系

本项目的 TF 坐标树集成了物理仿真和算法流两大体系，通过在 `mapping.launch.py` 中发布静态 TF 将两者缝合：

1. **物理与底盘控制体系**：`odom` ➔ `base_footprint` ➔ `base_link` ➔ `livox_mid360`
   - 由 `robot_state_publisher` 和差速控制器发布，描述机器人的真实物理结构和基于轮速推算的里程计。
2. **FAST-LIO 算法建图体系**：`camera_init` ➔ `body`
   - `camera_init` 为算法开机第一眼的全局原点，`body` 为算法实时推算出的雷达位姿。
3. **坐标系缝合桥梁**：`odom` ➔ `camera_init`
   - 我们强制将算法建图原点与小车下地原点对齐，合并了这两套原本孤立的 TF 树，为 Nav2 提供全局参考。

### 3.3 运行核心节点

请开启多个终端，并在每个终端下执行 `source install/setup.bash`。

**1. 启动 Gazebo 仿真环境与机器人**
加载基于 URDF 的差速小车并启动 Livox 激光雷达仿真插件。
```bash
ros2 launch my_robot_description gazebo_sim.launch.py
```

**2. 启动 FAST-LIO 进行 3D 建图 (附带 RViz)**
通过 FAST-LIO 接收雷达和 IMU 数据生成高精度的 3D 点云地图，并自动弹出 RViz 界面。
```bash
ros2 launch fast_lio mapping.launch.py config_file:=mid360.yaml
```
*(在弹出的 RViz 中，请将 `Fixed Frame` 设置为 **`odom`** 或 **`camera_init`**，并添加 `/cloud_registered` 观察 3D 点云，添加 `/Odometry` 观察轨迹)*

**3. 启动点云降维转换 (3D 转 2D)**
将 FAST-LIO 生成的 3D 雷达点云（0.1~1.0米高度内），像切片机一样实时压缩拍扁成 2D 激光雷达扫描数据，供 Nav2 的代价地图避障使用。
```bash
ros2 launch my_robot_navigation2 pcl2scan.launch.py
```

**4. 启动 Nav2 导航框架**
接收降维后的 `/scan` 数据和合并后的 TF 树，进行全局路径规划和局部避障控制。
```bash
ros2 launch my_robot_navigation2 navigation2.launch.py
```

**5. 键盘控制小车移动 (测试用)**
使用键盘操作机器人在环境中漫游，观察建图和 3D/2D 点云的生成效果。
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
*(提示：使用 `i`、`,`、`j`、`l` 来控制。注意在测试 Nav2 自主导航时，不要手动发键盘速度指令以免发生控制冲突)*
