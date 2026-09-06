"""Run inside Blender; render all frames with real timings and no cache reuse."""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path
import bpy

parser=argparse.ArgumentParser()
parser.add_argument('--frames-dir',type=Path,required=True)
parser.add_argument('--report-dir',type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
args.frames_dir.mkdir(parents=True,exist_ok=True)
args.report_dir.mkdir(parents=True,exist_ok=True)
if any(args.frames_dir.glob('sugarfall_*.png')):raise RuntimeError('Frames directory must be empty.')
scene=bpy.context.scene
cp=bpy.context.preferences.addons['cycles'].preferences
cp.compute_device_type='OPTIX'
cp.get_devices()
for device in cp.devices:device.use=device.type=='OPTIX'
if not any(d.use and d.type=='OPTIX' for d in cp.devices):raise RuntimeError('No OptiX GPU; refusing CPU fallback.')
scene.render.engine='CYCLES'
scene.cycles.device='GPU'
scene.cycles.use_denoising=True
scene.cycles.samples=24
scene.cycles.adaptive_threshold=.06
scene.render.resolution_x=960
scene.render.resolution_y=800
scene.render.resolution_percentage=100
scene.render.fps=24
scene.render.fps_base=1
scene.frame_start=1
scene.frame_end=192
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.render.image_settings.color_depth='8'
scene.render.image_settings.compression=15
scene.render.threads_mode='FIXED'
scene.render.threads=8
scene.cycles.denoiser='OPTIX'
scene.cycles.denoising_use_gpu=True
scene.render.use_persistent_data=True
settings={'blender':bpy.app.version_string,'scene_file':bpy.data.filepath,
 'render_device':scene.cycles.device,'compute_device_type':cp.compute_device_type,
 'devices':[{'name':d.name,'type':d.type,'enabled':d.use} for d in cp.devices],
 'denoiser':scene.cycles.denoiser,'gpu_denoising':scene.cycles.denoising_use_gpu,
 'threads_mode':scene.render.threads_mode,'threads':scene.render.threads,
 'persistent_data':scene.render.use_persistent_data,'samples':scene.cycles.samples,
 'adaptive_threshold':scene.cycles.adaptive_threshold,'resolution':[960,800],
 'frames':192,'fps':24,'objects':len(scene.objects)}
(args.report_dir/'render_settings.json').write_text(json.dumps(settings,indent=2),encoding='utf-8')
started=time.perf_counter()
times=[]
for frame in range(1,193):
 before=time.perf_counter()
 scene.frame_set(frame)
 output=args.frames_dir/f'sugarfall_{frame:04d}.png'
 scene.render.filepath=str(output)
 bpy.ops.render.render(write_still=True)
 if not output.exists():raise RuntimeError(f'Missing frame {frame}')
 elapsed=time.perf_counter()-before
 times.append(elapsed)
 progress={'frame':frame,'total':192,'frame_seconds':elapsed,'elapsed_render_seconds':time.perf_counter()-started}
 with (args.report_dir/'frame_times.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(progress)+'\n')
 temporary=args.report_dir/'progress.tmp'
 temporary.write_text(json.dumps(progress),encoding='utf-8')
 temporary.replace(args.report_dir/'progress.json')
 print(f'FRAME {frame}/192: {elapsed:.3f}s',flush=True)
report={**settings,'completed_frames':len(times),'render_loop_seconds':time.perf_counter()-started,
 'mean_frame_seconds':statistics.mean(times),'median_frame_seconds':statistics.median(times),
 'first_frame_seconds':times[0],'last_frame_seconds':times[-1]}
(args.report_dir/'render_result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('RENDER_COMPLETE '+json.dumps(report),flush=True)
