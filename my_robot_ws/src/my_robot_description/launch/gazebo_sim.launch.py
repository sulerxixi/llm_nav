import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # 获取默认路径
    robot_name_in_model = "my_robot"
    urdf_tutorial_path = get_package_share_directory('my_robot_description')
    default_model_path = urdf_tutorial_path + '/urdf/my_robot/my_robot.urdf.xacro'
    default_world_path = urdf_tutorial_path + '/world/room.world'
    # 为 Launch 声明参数
    action_declare_arg_mode_path = launch.actions.DeclareLaunchArgument(
        name='model', default_value=str(default_model_path),
        description='URDF 的绝对路径')
    # 获取文件内容生成新的参数
    robot_description = launch_ros.parameter_descriptions.ParameterValue(
        launch.substitutions.Command(
            ['xacro ', launch.substitutions.LaunchConfiguration('model')]),
        value_type=str)
  	
    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}]
    )

    # 通过 IncludeLaunchDescription 包含另外一个 launch 文件
    launch_gazebo = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource([get_package_share_directory(
            'gazebo_ros'), '/launch', '/gazebo.launch.py']),
      	# 传递参数
        launch_arguments=[('world', default_world_path),('verbose','true')]
    )
    # 请求 Gazebo 加载机器人
    spawn_entity_node = launch_ros.actions.Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', '/robot_description',
                   '-entity', robot_name_in_model, 
                   '-x', '0.0', 
                   '-y', '0.0', 
                   '-z', '0.0'])
    
    # 加载并激活 my_robot_joint_state_broadcaster 控制器
    load_joint_state_controller = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
            'my_robot_joint_state_broadcaster'],
        output='screen'
    )

    # 加载并激活 my_robot_effort_controller 控制器
    load_my_robot_effort_controller = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active','my_robot_effort_controller'], 
        output='screen')
    
    load_my_robot_diff_drive_controller = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active','my_robot_diff_drive_controller'], 
        output='screen')
    
    # 将 /points_raw 转换成二维的 /scan 给 Nav2 (注释掉，使用独立启动)
    # pointcloud_to_laserscan_node = launch_ros.actions.Node(
    #     package='pointcloud_to_laserscan',
    #     executable='pointcloud_to_laserscan_node',
    #     name='pointcloud_to_laserscan',
    #     remappings=[
    #         ('cloud_in', '/points_raw'),
    #         ('scan', '/scan')
    #     ],
    #     parameters=[{
    #         'target_frame': 'laser_link',    # 和雷达坐标系一致
    #         'transform_tolerance': 0.01,
    #         'min_height': 0.1,               # 提取点云的最低高度：0.1米（过滤掉地面）
    #         'max_height': 2.0,               # 提取点云的最高高度：2.0米（满足"所有高度"）
    #         'angle_min': -3.14159,           # -180度
    #         'angle_max': 3.14159,            # 180度
    #         'angle_increment': 0.0087,       # 角度分辨率
    #         'scan_time': 0.1,                # 扫描时间
    #         'range_min': 0.2,
    #         'range_max': 100.0,
    #         'use_inf': True,
    #         'inf_epsilon': 1.0,
    #         # 解决 QoS 不兼容问题，使用 Best Effort 等来匹配常见的 sensor_msgs 策略
    #         'qos_overrides./scan.publisher.reliability': 'best_effort'
    #     }]
    # )
    
    return launch.LaunchDescription([
        action_declare_arg_mode_path,
        robot_state_publisher_node,
        launch_gazebo,
        spawn_entity_node,
        # pointcloud_to_laserscan_node,
        # 事件动作，当加载机器人结束后执行    
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=spawn_entity_node,
                on_exit=[load_joint_state_controller],)
            ),
        # 事件动作，load_my_robot_diff_drive_controller
        launch.actions.RegisterEventHandler(
        event_handler=launch.event_handlers.OnProcessExit(
            target_action=load_joint_state_controller,
            on_exit=[load_my_robot_diff_drive_controller],)
            ),
    ])
