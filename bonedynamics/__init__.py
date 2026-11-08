bl_info = \
    {
        "name" : "BoneDynamics Pro",
        "author" : "Morelewd",
        "version" : (1, 6, 0),
        "blender" : (2, 91, 0),
        "location" : "UI > BoneDynamics Pro",
        "description" :
            "Apply physics to bones",
        "warning" : "", 
        "wiki_url" : "",
        "tracker_url" : "",
        "category" : "Animation",
    }


import bpy
from bpy.props import PointerProperty
import mathutils
from mathutils import Matrix
from math import pi
import math
import bmesh
import threading
from bl_operators.presets import AddPresetBase
from bpy.types import Panel, Menu
import shutil
import os
from os.path import basename, splitext




def debounce(wait_time):
    def decorator(function):
        def debounced(arg, arg2 , arg3):
            def call_function():
                debounced._timer = None
                return function(arg, arg2, arg3)

            if debounced._timer is not None:
                debounced._timer.cancel()

            debounced._timer = threading.Timer(wait_time, call_function)
            debounced._timer.start()

        debounced._timer = None
        return debounced

    return decorator



def findCollection(context):
        if not any(collection.name == "BoneDynamics" for collection in bpy.data.collections):
            my_coll = bpy.data.collections.new("BoneDynamics")
            bpy.context.scene.collection.children.link(my_coll)
            
def set_collection(collection_name):
    if collection_name in bpy.context.view_layer.layer_collection.children:
        root=bpy.context.view_layer.layer_collection.children[collection_name]
    else:
        coll=bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(coll)
        root=bpy.context.view_layer.layer_collection.children[coll.name]

    bpy.context.view_layer.active_layer_collection=root
    return(root)

def findroot(self , context):
    
    if len(context.selected_pose_bones) == 1:
        return context.active_pose_bone.parent       
    for num , ob in enumerate(context.selected_pose_bones):
        if ob.parent in context.selected_pose_bones:
            continue
        else:
            if ob.parent:
                return ob.parent
            else:
                if len(context.selected_pose_bones) == 2 and ob.parent != context.active_pose_bone:
                    return context.active_pose_bone
                return ob

def main(self , context):
    blist = []
    previouslayers = []
    active = context.object.data.bones.active
    arma = context.active_object


#    if len(bpy.context.selected_pose_bones) == 1 and context.active_pose_bone.parent == None and context.scene.dynamicParent == False :
#        self.report({'ERROR'}, 'you selected a bone that has no parent , please select another bone with a parent ')
#        return None
    if len(bpy.context.selected_pose_bones) > 0:
        for num , ob in enumerate(context.selected_pose_bones):
                  if  len(bpy.context.selected_pose_bones) > 0:

                    obj = ob.id_data
                    armature = ob.id_data.name
                    item = [ob.name,num,ob.tail,ob.length, ob.head]
                    T =  Matrix.Translation(ob.tail - ob.head)
                    thead= Matrix.Translation(1.0 * (ob.tail - ob.head))
                    ttail=  Matrix.Translation(0 * (ob.tail - ob.head))
                    mathead = obj.matrix_world @ (thead @ ob.matrix)
                    mattail = obj.matrix_world @ (ttail @ ob.matrix)                    
                    matrix_final = obj.matrix_world @ (T @ ob.matrix)

#                    if ob.parent:
#                        previouslayers = checkParentVisibility(self,context, ob , ob.parent)
#                    else:
#                        if context.scene.dynamicParent == False:
#                            continue;
                    if not context.scene.chainMode and ob.displace:
                      ob.displaceOrg = ob.bone.use_connect
                      print('armature library', ob.id_data.override_library)
                    if not ob.id_data.override_library: 
                      toggleConnect(self , context, ob , False)
                    if context.scene.dynamicParent:
                        print('start with dynamic parent' , context.active_pose_bone)
                        item = [ob.name,num,ob.tail,ob.length,ob.head, matrix_final , context.active_pose_bone, armature, mathead , mattail, ob]
                    else:
                        item = [ob.name,num,ob.tail,ob.length,ob.head, matrix_final , ob.parent, armature, mathead , mattail, ob]

                    if context.scene.dynamicParent and ob == context.active_pose_bone:
                        continue
                    else:
                        blist.append(item)                

        if context.scene.chainMode:
            makeChainphysics(self ,context , previouslayers)                
        else:
            makePhysics(self ,context , blist , previouslayers)
    else:
        self.report({'ERROR'}, 'Selection is empty, please select at least two bones.')


def toggleConnect(self , context, ob , cond):
    if context.scene.chainMode:
        return False;g
    arma = ob.id_data
    bpy.ops.object.mode_set(mode='EDIT')
    if ob.displace:
        arma.data.edit_bones[ob.name].use_connect = False
    if cond == True and ob.displace == ob.displaceOrg:
        arma.data.edit_bones[ob.name].use_connect = ob.displaceOrg
    bpy.ops.object.mode_set(mode='POSE')

def setDefault(self, context):
    bones = context.selected_pose_bones
    for bone in bones:
        if context.scene.chainMode:
            bone.boneMass = 0.5
            bone.boneFriction = 5
            bone.boneStiffness = 0.5
            bone.boneDamping = 5
            bone.boneBend = 10  
            bone.boneSpeed = 1  
            bone.boneStrength = 0.5
            bone.boneElasticity = 0.03
        else:
            bone.boneMass = 0.3
            bone.boneFriction = 12 
            bone.boneStrength = 0.7              
            bone.boneStiffness = 0.9
            bone.boneDamping = 10
            bone.boneBend = 10
            bone.boneElasticity = 0.03



def updateCloth (self, context):
    if self.clothMode:
        self.chainMode = True
  
        

def updateDisplace (self, context):
    bones =  context.selected_pose_bones
    print('displace is ',self.displace)
    updateRestBones(self,bones , 'displace')
        
        
     
def updateToggle(self,context):
    for bne in context.selected_pose_bones:
        nme = 'BoneDynamics-damped-' + bne.name
        cr = bne.constraints.get(nme)
        nme2 = 'BoneDynamics-displace-' +  bne.name
        cr2 = bne.constraints.get(nme2)
        if cr:
            if self.toggleDynamics:
                cr.influence = self.toggleDynamics
        if cr2:
            if self.toggleDynamics:
                cr2.influence = self.toggleDynamics
         
def updateChain (self, context):

   setDefault(self , context)
    

def checkParentVisibility(self , context , bone, parent ):
    obplayer = parent.bone.layers
    lastlayers = []

    for num , lay in enumerate(obplayer):
        lastlayers.append(bpy.context.object.data.layers[num])
        if lay == True:
            bpy.context.object.data.layers[num] = True
    return lastlayers

@debounce(0.1)
def updateRestBones(self ,bones , prop):
    for bone in bones:
        bone[prop] = self[prop]


def checkPresets():
    addon_path = os.path.join(bpy.utils.script_path_user(), 'addons', 'bonedynamics' , 'presets' ) 
    my_presets = os.path.join(bpy.utils.script_path_user(), 'presets', 'bonedynamics') 

    if not os.path.isdir(my_presets): 
        os.makedirs(my_presets) 
        files = os.listdir(addon_path) 
        # Copy them 
        [os.rename(os.path.join(addon_path,  f), os.path.join(my_presets, f)) for f in files]
   
def updateMass(self , context):
    bones = context.selected_pose_bones
    for num , ob in enumerate(bones):
            obj = ob.get('bbdObject')
            if obj:
                for modifier in obj.modifiers:
                  if modifier.type == "SOFT_BODY":
                    mod = modifier.settings
                    mod.mass= self.boneMass  
                  if modifier.type == "CLOTH":
                    mod = modifier.settings
                    mod.mass= self.boneMass                
    updateRestBones(self,bones , 'boneMass')

def updateFriction(self , context):
    bones = context.selected_pose_bones
    for num , ob in enumerate(bones):
            obj = ob.get('bbdObject')
            if obj:
                for modifier in obj.modifiers:
                  if modifier.type == "SOFT_BODY":
                    mod = modifier.settings
                    mod.friction = self.boneFriction
    updateRestBones(self,bones , 'boneFriction')

def updateSpeed(self , context):
    bones = context.selected_pose_bones
    for num , ob in enumerate(bones):
            obj = ob.get('bbdObject')
            if obj:
                for modifier in obj.modifiers:
                  if modifier.type == "SOFT_BODY":
                    mod = modifier.settings
                    mod.speed = self.boneSpeed
    updateRestBones(self,bones , 'boneSpeed')



def updateGravity(self , context):
    bones = context.selected_pose_bones
    for num , ob in enumerate(bones):
            obj = ob.get('bbdObject')
            if obj:
                for modifier in obj.modifiers:
                  if modifier.type == "SOFT_BODY":
                    mod = modifier.settings
                    mod.effector_weights.gravity = self.boneGravity
    updateRestBones(self,bones , 'boneGravity')


def updateStiffness(self , context):  
    bones = context.selected_pose_bones
    
    for num , ob in enumerate(bones):
            obj = ob.get('bbdObject')
            if obj:
                for modifier in obj.modifiers:
                  if modifier.type == "SOFT_BODY":
                    mod = modifier.settings
                    mod.goal_spring = self.boneStiffness
                  if modifier.type == "CLOTH":
                    mod = modifier.settings
                    mod.tension_stiffness= self.boneMass * 100
    updateRestBones(self,bones , 'boneStiffness')
    


def updateElasticity(self , context):
    bones = context.selected_pose_bones    
    for num , ob in enumerate(bones):
            obj = ob.get('bbdObject')
            if obj:
                for modifier in obj.modifiers:
                  if modifier.type == "SOFT_BODY":
                    mod = modifier.settings
                    mod.push = 1.0 - self.boneElasticity
                    mod.pull = 1.0 - self.boneElasticity
    updateRestBones(self,bones , 'boneElasticity') 

def updateDamping(self , context):
    bones = context.selected_pose_bones    
    for num , ob in enumerate(bones):
            obj = ob.get('bbdObject')
            if obj:
                for modifier in obj.modifiers:
                  if modifier.type == "SOFT_BODY":
                    mod = modifier.settings
                    mod.goal_friction = self.boneDamping
    updateRestBones(self,bones , 'boneDamping') 


def updateStrength(self , context):
    bones = context.selected_pose_bones 
    for num , ob in enumerate(bones):
        for obj in bpy.context.scene.objects:
            obj = ob.get('bbdObject')
            if obj:
                for modifier in obj.modifiers:
                  if modifier.type == "SOFT_BODY":
                    mod = modifier.settings
                    mod.goal_min = self.boneStrength
    updateRestBones(self,bones , 'boneStrength')
    
    
def updateBend(self , context):
    bones = context.selected_pose_bones 
    for num , ob in enumerate(bones):
        for obj in bpy.context.scene.objects:
            obj = ob.get('bbdObject')
            if obj:
                for modifier in obj.modifiers:
                  if modifier.type == "SOFT_BODY":
                    mod = modifier.settings
                    mod.bend = self.boneBend
    updateRestBones(self,bones , 'boneBend')



    
def makePhysics(self , context , blist  , previouslayers):
    arma = context.active_object
    parent = findroot(self , context)
    origin = bpy.context.scene.cursor.location.copy()

        
    bpy.ops.object.mode_set(mode='OBJECT')
    
    for obj in blist:         
        loc= obj[5]
        obname = obj[0 ] + '|' + obj[7]
        pBone = obj[10]
        exist = context.scene.objects.get(obname)
        if exist:
         bpy.context.layer_collection.children['BoneDynamics'].exclude = False  
         continue 

        root = set_collection('BoneDynamics')
        mesh = bpy.data.meshes.new("mesh")  # add a new mesh
        boneobj = bpy.data.objects.new(obname, mesh)  # add a new object using the mesh
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.collections['BoneDynamics'].objects.link(boneobj)
        bpy.context.view_layer.objects.active = boneobj
        boneobj.select_set(True)  # select object
#        verts = (obj[8].to_translation(), obj[9].to_translation())
        start = mathutils.Vector()
        pbl = pBone.length/ abs(pBone.scale.x)
        print('pBone scale' , pBone.length , pBone.scale.x)
            
        end = mathutils.Vector((0,0,pbl))
        verts =(start, end)
        edges = ([0,1] ,[1,0])
        mesh.from_pydata(verts , edges , [])
#        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        me = boneobj.data        
 #        bpy.context.scene.cursor.location = me.vertices[1].co
#        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
#        bpy.context.scene.cursor.location = origin    
        pingroup = boneobj.vertex_groups.new(name = "Pin")
        fallgroup = boneobj.vertex_groups.new(name = "Fall")
        if pBone.displace:
            displacegroup = boneobj.vertex_groups.new(name = "Displace")
            boneobj.vertex_groups[displacegroup.index].add([0], 0.5, 'REPLACE')
            boneobj.vertex_groups[displacegroup.index].add([1], 0.5, 'REPLACE')
            
        boneobj.vertex_groups[pingroup.index].add([0], 1.0, 'REPLACE')
        boneobj.vertex_groups[fallgroup.index].add([1], 1.0, 'REPLACE')
        pBone['dynamics'] = True
        pBone.bbdObject = boneobj
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.ed.undo_push()
        obj2 = context.active_object
        mw = arma.convert_space(pose_bone=pBone, matrix=pBone.matrix, from_space="POSE" , to_space="WORLD")
        mat_rot_mx = Matrix.Rotation(math.radians(-90.0), 4, 'X')
        obj2.matrix_world = mw @ mat_rot_mx

#        rotation = mw.to_quaternion()
#        obj2.rotation_mode = 'QUATERNION'
#        obj2.rotation_quaternion = rotation 
        obj2['dynamics'] = True
        obj2['arma'] = arma.id_data
        obj2['bone'] = pBone.name
        modi = obj2.modifiers.new(name = pBone.name + '-soft' , type='SOFT_BODY')
        mod = modi.settings       
        modi.point_cache.frame_start = context.scene.frame_start 
        modi.point_cache.frame_end = context.scene.frame_end  
        mod .vertex_group_goal = "Pin"
        if pBone.displace:
            mod.vertex_group_goal = "Displace"
        mod.use_edges = True
#        mod.use_stiff_quads = True
#        mod.use_self_collision = True
        mod.choke = 0
        mod.fuzzy = 0
        mod.step_min = 40
        mod.pull =  1.0 - pBone.boneElasticity
        mod.push =  1.0 - pBone.boneElasticity
        mod.bend = 10 
        mod.damping = 10
        mod.spring_length = 100
        mod.goal_default = 1  
        mod.use_face_collision = False
        mod.use_edge_collision = True
        ## settings ##
        mod.friction = pBone.boneFriction

        mod.mass= pBone.boneMass 
        mod.goal_spring  = pBone.boneStiffness
        mod.goal_friction = pBone.boneDamping
        mod.goal_min = pBone.boneStrength
        mod.speed = pBone.boneSpeed
        
        obj2.hide_render = True

    
        bpy.ops.ed.undo_push()
        obj2.select_set(True)
        arma.select_set(True) 
        bpy.context.view_layer.objects.active = arma
        
        if obj[6]:
            parentName = obj[6].name
            if(parentName):
                print('parent name' , parentName)
                parentB = arma.pose.bones.get(parentName)
                obj2.parent= arma
                obj2.parent_type = "BONE"
                obj2.parent_bone = parentName            
                obj2.matrix_parent_inverse = (arma.matrix_world @ Matrix.Translation(1 * ( parentB.tail - parentB.head)) @ parentB.matrix).inverted()
                obj2.scale = pBone.scale
        else:
             bpy.ops.object.mode_set(mode='POSE')
             TransferAnimation.transfer_keyframes(self, context)
#            
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj2.display_type = 'WIRE'
        obj2.hide_render = True
       
        

        
    bpy.ops.object.mode_set(mode='POSE')
    constraintName = 'STRETCH_TO' if context.scene.boneStretch == True else 'DAMPED_TRACK'
    constraintNameDisplace = 'COPY_LOCATION'
    for bne in blist:

        bn = bne[10]

        nme = 'BoneDynamics-damped-' + bne[10].name
        crobname = bne[10].name + '|' + bne[10].id_data.name
        obj = bpy.data.objects[crobname]
        if bn.displace:
            dnme = 'BoneDynamics-displace-' + bne[10].name
            crd = (bn.constraints.get(dnme)
                or bn.constraints.new(type=constraintNameDisplace))
            crd.target = obj 
            crd.subtarget = "Pin"
            crd.name= dnme
        cr = (bn.constraints.get(nme)
                or bn.constraints.new(type=constraintName))
        
        cr.target = obj 
        cr.subtarget = "Fall"
        cr.name= 'BoneDynamics-damped-' + bne[0]
       
            
        # cr.bulge = 0
        context_py = bpy.context.copy()
        context_py["constraint"] = cr
    # arma.data.bones[parent.name].select = False
    # bpy.context.object.data.layers = previouslayers
    # Ebone = arma.data.bones[parentName]
    # arma.data.bones.active = Ebone
          



def makeChainphysics(self , context, previouslayers):
    arma = context.active_object
#    bpy.ops.object.mode_set(mode='OBJECT')
  
    parent = findroot(self , context)    
    for num,  ob in enumerate(context.selected_pose_bones):
        if ob.bone.use_connect == False and  ob != parent:
           self.report({'WARNING'}, "using the chain mode on disconnected bones can lead to errors.")
           break
    boneLength = 0
    verts = list()
    edges = list()
    numb = 0 
    my_dict = [];
#    recursiveList = [value for value in parent.children_recursive if value in context.selected_pose_bones]
    tails = {}
    for num,  ob in enumerate(context.selected_pose_bones):
        recursive = [value for value in ob.children_recursive if value in context.selected_pose_bones]
        tails[ob.name] = 1 - (len(recursive) / len(context.selected_pose_bones) )


    for num,  ob in enumerate(context.selected_pose_bones):
        if 'dynamics' in ob :
            continue

        T =  Matrix.Translation(ob.tail - ob.head)
        matrix_final = arma.matrix_world @ (T @ ob.matrix)
        thead= Matrix.Translation(1.0 * (ob.tail - ob.head))
        ttail=  Matrix.Translation(0 * (ob.tail - ob.head))
        mathead = arma.matrix_world @ (thead @ ob.matrix)
        mattail = arma.matrix_world @ (ttail @ ob.matrix)
        headpos = mathead.to_translation()
        tailpos = mattail.to_translation()
        verts.append(headpos)
        verts.append(tailpos)
        my_dict.append([ob.name, headpos , tailpos])
        boneLength = (ob.length / context.scene.boneLength )* abs(arma.scale.x)
        edges.append([num + numb , num + numb+1])
        edges.append([num + numb + 1 , num + numb])
        numb += 1 
        if parent:
            name = parent.name + '|' + parent.id_data.name
            if ob != parent:
                ob['dynamics'] = True
                ob['chain'] = True
        else: 
            name = ob.name + '|' + ob.id_data.name
        print('bonelength' , boneLength) 
        bpy.ops.ed.undo_push()
        if ob == context.selected_pose_bones[-1]:
          mesh = bpy.data.meshes.new(name) 
          mesh.from_pydata(verts, edges, []) 
          obj = bpy.data.objects.new(name, mesh) 
          bpy.data.collections['BoneDynamics'].objects.link(obj)
          for bone  in context.selected_pose_bones:
            bone.bbdObject = obj
          bpy.ops.object.mode_set(mode='OBJECT')
          bpy.ops.object.select_all(action='DESELECT')
          context.view_layer.objects.active = obj 
          obj.select_set(True)
          obj["dynamics"] = True
          obj["chain"] = True
          obj['arma'] = arma.id_data
          bpy.context.object.data.validate()
          bpy.ops.object.mode_set(mode='EDIT')
          bpy.ops.mesh.select_all(action='SELECT')
          print('bonelength' , boneLength)
          bpy.ops.mesh.remove_doubles(threshold= boneLength)
          bpy.ops.object.mode_set(mode='OBJECT')
          bm = obj.data

          for v in bm.vertices:
                for b in my_dict:
                    result = v.co - b[1]     
                    if result.length < abs(boneLength):
                        if b[0] == parent.name:
                             if not "Pin" in [g.name for g in obj.vertex_groups]:
                                pin_group = obj.vertex_groups.new(name = "Pin")
                                pin_group.add([v.index], 1.0, 'REPLACE')
                             else:
                                pin_group = obj.vertex_groups["Pin"]
                                pin_group.add([v.index], 1.0, 'REPLACE')
                            
    
                        group = obj.vertex_groups.new(name = b[0])
                        
                        tailsgroup = (obj.vertex_groups.get("tails")
                                or obj.vertex_groups.new(name = "tails"))
                        if  b[0] != parent.name:
                           tailsgroup.add([v.index], tails[b[0]], 'REPLACE')
                        obj.vertex_groups[group.index].add([v.index], 1.0, 'REPLACE')
          vgroup_names = {vgroup.index: vgroup.name for vgroup in obj.vertex_groups}
          vgroups = {v.index: [vgroup_names[g.group] for g in v.groups] for v in bm.vertices}
          for v in bm.vertices:
              if len(vgroups[v.index])  == 0:
                  if not "Pin" in [g.name for g in obj.vertex_groups]:
                    pin_group = obj.vertex_groups.new(name = "Pin")
                  else:
                    pin_group = obj.vertex_groups["Pin"]
                  obj.vertex_groups[pin_group.index].add([v.index], 1.0, 'REPLACE')
          bpy.context.object.data.validate()
             
          bpy.ops.object.mode_set(mode='OBJECT')

          bpy.context.view_layer.objects.active = arma

          if(parent.name):
                parentB = arma.pose.bones.get(parent.name)
                obj.parent= arma
                obj.parent_type = "BONE"
                obj.parent_bone = parent.name
                obj.matrix_parent_inverse = (arma.matrix_world @ Matrix.Translation(parentB.tail - parentB.head) @ parentB.matrix).inverted()
         

          bpy.ops.object.mode_set(mode='POSE') 
          bpy.context.view_layer.objects.active = arma
             
          for bone  in context.selected_pose_bones: 
            if bone == parent:
                continue
            bn = arma.pose.bones.get(bone.name)
            nme = 'BoneDynamics-damped-' + bone.name
            constraintName = 'STRETCH_TO' if context.scene.boneStretch == True else 'DAMPED_TRACK'
            cr = (bn.constraints.get(nme)
                    or bn.constraints.new(type=constraintName))
#            obj = bpy.data.objects[name]
            cr.target = obj 
            cr.subtarget = bone.name
            cr.name= nme       
          bpy.ops.object.mode_set(mode='OBJECT')
          if context.scene.clothMode:
            addClothPhysics(self, context, obj , bone , boneLength)
          else:
              addSoftBody(self, context, obj , bone  )
            
    context.view_layer.objects.active = arma 
    bpy.ops.object.mode_set(mode='POSE')

    

def addClothPhysics (self , context, obj , bone , boneLength):
          bpy.ops.object.select_all(action='DESELECT')
          context.view_layer.objects.active = obj 
          obj.select_set(True)
          bpy.ops.object.mode_set(mode='EDIT')
          bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
          bpy.ops.mesh.select_all(action='SELECT')
          bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(boneLength*4,0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL'})

          bpy.ops.object.mode_set(mode='OBJECT')
          modi = obj.modifiers.new(name = "Cloth", type='CLOTH')
          mod = modi.settings     
          mod.bending_model = 'LINEAR'  
          modi.point_cache.frame_start = context.scene.frame_start 
          modi.point_cache.frame_end = context.scene.frame_end 
          if context.scene.chainMode: 
            mod.vertex_group_mass = "Pin"
          if bone.displace:
            mod.vertex_group_mass = "Displace"
          mod.quality = 9
          modi.collision_settings.use_collision = True
          modi.collision_settings.collision_quality = 4
          mod.time_scale = 1.7

          bpy.ops.object.select_all(action='DESELECT')

def addSoftBody (self , context, obj , bone ):
          bpy.ops.object.select_all(action='DESELECT')
          context.view_layer.objects.active = obj 
          obj.select_set(True)
          modi = obj.modifiers.new(name = "Soft Body", type='SOFT_BODY')
          mod = modi.settings       
          modi.point_cache.frame_start = context.scene.frame_start 
          modi.point_cache.frame_end = context.scene.frame_end  
          mod.vertex_group_goal = "Pin"
          mod.vertex_group_mass = 'tails'
          mod.use_edges = True
          mod.use_face_collision = True
          mod.use_edge_collision = True
          mod.use_stiff_quads = True
          mod.damping = 0
          mod.step_min = 60
          mod.spring_length = 100
          mod.goal_default = 1  
          mod.use_self_collision = True
          mod.choke = 0
        ## settings ##


          mod.friction = bone.boneFriction
#          multiplier = len(arma.data.bones[obj[0]].children_recursive)
          mod.mass= bone.boneMass 
          mod.goal_spring  = bone.boneStiffness
          mod.goal_friction = bone.boneDamping
          mod.goal_min = bone.boneStrength
          mod.speed = bone.boneSpeed
          mod.bend = bone.boneBend
          mod.pull =  1.0 - bone.boneElasticity
          mod.push =  1.0 - bone.boneElasticity
          bpy.ops.object.select_all(action='DESELECT')



def clearScene(self,context):
    bonenames = []
    for bone in bpy.context.selected_pose_bones:
        for c in bone.constraints:
            
             if c.name == 'BoneDynamics-damped-' + bone.name or c.name == "BoneDynamics-displace-" + bone.name :
                if c.name == "BoneDynamics-displace-" + bone.name:
                    if not bone.id_data.override_library: 
                        toggleConnect(self , context, bone , True)
                bone.constraints.remove( c )
                obname = bone.name + '|' + bone.id_data.name
                bonenames.append(obname)
                    
        try:
                bpy.data.objects.remove(bone['bbdObject'], do_unlink = True)
        except:
                print('object not found')
        try:
            for c in bpy.data.collections['BoneDynamics'].objects:
                if c.name in bonenames:
                    bpy.data.objects.remove(bpy.context.scene.objects[c.name], do_unlink = True)
        except:
                print('object not found')
        try:
            del bone['chain']
        except:
            print('property not found')
        try:
            del bone['displace']
        except:
            print('property not found')
        try:
                del bone['dynamics']
                del bone['bbd-parent']
        except:
                print('property not found')
                
    if len(bpy.data.collections['BoneDynamics'].objects) < 1:
        coll = bpy.data.collections.get('BoneDynamics')
        bpy.data.collections.remove(coll)
    bonenames.clear() 
         
     

class SyncTimeRange(bpy.types.Operator):
     """Synchronize the dynamic bones baking range with the timeline"""
     bl_idname = "object.sync_timerange"
     bl_label = "Sync Time Range"
     bl_options = {'REGISTER', 'UNDO'}
     
     @classmethod
     def poll(cls, context): 
        if context.mode == 'POSE' and len(context.selected_pose_bones) > 0:                  
            return True
        else:
            return False
        return context.active_object.type == "ARMATURE"
    
     def sync_timerange(self, context):
        arma = context.active_object
        start = context.scene.frame_start 
        end = context.scene.frame_end
        objects_list=[]
        for bone in bpy.context.selected_pose_bones:
            if bone.bbdObject:
                objects_list.append(bone.bbdObject)        
        if len(objects_list) > 0:
            for obj in objects_list:
                for modifier in obj.modifiers:
                  if modifier.type == "SOFT_BODY" or  modifier.type == "CLOTH":
                      modifier.point_cache.frame_start = start
                      modifier.point_cache.frame_end = end
     
     def execute(self, context):
        self.sync_timerange(context) 
        
        return {'FINISHED'} 
    
class TransferAnimation(bpy.types.Operator):
     """Transfer animation to the mesh that controls the bone"""
     bl_idname = "object.transfer_animation"
     bl_label = "Transfer Animation"
     bl_options = {'REGISTER', 'UNDO'}
     
     @classmethod
     def poll(cls, context): 
        if context.mode == 'POSE' and len(context.selected_pose_bones) > 0 and context.active_pose_bone.bbdObject and not  'chain' in context.active_pose_bone :                  
            return True
        else:
            return False
        return context.active_object.type == "ARMATURE"
    


     def transfer_keyframes(self, context):
        
        arma = context.active_object
        start = context.scene.frame_start 
        end = context.scene.frame_end
        objects_list=[]
        bone_names = [b.name for b in bpy.context.selected_pose_bones]
        bone = context.active_pose_bone
        obj = bone.bbdObject
        nme = 'BoneDynamics-damped-' + bone.name
        crobname = bone.name + '|' + bone.id_data.name
        dnme = 'BoneDynamics-displace-' + bone.name
        constraint1 = bone.constraints.get(nme)
        constraint2 = bone.constraints.get(dnme)

        
        if constraint1:
             constraint1.enabled = False       
        if constraint2:
             constraint2.enabled = False                  
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')       
        obj.select_set(True) 
        context.view_layer.objects.active = obj
        context.scene.frame_current = context.scene.frame_start
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        mod = None
        for modifier in obj.modifiers:
                  if modifier.type == "SOFT_BODY" or  modifier.type == "CLOTH":
                      mod = modifier
                      modifier.show_viewport = False  

#        cr = obj.constraints.new(type="CHILD_OF")     
#        cr.target = arma
#        cr.subtarget = bone.name
        obj.animation_data_clear()
        obj.parent = arma 
        obj.parent_type = 'BONE'
        obj.parent_bone = bone.name
        obj.matrix_parent_inverse = (arma.matrix_world @ Matrix.Translation(bone.tail - bone.head) @ bone.matrix).inverted()
        end = context.scene.frame_end
        start = context.scene.frame_start
        bpy.ops.nla.bake(frame_start=start, frame_end=end, clear_parents=True, visual_keying=True, clear_constraints=True, clean_curves=True, use_current_action=True, bake_types={'OBJECT'})
#         bpy.ops.nla.bake(frame_start=math.floor(first), frame_end=math.floor(last), bake_types={'POSE'})

        mod.show_viewport = True 
        if constraint1:
             constraint1.enabled = True   
        if constraint2:
             constraint2.enabled = True   
        bpy.ops.object.select_all(action='DESELECT')  
        arma.select_set(True)
        context.view_layer.objects.active = arma
        bpy.ops.object.mode_set(mode='POSE')
        context.active_pose_bone.toggleConstraints = True           
     def execute(self, context):
        self.transfer_keyframes(context) 
        
        return {'FINISHED'}                   
                      
                      
class AddPhysics(bpy.types.Operator):
    """Make the bone dynamic"""
    bl_idname = "object.add_physics"
    bl_label = "Simple Object Operator"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context): 
        if context.mode == 'POSE' and len(context.selected_pose_bones) > 0:                  
            return True
        else:
            return False
        return context.active_object.type == "ARMATURE"
    

    def execute(self, context):
        findCollection(context)
        main(self ,context) 
        
        return {'FINISHED'}
    
class RemovePhysics(bpy.types.Operator):
    """Restore the bone to its original state"""
    bl_idname = "object.remove_physics"
    bl_label = "Simple Object Operator"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not any(collection.name == "BoneDynamics" for collection in bpy.data.collections):
            return False
        if context.mode == 'POSE':
            return True
        else:
            return False
        return context.active_object.type == "ARMATURE"

    def execute(self, context ):
        clearScene(self ,context)

        return {'FINISHED'}
    

class SetDefault(bpy.types.Operator):
    """Set current parameters to default"""
    bl_idname = "object.set_default"
    bl_label = "Simple Object Operator"

    @classmethod
    def poll(cls, context):
        if context.mode == 'POSE' and len(context.selected_pose_bones) > 0: 
            return True
        else:
            return False
        return context.active_object.type == "ARMATURE"

    def execute(self, context):
        setDefault(self , context)
        

        return {'FINISHED'}

class SelectBone(bpy.types.Operator):
    """Select current bone"""
    bl_idname = "object.select_bone"
    bl_label = "Select this bone"
    bone_name : bpy.props.StringProperty(default="", options = {'HIDDEN'})


    @classmethod
    def poll(cls, context):
        if context.mode == 'POSE' : 
            return True
        else:
            return False

    def execute(self, context ):
        arma = context.active_object
        name = self.bone_name.split('|')

        bpy.ops.pose.select_all(action='DESELECT')
        Ebone = arma.data.bones[name [0]]
        Ebone.select = True
        
        arma.data.bones.active = Ebone

        return {'FINISHED'}


def updateToggleConstraints(self , context):
    bone = self
    nme = "BoneDynamics-displace-" + self.name
    nme2 = "BoneDynamics-damped-" + self.name
    cr = bone.constraints.get(nme)
    cr2 = bone.constraints.get(nme2)
    if cr:
        cr.enabled = self.toggleConstraints
    if cr2:
        cr2.enabled = self.toggleConstraints

class ExecutePresets(bpy.types.Operator):
    """Execute a preset"""
    bl_idname = "script.execute_bdpresets"
    bl_label = "Execute a Python Preset"

    filepath: bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE'},
    )
    menu_idname: bpy.props.StringProperty(
        name="Menu ID Name",
        description="ID name of the menu this was called from",
        options={'SKIP_SAVE'},
    )

    def execute(self, context):
        
        filepath = self.filepath

        # change the menu title to the most recently chosen option
        preset_class = getattr(bpy.types, self.menu_idname)
        preset_class.bl_label = bpy.path.display_name(basename(filepath))

        ext = splitext(filepath)[1].lower()
        print('presets execution' , filepath)
        if ext not in {".py", ".xml"}:
            self.report({'ERROR'}, "Unknown file type: %r" % ext)
            return {'CANCELLED'}

        if ext == ".py":
            try:
                print('exec preset ' +  preset_class.bl_label )
                bpy.utils.execfile(filepath)
                bpy.utils.execfile(filepath)
            except Exception as ex:
                self.report({'ERROR'}, "Failed to execute the preset: " + repr(ex))

        elif ext == ".xml":
            import rna_xml
            rna_xml.xml_file_run(context,
                                 filepath,
                                 preset_class.preset_xml_map)     

        return {'FINISHED'}

class OBJECT_MT_display_presets(Menu):
    bl_label = "Presets"
    preset_subdir = "bonedynamics"
    preset_operator = "script.execute_bdpresets"
    preset_operator_defaults = {
            "menu_idname" : 'OBJECT_MT_display_presets'
            }
    draw = Menu.draw_preset
    @classmethod
    def poll(cls, context): 
        return True


class AddPresetObjectDisplay(AddPresetBase, bpy.types.Operator):
    '''Save current parameters'''
    bl_idname = "bonedynamics.object_display_preset_add"
    bl_label = "Save as a preset"
    preset_menu = "OBJECT_MT_display_presets"
    @classmethod
    def poll(cls, context): 
        if context.mode == 'POSE' and len(context.selected_pose_bones) > 0:                  
            return True
        else:
            return False
    # variable used for all preset values
    preset_defines = [
        "obj = bpy.context.active_pose_bone",
        "objs = bpy.context.selected_pose_bones",
        "for i in objs:i.boneMass = obj.boneMass;i.boneFriction = obj.boneFriction;i.boneDamping = obj.boneDamping;i.boneStrength = obj.boneStrength;i.boneStiffness = obj.boneStiffness;i.boneSpeed = obj.boneSpeed;i.boneElasticity = obj.boneElasticity;i.boneBend = obj.boneBend"
    ]

    # properties to store in the preset
    preset_values = [
        
        "obj.boneMass",
        "obj.boneFriction",
        "obj.boneDamping",
        "obj.boneStrength",
        "obj.boneStiffness",
        "obj.boneBend",
        "obj.boneSpeed",
        "obj.boneElasticity",
       
    ]

    # where to store the preset
    preset_subdir = "bonedynamics"


class BONES_PT_Panel(Panel):
    bl_label = "Dynamic Bones"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Bone Dynamics Pro'
    bl_parent_id = "BBD_PT_PANEL"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout 
        col= layout.column()
        col.operator('object.sync_timerange', text ="Sync Time Range" )        
        for objj in bpy.data.objects:
            try :
                objj['dynamics'] 
                if objj['arma'] == context.active_object.id_data :              
                    rowb = layout.row(align=True)
                    rowb.label(text=objj.name, icon="BONE_DATA")
                    arma =objj['arma']
                    bone = arma.pose.bones.get(objj['bone'])  
                    if context.mode == 'POSE' :
                       rowb.operator('object.select_bone' , text="",icon='RESTRICT_SELECT_OFF').bone_name=objj.name
                       
                       rowb.prop(bone,"toggleConstraints",text="", icon='HIDE_ON' if not bone.toggleConstraints else 'HIDE_OFF' , toggle= False)
                       
                    for mod in objj.modifiers:
                        if mod.type == "SOFT_BODY" or mod.type == "CLOTH" :
                            rowb.prop(mod,'show_viewport' ,text="")


                    
            except:
                continue



class BBD_PT_Panel(Panel):
    bl_label = "Bone Dynamics Pro"
    bl_idname = "BBD_PT_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Bone Dynamics Pro'

    def draw(self, context):

        layout = self.layout
        col = layout.column_flow(align=True)
        rowp = col.row(align=True)
        if context.mode == 'POSE' :
            rowp.menu(OBJECT_MT_display_presets.__name__, text=OBJECT_MT_display_presets.bl_label)
            rowp.operator(AddPresetObjectDisplay.bl_idname, text="", icon='ADD')
            rowp.operator(AddPresetObjectDisplay.bl_idname, text="", icon='REMOVE').remove_active = True
        row2 = layout.column(align=True)
        row2.operator('object.add_physics', text ="Add Bone Dynamics" )
        row2.operator('object.remove_physics', text ="Remove Bone Dynamics" )
        row2.operator('object.set_default', text ="Reset Parameters" )   
        row2.operator('wm.myop', text ="Bake Animation" )
        row2.operator('object.transfer_animation', text ="Transfer Animation" )
        
        row3 = layout.column(align=True)
        row4 = layout.column(align=True)
            
        row4.prop(context.scene, "boneStretch" , toggle=1 )
        row4.prop(context.scene, "chainMode" , toggle=1)
        row4.prop(context.scene, "clothMode" , toggle=1)
        row4.prop(context.scene, "dynamicParent" , toggle=1)

        if context.scene.chainMode:
            row4.prop(context.scene, "bonedynamicsDebug" , toggle=1)
            if context.scene.bonedynamicsDebug:
                 row4.prop(context.scene, "boneLength" )
        
       


        if  context.mode == 'POSE' and context.active_object.type == "ARMATURE" and context.active_pose_bone and not context.scene.clothMode:
            bone = context.active_pose_bone
#            lst = ', '.join(str(x.name) for x in context.selected_pose_bones)
            row = layout.column(align=True )
            col = layout.row(align=True)
#            col.label(text=lst)
            row.prop(bone,  "displace" , toggle=1  )
            row.prop(bone,  "boneMass")
            row.prop(bone,  "boneFriction")
            row.prop(bone,  "boneDamping")
            row.prop(bone,  "boneStrength")
            row.prop(bone,  "boneStiffness")
            row.prop(bone,  "boneSpeed")
            row.prop(bone,  "boneBend")
            row.prop(bone,  "boneElasticity")
            row.prop(bone,  "toggleDynamics" )
            row.prop(bone,  "boneGravity" )
            
            
       
            



class WM_OT_bakeBone(bpy.types.Operator):
    """bake the physics of the selected bones into keyframes (Playback sync needs to be in 'Play Every Frame') """
    bl_idname = "wm.myop"
    bl_label = "Bake the animation of the selected bones"
    # clear scene
    prop1: bpy.props.BoolProperty(default = True)

    @classmethod
    def poll(cls, context):
        if context.mode == 'POSE' and len(context.selected_pose_bones) > 0 and context.active_object.type == "ARMATURE": 
            return True
        else:
            return False

    def execute(self, context):
        arma = context.active_object
        start = context.scene.frame_start 
        bpy.context.scene.sync_mode = 'NONE'
        for name in [b.name for b in context.selected_pose_bones]:
            ob = arma.pose.bones[name]

            bdobj = ob.get('bbdObject')
            if bdobj:
                ob.bone.inherit_scale = 'ALIGNED'
                continue

            bpy.ops.pose.select_all(action='DESELECT')
        end = context.scene.frame_end
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        arma.select_set(True)
        stepd = context.scene.bakeStep / 100
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.nla.bake(frame_start = start, frame_end = end,  step= 1 , use_current_action = True, only_selected = True, visual_keying = True, clean_curves=True, bake_types={'POSE'}, channel_types={'LOCATION', 'ROTATION', 'SCALE'})
        # bpy.ops.nla.bake(frame_start = start, frame_end = end,  step= 1 , use_current_action = context.scene.bakeStrip, only_selected = True, visual_keying = True, clean_curves=True, bake_types={'POSE'})
        area = context.area
        old_type = area.type
        area.type = 'GRAPH_EDITOR'
        bpy.ops.graph.clean(channels=True)
        bpy.ops.graph.decimate(mode='RATIO', factor=context.scene.bakeStep)
        area.type = old_type
        if self.prop1:
            clearScene(self , context)

        
        return {'FINISHED'}
   
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    def draw(self, context):
        row = self.layout
        row.label(text='IMPORTANT:',  translate=True, icon='NONE', icon_value=0)
        row.label(text='the baking range will follow the timeline length.',  translate=True, icon='NONE', icon_value=0)
        row.label(text='You need to play fully the animation at least once',  translate=True, icon='NONE', icon_value=0)
        row.label(text='Make sure that your playback sync is set to play every frame',  translate=True, icon='NONE', icon_value=0)
        row.prop(self, "prop1", text="Clear constraints and physics object" )
        row.prop(context.scene, "bakeStep", text="Simplification factor" , slider=True  )
        # row.prop(context.scene, "bakeStrip", text="Bake into a new strip")
        

class BdModalOperator(bpy.types.Operator):
    bl_idname = "object.bd_modal_operator"
    bl_label = "Simple Modal Operator"

    def execute(self, context):
        
        ### invalidate the physics cache ####
        bone = context.active_pose_bone
        if bone:
            arma = bone.id_data
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            coll = bpy.data.collections['BoneDynamics']
            if coll: 
                 for obj in coll.all_objects:
                     obj.select_set(True)
                     bpy.context.view_layer.objects.active = obj
                 bpy.ops.object.editmode_toggle()             
                 bpy.ops.object.editmode_toggle() 
                 bpy.ops.object.select_all(action='DESELECT')
                 arma.select_set(True) 
                 bpy.context.view_layer.objects.active = arma
                 bpy.ops.object.mode_set(mode='POSE')   

        
        return {'FINISHED'}

    def modal(self, context, event):
       
        if event.type == 'R':  # Confirm
           
            bpy.ops.transform.rotate('INVOKE_DEFAULT')
            if context.mode =="POSE" and context.active_pose_bone:
#                print('bone is being rotated')
                if "dynamics" in self.bne and not "chain" in self.bne:
                    self.cr.enabled = False
                if "displace" in self.bne and not "chain" in self.bne:
                    self.cr2.enabled = False
            return {'PASS_THROUGH'}
        
        if event.type == 'G':  # Confirm
           

            
            bpy.ops.transform.translate('INVOKE_DEFAULT')
            if context.mode =="POSE" and context.active_pose_bone:
                 if "dynamics" in self.bne and not "chain" in self.bne:
                    self.cr.enabled = False
                 if "displace" in self.bne and not "chain" in self.bne:
                    self.cr2.enabled = False
#                print('bone is being translated')


            return {'PASS_THROUGH'}
     
        elif event.type == 'LEFTMOUSE':  # Confirm
            if self.bne and "dynamics" in self.bne:

                obj2 = self.bne['bbdObject']
                if obj2  and not "chain" in self.bne:
                    ob = bpy.context.active_pose_bone
                    arma  = ob.id_data
                    parentB = arma.pose.bones.get(obj2.parent_bone)
                    mw = arma.convert_space(pose_bone=self.bne, matrix=self.bne.matrix, from_space="POSE" , to_space="WORLD")
                    mat_rot_mx = Matrix.Rotation(math.radians(-90.0), 4, 'X')
                    obj2.matrix_world = mw @ mat_rot_mx
                    
                    if parentB:
                        obj2.matrix_parent_inverse = (arma.matrix_world @ Matrix.Translation(1 * (parentB.tail - parentB.head)) @ parentB.matrix).inverted()
                    if "dynamics" in self.bne:
                        self.cr.enabled = True
                    if "displace" in self.bne:
                        self.cr2.enabled = True
 
                    if context.scene.tool_settings.use_keyframe_insert_auto:
#                        print('autokeying is on')
                        obj2.keyframe_insert("rotation_quaternion")

                    
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel
            # Revert all changes that have been made
#            print('bone rotation has been  cancelled')
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):


            
            self.bne = context.active_pose_bone
            if self.bne and "dynamics" in self.bne:
                nme = 'BoneDynamics-damped-' +  self.bne.name
                nme2 = 'BoneDynamics-displace-' +  self.bne.name
                self.cr = self.bne.constraints.get(nme)
                self.cr2 = self.bne.constraints.get(nme2)
                self.execute(context)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
         
                 
addon_keymaps = []
       
def register():
    bpy.utils.register_class(BBD_PT_Panel)
    bpy.utils.register_class(BONES_PT_Panel)
    bpy.utils.register_class(AddPhysics)
    bpy.utils.register_class(SetDefault)
    bpy.utils.register_class(ExecutePresets)
    bpy.utils.register_class(OBJECT_MT_display_presets)
    bpy.utils.register_class(AddPresetObjectDisplay)
    bpy.utils.register_class(WM_OT_bakeBone)
    bpy.utils.register_class(SelectBone)
    bpy.utils.register_class(SyncTimeRange)
    bpy.utils.register_class(TransferAnimation)
    bpy.utils.register_class(RemovePhysics)
    bpy.utils.register_class(BdModalOperator)
    
  

    bpy.types.Scene.chainMode = bpy.props.BoolProperty(name="Chain mode",description="Only for connected bones ", default = False , update=updateChain ) 
    bpy.types.Scene.clothMode = bpy.props.BoolProperty(name="Cloth mode",description="Only for connected bones, This mode is useful for hair or clothes", default = False, update=updateCloth   ) 
    bpy.types.Scene.boneStretch = bpy.props.BoolProperty(name="Allow Stretching",description="allow the bones to stretch",default = False)
    bpy.types.Scene.bakeStrip = bpy.props.BoolProperty(name="Allow Stretching",description="allow the bones to stretch",default = False)
    bpy.types.Scene.bonedynamicsDebug = bpy.props.BoolProperty(name="Debug",description="Debug mode", default = False  )
    bpy.types.Scene.dynamicParent = bpy.props.BoolProperty(name="Dynamic Parent",description="Enable this if you want the active bone to be the parent", default = False  )
    bpy.types.Scene.bakeStep = bpy.props.FloatProperty(name = "Curve simplification",description="Higher number means lower keyframes and less accuracy too.",default =0.5,min = 0,max =1)
    bpy.types.Scene.boneLength =  bpy.props.FloatProperty(name = "Bone Length",description="If the chain is not working properly. Try changing this parameter",default = 100 ,min = 10,max = 1000 , step=100, options = {'LIBRARY_EDITABLE' }, override = {'LIBRARY_OVERRIDABLE'} )
    bpy.types.PoseBone.bbdObject = bpy.props.PointerProperty(name = "bbd pointer" , type=bpy.types.Object ,  options = {'LIBRARY_EDITABLE', "HIDDEN" }, override = {'LIBRARY_OVERRIDABLE'}  )
    bpy.types.PoseBone.toggleConstraints = bpy.props.BoolProperty(name = "toggle constraintes"  , default = True , update=updateToggleConstraints,  options = {'LIBRARY_EDITABLE', "HIDDEN" }, override = {'LIBRARY_OVERRIDABLE'} )
    bpy.types.PoseBone.displace = bpy.props.BoolProperty(name="Displacement",description="Allow the bone to translate on top of rotating ", default = False , update=updateDisplace ,  options = {'LIBRARY_EDITABLE' }, override = {'LIBRARY_OVERRIDABLE'}  )
    bpy.types.PoseBone.dynamics = bpy.props.BoolProperty(name="Dynamics",description="Dynamics", default = False ,  options = {'LIBRARY_EDITABLE' , "HIDDEN" }, override = {'LIBRARY_OVERRIDABLE'}  )
    bpy.types.PoseBone.displaceOrg = bpy.props.BoolProperty(name="Displacement original",description="original bone connect", default = False ,  options = {'LIBRARY_EDITABLE', "HIDDEN" }, override = {'LIBRARY_OVERRIDABLE'} )  
    bpy.types.PoseBone.boneMass = bpy.props.FloatProperty(name = "Mass",description="Mass of the bone",default = 0.3,min = 0,max = 50 , update=updateMass,  options = {'LIBRARY_EDITABLE' , "HIDDEN" }, override = {'LIBRARY_OVERRIDABLE'} )
    bpy.types.PoseBone.boneFriction = bpy.props.FloatProperty(name = "Friction",description="Air thickness",default = 12,min = 0,max = 50 , update=updateFriction, options = {'LIBRARY_EDITABLE' }, override = {'LIBRARY_OVERRIDABLE'} )
    bpy.types.PoseBone.boneStiffness = bpy.props.FloatProperty(name = "Stiffness",description="Stiffness of the bone",default = 0.9,min = 0,max = 0.99, update=updateStiffness, options = {'LIBRARY_EDITABLE' }, override = {'LIBRARY_OVERRIDABLE'}  )
    bpy.types.PoseBone.boneDamping = bpy.props.FloatProperty(name = "Damping",description="Damping of the bone",default = 10,min = 0,max = 50, update=updateDamping, options = {'LIBRARY_EDITABLE' }, override = {'LIBRARY_OVERRIDABLE'})
    bpy.types.PoseBone.boneStrength = bpy.props.FloatProperty(name = "Strength",description="Strength of the bone",default = 0.7 ,min = 0,max = 1 , update=updateStrength, options = {'LIBRARY_EDITABLE' }, override = {'LIBRARY_OVERRIDABLE'})
    bpy.types.PoseBone.boneSpeed = bpy.props.FloatProperty(name = "Speed",description="",default = 1 ,min = 0 ,max = 100 , update=updateSpeed, options = {'LIBRARY_EDITABLE' }, override = {'LIBRARY_OVERRIDABLE'})
    bpy.types.PoseBone.toggleDynamics =  bpy.props.FloatProperty(name = "Influence",description="",default = 1 ,min = 0 ,max = 1 , update=updateToggle, options = {'LIBRARY_EDITABLE' }, override = {'LIBRARY_OVERRIDABLE'}) 
    bpy.types.PoseBone.boneElasticity = bpy.props.FloatProperty(name = "Elasticity",description="",default = 0.01 ,min = 0 ,max = 0.99 , update=updateElasticity, options = {'LIBRARY_EDITABLE' }, override = {'LIBRARY_OVERRIDABLE'})
    bpy.types.PoseBone.boneBend = bpy.props.FloatProperty(name = "Bending",description="",default = 0.5 ,min = 0 ,max = 10 , update=updateBend, options = {'LIBRARY_EDITABLE' }, override = {'LIBRARY_OVERRIDABLE'})
    bpy.types.PoseBone.boneGravity = bpy.props.FloatProperty(name = "Gravity",description="",default = 1.0 ,min = -10 ,max = 10 , update=updateGravity, options = {'LIBRARY_EDITABLE' }, override = {'LIBRARY_OVERRIDABLE'})

    checkPresets()
   
    # Add the hotkeys
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(BdModalOperator.bl_idname, type='R', value='PRESS'  )
        kmg = km.keymap_items.new(BdModalOperator.bl_idname, type='G', value='PRESS'  )
        addon_keymaps.append((km, kmi))
        addon_keymaps.append((km, kmg))
   
def unregister():
    bpy.utils.unregister_class(BBD_PT_Panel)
    bpy.utils.unregister_class(BONES_PT_Panel)
    bpy.utils.unregister_class(AddPhysics)
    bpy.utils.unregister_class(RemovePhysics)
    bpy.utils.unregister_class(SetDefault)
    bpy.utils.unregister_class(OBJECT_MT_display_presets)
    bpy.utils.unregister_class(AddPresetObjectDisplay)
    bpy.utils.unregister_class(ExecutePresets)
    bpy.utils.unregister_class(WM_OT_bakeBone)
    bpy.utils.unregister_class(SelectBone)
    bpy.utils.unregister_class(SyncTimeRange)
    bpy.utils.unregister_class(TransferAnimation)
    bpy.utils.unregister_class(BdModalOperator)
    
    # Remove the hotkey
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()    
   
    del  bpy.types.Scene.boneStretch
    del  bpy.types.Scene.chainMode
    del  bpy.types.Scene.bakeStep
    del  bpy.types.Scene.clothMode
    del  bpy.types.Scene.boneLength
    del  bpy.types.Scene.dynamicParent


if __name__ == "__main__":
    register() 

