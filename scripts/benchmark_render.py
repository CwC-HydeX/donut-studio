"""Full render with resource sampling, encoding and a reproducible timing report."""
import datetime
import atexit
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import time
import psutil
from encode_video import encode_sequence

ROOT=Path(__file__).resolve().parents[1]

def gpu_sample():
 fields=['utilization.gpu','memory.used','temperature.gpu','power.draw','clocks.sm']
 try:
  value=subprocess.run(['nvidia-smi','--query-gpu='+','.join(fields),'--format=csv,noheader,nounits'],
   capture_output=True,text=True,timeout=3,creationflags=subprocess.CREATE_NO_WINDOW)
  if value.returncode:return {'error':value.stderr.strip()[:200]}
  return {key:(float(part.strip()) if part.strip().replace('.','',1).isdigit() else None)
   for key,part in zip(fields,value.stdout.splitlines()[0].split(','))}
 except Exception as error:return {'error':str(error)}

def main():
 run_id=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_optimized'
 run_dir=ROOT/'reports'/run_id
 frames=ROOT/'cache'/'frames'/run_id
 run_dir.mkdir(parents=True,exist_ok=False)
 frames.mkdir(parents=True,exist_ok=False)
 scene=ROOT/'donut_studio.blend'
 source_hash=hashlib.sha256(scene.read_bytes()).hexdigest()
 environment=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',
  TEMP=str(ROOT/'cache'/'tmp'),TMP=str(ROOT/'cache'/'tmp'),OMP_NUM_THREADS='8',MKL_NUM_THREADS='8')
 (ROOT/'cache'/'tmp').mkdir(parents=True,exist_ok=True)
 command=['E:/Blender/blender.exe','--background',str(scene),'--offline-mode','--threads','8','--python',
  str(ROOT/'scripts'/'render_frames.py'),'--','--frames-dir',str(frames),'--report-dir',str(run_dir)]
 (run_dir/'run.json').write_text(json.dumps({'command':command,'run_id':run_id,'source_sha256':source_hash,
  'logical_cpus':psutil.cpu_count(),'physical_cpus':psutil.cpu_count(logical=False),
  'ram_gib':psutil.virtual_memory().total/2**30,'threads_env':8},indent=2),encoding='utf-8')
 (ROOT/'reports'/'latest_run.json').write_text(json.dumps({'run_id':run_id,'report_dir':str(run_dir),'frames_dir':str(frames)}),encoding='utf-8')
 print('RUN '+run_id,flush=True)
 began=time.perf_counter()
 samples=[]
 last_print=-30
 with (run_dir/'blender.log').open('w',encoding='utf-8') as log:
  process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=environment,creationflags=subprocess.CREATE_NO_WINDOW)
  def stop_child():
   if process.poll() is None:
    process.terminate()
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:process.kill();process.wait()
  atexit.register(stop_child)
  tracked=psutil.Process(process.pid)
  tracked.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
  tracked.cpu_percent(None)
  psutil.cpu_percent(None)
  while process.poll() is None:
   time.sleep(2)
   elapsed=time.perf_counter()-began
   try:
    sample={'seconds':elapsed,'system_cpu_percent':psutil.cpu_percent(None),
     'blender_cpu_percent_of_system':tracked.cpu_percent(None)/psutil.cpu_count(),
     'blender_rss_mib':tracked.memory_info().rss/2**20,
     'system_ram_available_gib':psutil.virtual_memory().available/2**30,'gpu':gpu_sample()}
   except psutil.NoSuchProcess:break
   samples.append(sample)
   with (run_dir/'telemetry.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(sample)+'\n')
   if elapsed-last_print>=20:
    last_print=elapsed
    try:progress=json.loads((run_dir/'progress.json').read_text(encoding='utf-8'))
    except (FileNotFoundError,json.JSONDecodeError):progress={'frame':0}
    print(f"PROGRESS {progress['frame']}/192 elapsed={elapsed:.1f}s CPU(Blender)={sample['blender_cpu_percent_of_system']:.1f}% GPU(system)={sample['gpu'].get('utilization.gpu')}%",flush=True)
  code=process.wait()
 render_wall=time.perf_counter()-began
 if code:raise RuntimeError(f'Blender exited {code}; see {run_dir / "blender.log"}')
 render=json.loads((run_dir/'render_result.json').read_text(encoding='utf-8'))
 assert render['completed_frames']==192
 encoding=encode_sequence(frames,run_dir/'sugarfall.mp4',run_dir/'video_validation.json')
 total=time.perf_counter()-began
 assert hashlib.sha256(scene.read_bytes()).hexdigest()==source_hash,'Source .blend changed during run'
 def metrics(values):
  values=[v for v in values if v is not None]
  return {'mean':statistics.mean(values),'max':max(values)} if values else None
 report={'run_id':run_id,'source_sha256':source_hash,'render_wall_seconds':render_wall,
  'render_loop_seconds':render['render_loop_seconds'],'encode_seconds':encoding['encode_seconds'],
  'total_seconds_including_validation':total,'original_render_reference_seconds':746,
  'reference_note':'Original log ~12m26s; this is a historical comparison, not a controlled simultaneous A/B benchmark.',
  'render_time_reduction_percent':100*(1-render_wall/746),'speedup_vs_original':746/render_wall,
  'telemetry_samples':len(samples),'blender_cpu_percent_of_system':metrics([s['blender_cpu_percent_of_system'] for s in samples]),
  'system_cpu_percent':metrics([s['system_cpu_percent'] for s in samples]),
  'gpu_system_utilization_percent':metrics([s['gpu'].get('utilization.gpu') for s in samples]),
  'gpu_system_memory_mib':metrics([s['gpu'].get('memory.used') for s in samples]),
  'gpu_temperature_c':metrics([s['gpu'].get('temperature.gpu') for s in samples]),
  'blender_rss_mib':metrics([s['blender_rss_mib'] for s in samples]),
  'minimum_system_ram_available_gib':min(s['system_ram_available_gib'] for s in samples) if samples else None,
  'telemetry_note':'CPU normalized to 16 logical cores. GPU statistics include other applications. Sampling may miss short peaks.',
  'render_settings':render,'video':encoding,'passed':True}
 (run_dir/'benchmark.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print('COMPLETE '+json.dumps({'report':str(run_dir/'benchmark.json'),'render_seconds':render_wall,'total_seconds':total,'video':str(run_dir/'sugarfall.mp4')}),flush=True)
 from finalize_delivery import finalize
 finalize(run_dir)

if __name__=='__main__':main()
