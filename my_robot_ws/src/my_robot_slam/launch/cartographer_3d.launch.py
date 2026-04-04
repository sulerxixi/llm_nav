import os
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_share = get_package_share_directory('my_robot_slam')
    
    # 指向新的 3D 配置文件
    cartographer_config_dir = os.path.join(pkg_share, 'config')
    configuration_basename = 'my_robot_3d.lua'

    return LaunchDescription([
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            parameters=[{'use_sim_time': True}],
            arguments=[
                '-configuration_directory', cartographer_config_dir,
                '-configuration_basename', configuration_basename,
            ],
            remappings=[
                # 3D Cartographer 默认订阅 'points2' 话题 (sensor_msgs/PointCloud2)
                ('points2', '/camera_sensor/points'), 
                # odom 话题直接映射到 /odom
                ('odom', '/odom'),
                ('imu', '/imu'),
            ]
        ),

        # 3D 建图依然可以输出 2D 栅格图用于导航
        # 如果你不需要 2D 图，可以注释掉下面这个节点
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            output='screen',
            parameters=[{'use_sim_time': True}],
            arguments=['-resolution', '0.05', '-publish_period_sec', '1.0']
        ),
    ])
