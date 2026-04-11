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

### ⚠️ 重要提醒：Git LFS 与仓库克隆

本项目包含了体积较大的 Gazebo 仿真模型压缩包 (`models.zip`，约 287MB)。我们使用了 **Git Large File Storage (LFS)** 来管理该文件。

**如果你要克隆本项目，请务必先安装 Git LFS，否则模型文件将无法正确下载，导致仿真环境缺失模型！**

#### 正确的克隆步骤：

1. **安装 Git LFS (如果尚未安装)**:
   ```bash
   sudo apt update
   sudo apt install git-lfs
   git lfs install
   ```

2. **克隆仓库并拉取大文件**:
   你可以直接使用 `git clone`，只要 `git lfs` 安装配置正常，它会自动拉取真实文件：
   ```bash
   git clone https://github.com/sulerxixi/llm_nav.git
   ```

   *(如果你已经不小心用普通方式 clone 了，且 `models.zip` 只有几百字节，可以通过运行 `git lfs pull` 来补救下载真实文件。)*

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

### 3.2 核心系统架构与 TF 坐标系 (单线高精动态 SLAM)

本项目的最新 TF 坐标树经过深度重构，摒弃了 Gazebo 不准确的轮式里程计（禁用打滑误差），由 FAST-LIO 高精度雷达里程计**完全接管**底层物理车体的定位。实现了“边建图边导航”（Dynamic SLAM + Navigation）的终极形态。

**架构核心路线（完美单线串联）：**
`map` ➔ `odom` ➔ `camera_init` ➔ `body` ➔ `base_footprint` ➔ `base_link` ➔ `livox_mid360`

1. **`map` ➔ `odom`**: 由 Nav2 的 `slam_toolbox` 动态发布，实时修正全图漂移。
2. **`odom` ➔ `camera_init`**: 静态TF，将 FAST-LIO 世界原点与标准里程计起点绑定。
3. **`camera_init` ➔ `body`**: 由 FAST-LIO 实时高频发布的**超高精度激光里程计**。
4. **`body` ➔ `base_footprint`**: 静态TF，将雷达算出的位姿强行绑定到底盘地面投影上，使得雷达接管了整车的物理移动。
5. **代价地图处理**: 无图漫游模式。废弃老旧的静态图层，点云 (`/cloud_registered`) 被 `pcl2scan` 实时拍扁为 2D `/scan` 激光线，直接喂给 Nav2 构建实时的动态代价地图（Costmap）。

### 3.3 运行核心节点（完整 5 步启动流）

请在工作空间 `my_robot_ws` 下开启多个终端，并在每个终端执行 `source install/setup.bash`。

**1. 启动 Gazebo 物理仿真环境**
加载底盘模型（已关闭假轮式 odom 发布），启动 Livox 激光雷达仿真。
```bash
ros2 launch my_robot_description gazebo_sim.launch.py
```

**2. 启动 FAST-LIO 3D 激光建图与高精定位**
接收 3D 雷达和 IMU 数据，生成高精度的 3D 点云地图并发布 `body` 位姿（自动弹出 RViz 呈现 3D 震撼视角）。
```bash
ros2 launch fast_lio mapping.launch.py config_file:=mid360.yaml
```

**3. 启动点云降维压缩 (3D 转 2D)**
将 FAST-LIO 庞大的 3D 点云（高度 -0.1~1.0米）像切片机一样“拍扁”成 2D 激光射线 (`/scan`)，专供 Nav2 避障。
```bash
ros2 launch my_robot_navigation2 pcl2scan.launch.py
```

**4. 启动 Nav2 (动态 SLAM 导航模式)**
启动自带 `slam_toolbox` 的 Nav2。它会在 RViz 中以“拨开战争迷雾”的形式实时生成 2D 栅格地图。您可以在 RViz 中直接使用 `2D Goal Pose` 指挥小车前往未知区域探索。
```bash
ros2 launch my_robot_navigation2 navigation2.launch.py
```

**5. 键盘控制小车漫游 (可选)**
如果您想手动建图探索房间，可以使用键盘操控。
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
*(提示：使用 `i`、`,`、`j`、`l` 来控制。注意在测试 Nav2 自主导航时，不要手动发键盘速度指令以免发生控制冲突)*

## Gazebo 模型安装说明

本项目的 Gazebo 模型压缩包位于：

```bash
/home/xixi5/llm_nav/my_robot_ws/src/my_robot_description/models.zip
```

使用前需要将模型手动安装到本机的 Gazebo 模型目录：

```bash
~/.gazebo/models
```

在文件管理器中按 `Ctrl + H` 可以显示隐藏文件夹，找到 `.gazebo` 后将模型解压到其中的 `models` 目录。

完成后即可正常使用示例 Gazebo 环境；如有需要，也可以自行替换或扩展 Gazebo 模型。

file:///home/xixi5/%E5%9B%BE%E7%89%87/%E6%88%AA%E5%9B%BE/%E6%88%AA%E5%9B%BE%202026-04-08%2013-06-23.png
