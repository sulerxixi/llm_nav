include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "imu_link",
  published_frame = "odom",
  odom_frame = "odom",
  publish_to_tf = true,
  provide_odom_frame = false,
  publish_frame_projected_to_2d = false,
  use_pose_extrapolator = true,
  use_odometry = true,
  use_nav_sat = false,
  use_landmarks = false,
  num_laser_scans = 0,            
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 1,           
  lookup_transform_timeout_sec = 0.5,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,
  rangefinder_sampling_ratio = 1.,
  odometry_sampling_ratio = 1.,
  fixed_frame_pose_sampling_ratio = 1.,
  imu_sampling_ratio = 1.,
  landmarks_sampling_ratio = 1.,
}

-- 启用 3D 建图
MAP_BUILDER.use_trajectory_builder_3d = true

-- 配置 3D 轨迹构建器参数
TRAJECTORY_BUILDER_3D.num_accumulated_range_data = 1 -- 如果点云频率高，设为1；如果需要累积多帧才够一圈，增加此值
TRAJECTORY_BUILDER_3D.min_range = 0.2
TRAJECTORY_BUILDER_3D.max_range = 5.0

-- 滤波配置，减少计算量
TRAJECTORY_BUILDER_3D.voxel_filter_size = 0.05
TRAJECTORY_BUILDER_3D.high_resolution_adaptive_voxel_filter.max_length = 2.0
TRAJECTORY_BUILDER_3D.high_resolution_adaptive_voxel_filter.min_num_points = 50
TRAJECTORY_BUILDER_3D.low_resolution_adaptive_voxel_filter.max_length = 4.0
TRAJECTORY_BUILDER_3D.low_resolution_adaptive_voxel_filter.min_num_points = 200

-- 3D 必须使用 IMU
TRAJECTORY_BUILDER_3D.use_online_correlative_scan_matching = false -- 3D通常用 ceres 匹配
TRAJECTORY_BUILDER_3D.ceres_scan_matcher.translation_weight = 50.
TRAJECTORY_BUILDER_3D.ceres_scan_matcher.rotation_weight = 200.
TRAJECTORY_BUILDER_3D.ceres_scan_matcher.ceres_solver_options.max_num_iterations = 50
TRAJECTORY_BUILDER_3D.imu_gravity_time_constant = 20.

POSE_GRAPH.optimize_every_n_nodes = 320
POSE_GRAPH.constraint_builder.min_score = 0.62
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.66

-- 设置重力常数 (cartographer 默认是 9.8，如果你的IMU没校准可以不改)
-- TRAJECTORY_BUILDER_3D.imu_gravity_time_constant = 10.

return options
