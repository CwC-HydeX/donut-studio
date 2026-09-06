import bpy
import json
from pathlib import Path

ROOT=Path('E:/codex/新奇想法/donut-studio')
scene=bpy.context.scene
sprinkles=[o for o in scene.objects if o.name.startswith('Sugarfall /')]
samples=[]
for frame in [1,65,110,170,192]:
    scene.frame_set(frame)
    samples.append({'frame':frame,'full_size_sprinkles':sum(o.scale.x>.5 for o in sprinkles),
                    'airborne':sum(o.scale.x>.5 and o.location.z>1.7 for o in sprinkles),
                    'camera':[round(c,3) for c in scene.camera.location]})
assert len(sprinkles)==310
assert samples[0]['full_size_sprinkles']==0
assert samples[-1]['full_size_sprinkles']==310
assert samples[-1]['airborne']==0
assert samples[0]['camera']!=samples[-1]['camera']
scene.frame_set(170)
result={'passed':True,'sprinkles':len(sprinkles),'objects':len(scene.objects),'duration_seconds':8,
        'samples':samples,'animation':'keyframed ballistic fall and bounce',
        'external_images':[i.filepath for i in bpy.data.images if i.source=='FILE' and i.filepath]}
(ROOT/'reports'/'scene_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
