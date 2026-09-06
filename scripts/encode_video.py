"""Encode PNG frames and decode the entire MP4 to validate delivery."""
import argparse
import json
import subprocess
import time
from pathlib import Path
import imageio_ffmpeg

def encode_sequence(frames_dir,output,report_path):
 missing=[i for i in range(1,193) if not (frames_dir/f'sugarfall_{i:04d}.png').exists()]
 if missing:raise RuntimeError(f'Missing {len(missing)} frames')
 output.parent.mkdir(parents=True,exist_ok=True)
 ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
 started=time.perf_counter()
 subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y','-framerate','24',
  '-i',str(frames_dir/'sugarfall_%04d.png'),'-c:v','libx264','-threads','4',
  '-preset','slow','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
 encode_seconds=time.perf_counter()-started
 reader=imageio_ffmpeg.read_frames(str(output),pix_fmt='rgb24',input_params=['-threads','2'])
 metadata=next(reader)
 count=sum(1 for _ in reader)
 assert count==192,count
 assert metadata['size']==(960,800),metadata
 assert abs(metadata['fps']-24)<.01,metadata
 assert abs(metadata['duration']-8)<.1,metadata
 report={'path':str(output),'frames':count,'fps':metadata['fps'],'duration':metadata['duration'],
  'size':metadata['size'],'bytes':output.stat().st_size,'codec':'H.264','encode_seconds':encode_seconds,
  'encode_and_validation_seconds':time.perf_counter()-started,'passed':True}
 report_path.parent.mkdir(parents=True,exist_ok=True)
 report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
 return report

if __name__=='__main__':
 parser=argparse.ArgumentParser()
 parser.add_argument('--frames-dir',type=Path,required=True)
 parser.add_argument('--output',type=Path,required=True)
 parser.add_argument('--report',type=Path,required=True)
 args=parser.parse_args()
 print(json.dumps(encode_sequence(args.frames_dir,args.output,args.report),indent=2))
