# Full render, timing and CPU/GPU sampling. Results go to reports/<run-id>.
$ErrorActionPreference='Stop'
$env:PYTHONDONTWRITEBYTECODE='1'
& 'E:/anaconda3/envs/llm/python.exe' -B (Join-Path $PSScriptRoot 'scripts/benchmark_render.py')
if($LASTEXITCODE -ne 0){throw 'Render failed. See reports/<run-id>/blender.log.'}
