"""Publish only a validated render, update the readable report, and package it."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def finalize(run_dir):
 r=json.loads((run_dir/'benchmark.json').read_text(encoding='utf-8'))
 assert r['passed'] and r['video']['passed'] and r['render_settings']['completed_frames']==192
 output=ROOT/'output'/'sugarfall.mp4'
 shutil.copy2(run_dir/'sugarfall.mp4',output)
 video=dict(r['video'],path=str(output))
 (ROOT/'reports'/'video_validation.json').write_text(json.dumps(video,indent=2),encoding='utf-8')
 shutil.copy2(run_dir/'benchmark.json',ROOT/'reports'/'benchmark.json')
 text=f'''# 甜甜圈重渲染实测

实测批次：`{r['run_id']}`。192 帧全部重新计算，8 秒、24 fps、960×800、24 samples，自适应阈值 0.06。

## 耗时

| 项目 | 实测 |
|---|---:|
| 上次完整渲染（历史日志） | 约 746 秒 / 12 分 26 秒 |
| 本次 Blender 进程耗时（含启动、退出、监测轮询间隔） | {r['render_wall_seconds']:.2f} 秒 |
| 本次逐帧循环耗时 | {r['render_loop_seconds']:.2f} 秒 |
| H.264 编码 | {r['encode_seconds']:.2f} 秒 |
| 本次总时间（含启动、渲染、编码、视频解码验证） | {r['total_seconds_including_validation']:.2f} 秒 |
| 单帧中位数 | {r['render_settings']['median_frame_seconds']:.3f} 秒 |
| 渲染耗时减少 | {r['render_time_reduction_percent']:.1f}% |
| 相对上次的渲染速度 | {r['speedup_vs_original']:.2f} 倍 |

这是与历史日志的比较，不是同一时刻的严格对照实验。画面尺寸、帧数和采样数保持不变，但降噪算法、数据复用、线程及进程调度一起调整，无法把改善单独归因于某一项。旧帧未用于新视频；OptiX 和原 OpenImageDenoise 的画面细节不会逐像素一致。

## 配置与负载

本机：Ryzen 7 5800H，8 核 16 线程；约 32 GB 内存；RTX 3070 Laptop GPU，8 GB 显存。检测时 NVIDIA 驱动版本 591.74，Blender 5.2.1 LTS。

| 指标 | 采样平均 | 采样最高 |
|---|---:|---:|
| Blender 占整机 CPU 比例 | {r['blender_cpu_percent_of_system']['mean']:.1f}% | {r['blender_cpu_percent_of_system']['max']:.1f}% |
| 整机 CPU 占用 | {r['system_cpu_percent']['mean']:.1f}% | {r['system_cpu_percent']['max']:.1f}% |
| 整机 GPU 占用 | {r['gpu_system_utilization_percent']['mean']:.1f}% | {r['gpu_system_utilization_percent']['max']:.1f}% |
| 整机显存使用 | {r['gpu_system_memory_mib']['mean']/1024:.2f} GiB | {r['gpu_system_memory_mib']['max']/1024:.2f} GiB |
| GPU 温度 | {r['gpu_temperature_c']['mean']:.1f} °C | {r['gpu_temperature_c']['max']:.0f} °C |
| Blender 进程工作集内存 | {r['blender_rss_mib']['mean']:.0f} MiB | {r['blender_rss_mib']['max']:.0f} MiB |

运行期间整机可用内存最低约 {r['minimum_system_ram_available_gib']:.1f} GiB。以上来自 {r['telemetry_samples']} 次、约每两秒一次的采样，不包含视频编码阶段；采样可能错过瞬时峰值。GPU 指标包含桌面及其他应用，不是只统计 Blender。CPU 进程占用已除以逻辑核心数，可与任务管理器的整机比例比较。上次没有同口径负载记录，因此不提供虚构的 CPU 前后平均对比。

## 做了哪些优化

1. 仅启用 RTX 的 OptiX 渲染设备，CPU 光线追踪设备关闭。
2. 降噪从 CPU OpenImageDenoise 换为 GPU OptiX。
3. 开启 Persistent Data，让动画帧复用渲染数据。
4. Blender 渲染线程、OpenMP/MKL 上限设为 8，使用低于普通任务的进程优先级。
5. H.264 软件编码限制为 4 线程。

当前场景下，8 GB 显存和 32 GB 内存都有余量，暂时没有为此升级硬件的必要。没有修改驱动、电源策略、超频、系统服务或 Python 环境。新文件和渲染缓存全部写入 E 盘。

Blender 官方说明，Persistent Data 可以加快重新渲染和动画渲染，代价是保留更多内存；本次已实测内存余量。[官方性能说明](https://docs.blender.org/manual/en/4.1/render/cycles/render_settings/performance.html)。[GPU 渲染官方说明](https://docs.blender.org/manual/en/5.0/render/cycles/gpu_rendering.html)

## 验证与原始记录

- MP4 完整解码通过：192 帧、24 fps、8 秒、960×800。
- 渲染前后主工程 SHA-256 相同：`{r['source_sha256']}`。
- 视觉抽查记录：{r.get('visual_reviewed_frames', '未记录人工视觉检查')}；自动解码验证不替代视觉检查。
- [本次原始报告](../reports/{r['run_id']}/benchmark.json)
- [逐帧耗时](../reports/{r['run_id']}/frame_times.jsonl)
- [CPU/GPU 采样](../reports/{r['run_id']}/telemetry.jsonl)
- [Blender 日志](../reports/{r['run_id']}/blender.log)
- [新视频](../output/sugarfall.mp4)
- [首轮视频](../archive/first-render/sugarfall.mp4)
'''
 (ROOT/'docs'/'render-benchmark.md').write_text(text,encoding='utf-8')
 subprocess.run([sys.executable,'-B',str(ROOT/'scripts'/'package_delivery.py')],check=True)
 print('Published '+str(output),flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser()
 parser.add_argument('--run-dir',type=Path)
 args=parser.parse_args()
 selected=args.run_dir or Path(json.loads((ROOT/'reports'/'latest_run.json').read_text(encoding='utf-8'))['report_dir'])
 finalize(selected)
