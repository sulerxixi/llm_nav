#!/usr/bin/env python3
"""
semantic_to_keepout.py
=======================
读取 semantic_labels.yaml，将 keepout 类型的多边形/圆形区域
光栅化并写入 keepout_mask.pgm + keepout_mask.yaml。

用法:
    python3 semantic_to_keepout.py \
        --labels maps/semantic_labels.yaml \
        --output maps/keepout_mask

依赖:
    pip install pillow pyyaml

生成的文件符合 Nav2 KeepoutFilter / CostmapFilter 规范：
  - 白色像素 (205) = 自由（不影响代价地图）
  - 黑色像素 (0)   = 禁区（代价 = 254，机器人绝对不走）

坐标换算：
    pixel_x = (map_x - origin_x) / resolution          ← 列
    pixel_y = height - 1 - (map_y - origin_y) / resolution  ← 行（PGM 原点在左上角）
"""

import os
import sys
import math
import argparse
import yaml
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("请先安装 Pillow:  pip install pillow")


# ─────────────────────────────────────────────────────────────────────────────
# 坐标换算
# ─────────────────────────────────────────────────────────────────────────────

def world_to_pixel(x_m, y_m, origin_x, origin_y, resolution, height):
    """把地图坐标(米)转为图像像素(列, 行)。"""
    col = int((x_m - origin_x) / resolution)
    row = int(height - 1 - (y_m - origin_y) / resolution)
    return col, row


def polygon_world_to_pixel(polygon, origin_x, origin_y, resolution, height):
    """把多边形顶点列表从地图坐标转为像素坐标。"""
    return [
        world_to_pixel(p[0], p[1], origin_x, origin_y, resolution, height)
        for p in polygon
    ]


def circle_world_to_pixel(cx, cy, radius, origin_x, origin_y, resolution, height):
    """圆形中心和半径转像素。"""
    col, row = world_to_pixel(cx, cy, origin_x, origin_y, resolution, height)
    r_px = int(radius / resolution)
    return col, row, r_px


# ─────────────────────────────────────────────────────────────────────────────
# 主函数
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="语义标注 YAML → keepout PGM 掩码")
    parser.add_argument("--labels",
                        default="maps/semantic_labels.yaml",
                        help="输入的语义标注文件（默认: maps/semantic_labels.yaml）")
    parser.add_argument("--output",
                        default="maps/keepout_mask",
                        help="输出文件前缀（默认: maps/keepout_mask，"
                             "会生成 .pgm 和 .yaml）")
    parser.add_argument("--classes",
                        nargs="+",
                        default=["keepout"],
                        help="要写入禁区掩码的语义类别（默认: keepout）")
    args = parser.parse_args()

    # ── 1. 读取语义标注文件 ────────────────────────────────────────────────
    labels_path = Path(args.labels)
    if not labels_path.exists():
        sys.exit(f"[ERROR] 找不到标注文件: {labels_path}")

    with open(labels_path) as f:
        data = yaml.safe_load(f)

    map_info = data["map_info"]
    resolution = float(map_info["resolution"])
    origin_x   = float(map_info["origin"][0])
    origin_y   = float(map_info["origin"][1])
    ref_pgm    = labels_path.parent / map_info["image"]

    # ── 2. 从参考 PGM 读取地图尺寸 ────────────────────────────────────────
    if not ref_pgm.exists():
        sys.exit(f"[ERROR] 参考地图 PGM 不存在: {ref_pgm}\n"
                 "请在 map_info.image 中填写正确的 PGM 路径。")

    ref_img = Image.open(ref_pgm)
    width, height = ref_img.size          # PIL:  size = (width, height)
    print(f"[INFO] 参考地图尺寸: {width} x {height} 像素")
    print(f"[INFO] 分辨率: {resolution} m/px  原点: ({origin_x}, {origin_y})")
    print(f"[INFO] 地图范围 X: [{origin_x:.2f}, {origin_x + width*resolution:.2f}] m")
    print(f"[INFO] 地图范围 Y: [{origin_y:.2f}, {origin_y + height*resolution:.2f}] m")

    # ── 3. 创建全白掩码（205 = "自由"，符合 Nav2 标准）─────────────────────
    FREE_PIXEL    = 205   # 自由区域（不影响代价）
    BLOCKED_PIXEL = 0     # 禁区（代价 = 254）

    mask = Image.new("L", (width, height), FREE_PIXEL)
    draw = ImageDraw.Draw(mask)

    # ── 4. 光栅化各区域 ──────────────────────────────────────────────────
    zones = data.get("zones", [])
    drawn_count = 0

    for zone in zones:
        zone_id    = zone.get("id", "?")
        zone_class = zone.get("class", "")
        comment    = zone.get("comment", "")

        if zone_class not in args.classes:
            print(f"[SKIP] zone '{zone_id}' class='{zone_class}' (不在目标类别 {args.classes} 中)")
            continue

        # ── 多边形 ──────────────────────────────────────────────────────
        if "polygon" in zone:
            poly_world = zone["polygon"]
            poly_px = polygon_world_to_pixel(
                poly_world, origin_x, origin_y, resolution, height)
            draw.polygon(poly_px, fill=BLOCKED_PIXEL)
            print(f"[DRAW] 多边形 '{zone_id}'  顶点数={len(poly_world)}  {comment}")
            drawn_count += 1

        # ── 圆形 ────────────────────────────────────────────────────────
        elif "center" in zone and "radius" in zone:
            cx, cy   = zone["center"]
            radius   = float(zone["radius"])
            col, row, r_px = circle_world_to_pixel(
                cx, cy, radius, origin_x, origin_y, resolution, height)
            bbox = [col - r_px, row - r_px, col + r_px, row + r_px]
            draw.ellipse(bbox, fill=BLOCKED_PIXEL)
            print(f"[DRAW] 圆形   '{zone_id}'  中心=({cx},{cy})  半径={radius}m={r_px}px  {comment}")
            drawn_count += 1

        else:
            print(f"[WARN] zone '{zone_id}' 没有 polygon 或 center/radius 字段，已跳过")

    print(f"[INFO] 共绘制 {drawn_count} 个区域")

    # ── 5. 保存 PGM 和 YAML ───────────────────────────────────────────────
    out_prefix = Path(args.output)
    out_pgm    = out_prefix.with_suffix(".pgm")
    out_yaml   = out_prefix.with_suffix(".yaml")

    # 保存 PGM（8-bit 灰度）
    mask.save(str(out_pgm))
    print(f"[SAVE] PGM 掩码 → {out_pgm}")

    # 保存配套 YAML（与 Nav2 map_server 格式一致）
    mask_yaml = {
        "image":          out_pgm.name,
        "mode":           "trinary",
        "resolution":     resolution,
        "origin":         [origin_x, origin_y, 0.0],
        "negate":         0,
        "occupied_thresh": 0.65,
        "free_thresh":    0.25,
    }
    with open(out_yaml, "w") as f:
        yaml.dump(mask_yaml, f, default_flow_style=False, allow_unicode=True)
    print(f"[SAVE] 掩码 YAML  → {out_yaml}")
    print()
    print("下一步：")
    print("  1. 在 nav2_params.yaml 的 global_costmap.plugins 里加入 keepout_filter")
    print("  2. 在 navigation2.launch.py 里启动 costmap_filter_info_server")
    print("  3. 重新 colcon build，然后 ros2 launch my_robot_navigation2 navigation2.launch.py")


if __name__ == "__main__":
    main()
