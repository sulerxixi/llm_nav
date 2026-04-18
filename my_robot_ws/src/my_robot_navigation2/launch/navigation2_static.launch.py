import os
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    my_robot_navigation2_dir = get_package_share_directory('my_robot_navigation2')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    rviz_config_dir = os.path.join(nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz')
    
    # 指向你已经建好的地图的 yaml 文件
    # 注意：Nav2 加载的是 yaml 文件，yaml 文件中会指明对应的 pgm 图片路径
    default_map_path = os.path.join(my_robot_navigation2_dir, 'maps', 'my_room_map.yaml')
    
    use_sim_time = launch.substitutions.LaunchConfiguration('use_sim_time', default='true')
    nav2_param_path = launch.substitutions.LaunchConfiguration('params_file', default=os.path.join(my_robot_navigation2_dir, 'config', 'nav2_params.yaml'))
    map_yaml_file = launch.substitutions.LaunchConfiguration('map', default=default_map_path)

    return launch.LaunchDescription([
        launch.actions.DeclareLaunchArgument('use_sim_time', default_value=use_sim_time),
        launch.actions.DeclareLaunchArgument('params_file', default_value=nav2_param_path),
        launch.actions.DeclareLaunchArgument('map', default_value=map_yaml_file, description='Full path to map yaml file to load'),

        # 调用 bringup_launch.py 时，将 slam 参数设为 False，并传入 map 参数
        launch.actions.IncludeLaunchDescription(
            PythonLaunchDescriptionSource([nav2_bringup_dir, '/launch', '/bringup_launch.py']),
            launch_arguments={
                'slam': 'False',       # 关闭在线 SLAM
                'map': map_yaml_file,  # 传入已知的静态地图
                'use_sim_time': use_sim_time,
                'params_file': nav2_param_path
            }.items(),
        ),

        # 启动 Rviz
        launch_ros.actions.Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2_nav',
            arguments=['-d', rviz_config_dir],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'),
    ])
