"""Procedural strawberry donut, capsule sprinkles and an eight-second studio shot.

Executed through Blender Lab's execute_blender_code MCP tool. No external assets.
"""
import bpy
import math
import random
from pathlib import Path
from mathutils import Vector

ROOT=Path('E:/codex/新奇想法/donut-studio')
random.seed(219)
scene=bpy.context.scene
assert Path(bpy.data.filepath).resolve()==(ROOT/'donut_studio.blend').resolve(), 'Wrong target scene'
# Only this task's newly created startup scene is cleared.
for obj in list(scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
scene.name='STRAWBERRY / Sugarfall'
for name in ['01 Pastry','02 Falling sprinkles','03 Table styling','04 Studio']:
    col=bpy.data.collections.new(name)
    scene.collection.children.link(col)
pastry=bpy.data.collections['01 Pastry']
sugars=bpy.data.collections['02 Falling sprinkles']
styling=bpy.data.collections['03 Table styling']
studio=bpy.data.collections['04 Studio']

def move_to(obj,col):
    for old in list(obj.users_collection): old.objects.unlink(obj)
    col.objects.link(obj)
    return obj

def mat(name,color,roughness=.4,metallic=0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=roughness
    p.inputs['Metallic'].default_value=metallic
    return m,p

def mesh_obj(name,verts,faces,col,material):
    mesh=bpy.data.meshes.new(name+' / mesh')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    col.objects.link(obj)
    if material: mesh.materials.append(material)
    for poly in mesh.polygons: poly.use_smooth=True
    return obj

dough,p=mat('Brioche / baked crust',(0.62,.25,.07),.48)
p.inputs['Subsurface Weight'].default_value=.065
p.inputs['Subsurface Radius'].default_value=(1,.45,.2)
n=dough.node_tree.nodes; l=dough.node_tree.links
tex=n.new('ShaderNodeTexCoord'); tex.location=(-900,0)
noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=5; noise.inputs['Detail'].default_value=4; noise.location=(-700,150)
l.new(tex.outputs['Generated'],noise.inputs['Vector'])
ramp=n.new('ShaderNodeValToRGB'); ramp.location=(-480,180)
ramp.color_ramp.elements[0].position=.2; ramp.color_ramp.elements[0].color=(.19,.043,.009,1)
ramp.color_ramp.elements[1].position=.8; ramp.color_ramp.elements[1].color=(.8,.39,.105,1)
l.new(noise.outputs['Fac'],ramp.inputs[0])
sep=n.new('ShaderNodeSeparateXYZ'); sep.location=(-690,-100); l.new(tex.outputs['Generated'],sep.inputs[0])
belt=n.new('ShaderNodeValToRGB'); belt.location=(-480,-100)
cr=belt.color_ramp
cr.elements.remove(cr.elements[1])
cr.elements[0].position=0; cr.elements[0].color=(0,0,0,1)
for pos,value in [(.29,0),(.42,.75),(.5,1),(.59,.7),(.7,0),(1,0)]:
    e=cr.elements.new(pos); e.color=(value,value,value,1)
l.new(sep.outputs['Z'],belt.inputs[0])
mix=n.new('ShaderNodeMixRGB'); mix.blend_type='MIX'; mix.location=(-180,160)
l.new(belt.outputs['Color'],mix.inputs[0]); l.new(ramp.outputs[0],mix.inputs[1]); mix.inputs[2].default_value=(.86,.49,.19,1)
l.new(mix.outputs[0],p.inputs['Base Color'])
pores=n.new('ShaderNodeTexNoise'); pores.location=(-490,-380); pores.inputs['Scale'].default_value=155; pores.inputs['Detail'].default_value=3; pores.inputs['Roughness'].default_value=.7
l.new(tex.outputs['Generated'],pores.inputs['Vector'])
bump=n.new('ShaderNodeBump'); bump.location=(-170,-130); bump.inputs['Strength'].default_value=.32; bump.inputs['Distance'].default_value=.026
l.new(pores.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs[0],p.inputs['Normal'])

icing,p=mat('Strawberry / glossy fondant',(.78,.16,.29),.265)
p.inputs['Subsurface Weight'].default_value=.08
p.inputs['Subsurface Radius'].default_value=(.8,.3,.22)
p.inputs['Coat Weight'].default_value=.22
p.inputs['Coat Roughness'].default_value=.22
n=icing.node_tree.nodes; l=icing.node_tree.links
noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=7; noise.inputs['Detail'].default_value=2
ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color=(.55,.065,.15,1); ramp.color_ramp.elements[1].color=(.95,.33,.43,1)
l.new(noise.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs[0],p.inputs['Base Color'])
micro=n.new('ShaderNodeTexNoise'); micro.inputs['Scale'].default_value=190
bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.12; bump.inputs['Distance'].default_value=.009
l.new(micro.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs[0],p.inputs['Normal'])

R=1.43; r=.65; z0=.94
def surface(u,v,offset=0):
    major=R+.027*math.sin(3*u+.7)+.018*math.sin(7*u)
    tube=r*(1+.035*math.sin(5*u)+.018*math.cos(9*u+2*v))
    detail=.006*math.sin(21*u+5*v)*math.sin(13*v+3*u)
    radial=major+(tube+offset+detail)*math.cos(v)
    z=z0+(.58+offset+detail)*math.sin(v)+.018*math.sin(4*u)+.008*math.sin(11*u+3*v)
    return Vector((radial*math.cos(u),radial*math.sin(u),z))

NU=192; NV=72
verts=[surface(i*math.tau/NU,j*math.tau/NV) for i in range(NU) for j in range(NV)]
faces=[(i*NV+j,((i+1)%NU)*NV+j,((i+1)%NU)*NV+(j+1)%NV,i*NV+(j+1)%NV) for i in range(NU) for j in range(NV)]
body=mesh_obj('Donut / hand-shaped brioche',verts,faces,pastry,dough)
sub=body.modifiers.new('Soft baked silhouette','SUBSURF'); sub.levels=1; sub.render_levels=1

drips=[(.12,.9,.10),(.75,.65,.12),(1.30,1.05,.11),(1.96,.63,.16),(2.55,.9,.1),(3.12,.6,.15),(3.75,1.0,.11),(4.26,.65,.11),(4.89,.96,.105),(5.47,.7,.14),(5.92,.5,.09)]
def wrap(a): return (a+math.pi)%math.tau-math.pi
def outer_edge(u):
    return .24+.065*math.sin(8*u)-sum(depth*math.exp(-.5*(wrap(u-pos)/width)**2) for pos,depth,width in drips)
NV=46
verts=[]
for i in range(NU):
    u=i*math.tau/NU
    low=outer_edge(u); high=math.pi-.18+.2*math.sin(5*u+.4)+.10*math.sin(9*u)
    for j in range(NV):
        v=low+(high-low)*j/(NV-1)
        verts.append(surface(u,v,.035))
faces=[(i*NV+j,((i+1)%NU)*NV+j,((i+1)%NU)*NV+j+1,i*NV+j+1) for i in range(NU) for j in range(NV-1)]
glaze=mesh_obj('Icing / strawberry drips',verts,faces,pastry,icing)
solid=glaze.modifiers.new('Fondant thickness','SOLIDIFY'); solid.thickness=.035; solid.offset=0
sub=glaze.modifiers.new('Rounded sugar edges','SUBSURF'); sub.levels=1; sub.render_levels=2

ceramic,p=mat('Porcelain / warm celadon',(.66,.81,.74),.22)
p.inputs['Coat Weight'].default_value=.3
gold,_=mat('Plate / brushed champagne rim',(.65,.41,.15),.24,.82)
profile=[(0,.12),(.8,.12),(1.8,.12),(2.3,.16),(2.65,.24),(2.77,.30),(2.8,.345),(2.78,.38),(2.72,.385),(2.6,.345),(2.4,.28),(2.18,.24),(1.6,.24),(.7,.24),(0,.24)]
verts=[(rad*math.cos(i*math.tau/192),rad*math.sin(i*math.tau/192),h) for i in range(192) for rad,h in profile]
np=len(profile)
faces=[(i*np+j,((i+1)%192)*np+j,((i+1)%192)*np+j+1,i*np+j+1) for i in range(192) for j in range(np-1)]
plate=mesh_obj('Plate / turned porcelain',verts,faces,styling,ceramic)
sub=plate.modifiers.new('Glazed ceramic curves','SUBSURF'); sub.levels=2
for radius,height in [(2.75,.383),(2.43,.288)]:
    bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=.009,major_segments=192,minor_segments=10,location=(0,0,height))
    o=move_to(bpy.context.object,styling); o.name='Plate / gold inlay'; o.data.materials.append(gold)
    for p in o.data.polygons:p.use_smooth=True

colors=[('Vanilla',(.96,.82,.5)),('Raspberry',(.63,.025,.11)),('Mint',(.13,.67,.51)),('Lavender',(.43,.19,.75)),('Cream',(1,.93,.78)),('Cocoa',(.095,.029,.016)),('Coral',(.98,.22,.12))]
sugar_mats=[]
for name,color in colors:
    m,p=mat('Sprinkle / '+name,color,.3)
    p.inputs['Subsurface Weight'].default_value=.035
    sugar_mats.append(m)
# A capsule with a genuinely cylindrical body and rounded ends, linked mesh per color.
def capsule_mesh(material):
    verts=[]; faces=[]
    rings=[]; radius=.024; half=.062
    for k in range(7):
        a=-math.pi/2+k*math.pi/12
        rings.append((radius*math.cos(a),-half+radius*math.sin(a)))
    for k in range(7):
        a=k*math.pi/12
        rings.append((radius*math.cos(a),half+radius*math.sin(a)))
    for rad,z in rings:
        for j in range(10):
            a=j*math.tau/10; verts.append((rad*math.cos(a),rad*math.sin(a),z))
    for k in range(len(rings)-1):
        for j in range(10): faces.append((k*10+j,k*10+(j+1)%10,(k+1)*10+(j+1)%10,(k+1)*10+j))
    mesh=bpy.data.meshes.new('Capsule / '+material.name); mesh.from_pydata(verts,[],faces); mesh.materials.append(material)
    for p in mesh.polygons:p.use_smooth=True
    return mesh
capsules=[capsule_mesh(m) for m in sugar_mats]

def key(obj,frame,pos,rot,scale):
    obj.location=pos; obj.rotation_euler=rot; obj.scale=scale
    for path in ('location','rotation_euler','scale'): obj.keyframe_insert(data_path=path,frame=frame)

final_points=[]
for i in range(310):
    for _ in range(60):
        u=random.uniform(0,math.tau); v=random.uniform(.39,2.70)
        pt=surface(u,v,.071)
        if all((pt-old).length>.08 for old in final_points): break
    final_points.append(pt)
    normal=Vector((math.cos(u)*math.cos(v),math.sin(u)*math.cos(v),math.sin(v))).normalized()
    tangent_u=Vector((-math.sin(u),math.cos(u),0))
    tangent_v=normal.cross(tangent_u)
    a=random.uniform(0,math.tau)
    tangent=(math.cos(a)*tangent_u+math.sin(a)*tangent_v).normalized()
    rot=tangent.to_track_quat('Z','Y').to_euler()
    o=bpy.data.objects.new('Sugarfall / %03d'%(i+1),capsules[i%len(capsules)]); sugars.objects.link(o)
    size=random.uniform(.78,1.18); scl=Vector((size,size,size*random.uniform(.8,1.3)))
    landing=random.randint(34,139)
    travel=random.randint(20,29)
    start=landing-travel
    drift=Vector((random.uniform(-.25,.25),random.uniform(-.25,.25),0))
    fallheight=random.uniform(2.7,4.2)
    spin=Vector((random.uniform(-2.5,2.5),random.uniform(-2,2),random.uniform(-3,3)))
    key(o,1,pt+Vector((0,0,fallheight)),Vector(rot)+spin,(.001,.001,.001))
    key(o,start-1,pt+drift+Vector((0,0,fallheight)),Vector(rot)+spin,(.001,.001,.001))
    for k in range(9):
        t=k/8
        pos=pt+drift*(1-t)+Vector((0,0,fallheight*(1-t*t)))
        key(o,start+travel*t,pos,Vector(rot)+spin*(1-t),scl)
    key(o,landing+3,pt+normal*random.uniform(.05,.14),Vector(rot)+spin*.08,scl)
    key(o,landing+8,pt,rot,scl)
    key(o,192,pt,rot,scl)
    o['landing_frame']=landing

# Finished grains and crumbs on the plate reinforce scale.
for i in range(30):
    a=random.uniform(0,math.tau); rr=random.uniform(2.16,2.52)
    o=bpy.data.objects.new('Plate / loose sprinkle %02d'%i,capsules[i%len(capsules)]); styling.objects.link(o)
    o.location=(rr*math.cos(a),rr*math.sin(a),.285+(rr-2.2)*.17)
    o.rotation_euler=(math.pi/2,0,random.uniform(0,math.tau)); o.scale=(.8,.8,.85)
for i in range(38):
    a=random.uniform(0,math.tau); rr=random.uniform(1.9,2.59)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=random.uniform(.008,.025),location=(rr*math.cos(a),rr*math.sin(a),.27+(max(rr,2.2)-2.2)*.2))
    o=move_to(bpy.context.object,styling); o.name='Crumb / brioche'; o.scale=(1,.7,.55);o.data.materials.append(dough)

table,p=mat('Backdrop / pistachio paper',(.095,.22,.18),.69)
bpy.ops.mesh.primitive_plane_add(size=200)
o=move_to(bpy.context.object,studio);o.name='Backdrop / seamless';o.data.materials.append(table)

def light(name,pos,power,color,size,target=(0,0,.7),shape='DISK',size_y=None):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape=shape;data.size=size
    if size_y is not None:data.size_y=size_y
    o=bpy.data.objects.new(name,data);studio.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
light('KEY / silk softbox',(-3.5,-4.5,7),850,(1,.84,.69),5)
light('RIM / strawberry sheen',(3,2.5,6),1050,(1,.73,.58),3)
light('FILL / cool bounce',(1,-1,5.5),240,(.7,.85,1),4)
light('STRIP / long glaze highlight',(-4,1,3.5),320,(1,.94,.84),3,shape='RECTANGLE',size_y=1)
world=bpy.data.worlds.new('World / soft studio');scene.world=world;world.use_nodes=True
background=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
background.inputs[0].default_value=(.35,.45,.42,1)
background.inputs[1].default_value=.3

camdata=bpy.data.cameras.new('Camera / confectionery portrait');cam=bpy.data.objects.new('Camera / slow orbit',camdata);studio.objects.link(cam);scene.camera=cam
camdata.lens=54
focus=bpy.data.objects.new('Focus / strawberry crown',None);studio.objects.link(focus);focus.location=(0,0,1.05)
camdata.dof.use_dof=True;camdata.dof.focus_object=focus;camdata.dof.aperture_fstop=6.3
for frame,angle,radius,height in [(1,-64,10.8,7.3),(96,-56,10.4,7.0),(192,-46,10.0,6.65)]:
    a=math.radians(angle);cam.location=(radius*math.cos(a),radius*math.sin(a),height)
    cam.rotation_euler=(Vector((0,0,.9))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.keyframe_insert(data_path='location',frame=frame);cam.keyframe_insert(data_path='rotation_euler',frame=frame)

scene.render.engine='CYCLES'
scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3
try:
    cp=bpy.context.preferences.addons['cycles'].preferences
    cp.compute_device_type='OPTIX';cp.get_devices()
    for device in cp.devices: device.use=device.type!='CPU'
    scene.cycles.device='GPU'
except Exception: pass
scene.render.resolution_x=1200;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.fps=24;scene.frame_start=1;scene.frame_end=192
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.render.film_transparent=False
scene.render.filepath=str(ROOT/'output'/'hero.png')
scene.frame_set(170)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.color_type='MATERIAL'
            area.spaces.active.overlay.show_overlays=False

note=bpy.data.texts.new('READ ME / Sugarfall')
note.write('STRAWBERRY / SUGARFALL\nProcedural model created through Blender Lab official MCP.\n8 seconds, 24 fps, frames 1-192.\n310 individually animated capsule sprinkles.\nArt-directed fall, spin and bounce keyframes; no rigid-body simulation.\nScrub frames 1, 65, 110 and 170.\nAll geometry and materials are editable; no external textures.\n')
scene['animation_method']='Art-directed ballistic fall and bounce keyframes (not rigid-body simulation)'
scene['mcp_source']='https://projects.blender.org/lab/blender_mcp @ v1.0.0'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'donut_studio.blend'))
result={'file':bpy.data.filepath,'objects':len(scene.objects),'animated_sprinkles':len(sugars.objects),'frames':192,'fps':24,'status':'built'}
