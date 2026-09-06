from pathlib import Path
import json
import zipfile

ROOT=Path(__file__).resolve().parents[1]
files=['README.md','render.ps1','donut_studio.blend','output/hero.png','output/sugarfall.mp4',
       'docs/MCP调查与使用说明.md','docs/render-benchmark.md','docs/mcp_tools.json','docs/requirements.lock.txt',
       'scripts/build_donut.py','scripts/render_frames.py','scripts/encode_video.py','scripts/benchmark_render.py',
       'scripts/finalize_delivery.py','scripts/package_delivery.py','scripts/verify_scene.py','scripts/mcp_client.py',
       'reports/benchmark.json','reports/video_validation.json','reports/setup/scene_validation.json']
assert all((ROOT/name).exists() for name in files)
with zipfile.ZipFile(ROOT/'output'/'Sugarfall_Donut_Package.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in files:z.write(ROOT/name,name)
print(json.dumps({'package':str(ROOT/'output'/'Sugarfall_Donut_Package.zip'),'files':len(files),
                  'bytes':(ROOT/'output'/'Sugarfall_Donut_Package.zip').stat().st_size},ensure_ascii=False))
