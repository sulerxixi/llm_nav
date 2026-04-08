import os
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    my_robot_navigation2_dir = get_package_share_directory('my_robot_navigation2')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    rviz_config_dir = os.path.join(nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz')
    
    use_sim_time = launch.substitutions.LaunchConfiguration('use_sim_time', default='true')
    nav2_param_path = launch.substitutions.LaunchConfiguration('params_file', default=os.path.join(my_robot_navigation2_dir, 'config', 'nav2_params.yaml'))

    return launch.LaunchDescription([
        launch.actions.DeclareLaunchArgument('use_sim_time', default_value=use_sim_time),
        launch.actions.DeclareLaunchArgument('params_file', default_value=nav2_param_path),

        launch.actions.IncludeLaunchDescription(
            PythonLaunchDescriptionSource([nav2_bringup_dir, '/launch', '/bringup_launch.py']),
            launch_arguments={
                'slam': 'True',
                'map': '',
                'use_sim_time': use_sim_time,
                'params_file': nav2_param_path
            }.items(),
        ),

        # Optional: Rviz for Nav2 (Requires a clean TF tree)
        launch_ros.actions.Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2_nav',
            arguments=['-d', rviz_config_dir],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'),
    ])
