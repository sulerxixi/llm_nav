import os
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 获取配置目录
    pkg_share = get_package_share_directory('my_robot_slam')
    
    # Lua 配置文件名
    cartographer_config_dir = os.path.join(pkg_share, 'config')
    configuration_basename = 'my_robot.lua'

    return LaunchDescription([
        # 1. 启动 Cartographer 主节点
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            parameters=[{'use_sim_time': True}], # 如果是仿真，设为 True
            arguments=[
                '-configuration_directory', cartographer_config_dir,
                '-configuration_basename', configuration_basename,
            ],
            # 这里的重映射非常重要，确保话题名称对齐
            remappings=[
                ('scan', '/scan'),   # 将 Cartographer 的 scan 重映射到你机器人的雷达话题
                ('odom', '/odom'),   # 同理
                ('imu', '/imu'),
            ]
        ),

        # 2. 启动 Occupancy Grid 节点 (将子图转换为栅格地图)
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            output='screen',
            parameters=[{'use_sim_time': False}],
            arguments=['-resolution', '0.05', '-publish_period_sec', '1.0']
        ),
    ])