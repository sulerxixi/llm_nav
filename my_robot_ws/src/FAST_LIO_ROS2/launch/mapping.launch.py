import os
import launch
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration

def generate_launch_description():
    fast_lio_path = get_package_share_directory('fast_lio')
    
    declare_use_sim_time_cmd = launch.actions.DeclareLaunchArgument('use_sim_time', default_value='true')
    declare_config_path_cmd = launch.actions.DeclareLaunchArgument('config_path', default_value=os.path.join(fast_lio_path, 'config'))
    declare_config_file_cmd = launch.actions.DeclareLaunchArgument('config_file', default_value='mid360.yaml')
    
    fast_lio_node = Node(
        package='fast_lio',
        executable='fastlio_mapping',
        parameters=[
            PathJoinSubstitution([
                LaunchConfiguration('config_path'),
                LaunchConfiguration('config_file')
            ]),
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        output='screen'
    )
    
    # 💥 将 FAST-LIO 的世界原点(camera_init) 对齐到小车起点的(odom)上
    # 这样就可以把 FAST-LIO 产生的 TF 树和 Gazebo 的 TF 树连成一整棵树，避免 body 出现两个父节点的冲突
    tf_camera_init_to_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'odom', 'camera_init']
    )
    
    # 💥 将 FAST-LIO 算出的高精度车体位姿(body)，桥接到小车的物理脚印(base_footprint)上
    # 这样雷达里程计就正式接管了整台车的底盘，单线 TF 设计完美避障
    tf_body_to_base_footprint = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'body', 'base_footprint']
    )
    
    # 新增 RViz2 节点，自带 FAST-LIO 的配置文件
    rviz_config_path = os.path.join(fast_lio_path, 'rviz', 'fastlio.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        output='screen'
    )
    
    return launch.LaunchDescription([
        declare_use_sim_time_cmd,
        declare_config_path_cmd,
        declare_config_file_cmd,
        fast_lio_node,
        tf_camera_init_to_odom,
        tf_body_to_base_footprint,
        rviz_node
    ])
