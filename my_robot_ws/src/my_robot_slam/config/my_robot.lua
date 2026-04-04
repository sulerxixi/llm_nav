include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "imu_link", -- 如果有IMU，通常设为 imu_link
  published_frame = "odom",     -- Cartographer 发布 map 到 odom 的变换
  odom_frame = "odom",          -- 里程计坐标系
  provide_odom_frame = false,   -- 如果你的机器人已有里程计节点发布 odom，设为 false
  publish_frame_projected_to_2d = false,
  use_pose_extrapolator = true,
  use_odometry = true,          -- 是否使用里程计数据
  use_nav_sat = false,
  use_landmarks = false,
  num_laser_scans = 1,          -- 激光雷达数量
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,
  lookup_transform_timeout_sec = 0.2,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,
  rangefinder_sampling_ratio = 1.,
  odometry_sampling_ratio = 1.,
  fixed_frame_pose_sampling_ratio = 1.,
  imu_sampling_ratio = 1.,
  landmarks_sampling_ratio = 1.,
}

MAP_BUILDER.use_trajectory_builder_2d = true

-- 根据你的雷达性能调整以下参数
TRAJECTORY_BUILDER_2D.min_range = 0.1
TRAJECTORY_BUILDER_2D.max_range = 8.0
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 8.5
TRAJECTORY_BUILDER_2D.use_imu_data = true -- 如果没有IMU，必须设为false
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true 

return options