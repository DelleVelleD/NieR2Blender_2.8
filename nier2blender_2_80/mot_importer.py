"""
import importlib
import nier2blender_2_80.mot_importer
importlib.reload(nier2blender_2_80.mot_importer)
"""
import bpy, bmesh, math, mathutils
import nier2blender_2_80.mot as MOT

def show_message(message = "", title = "Message Box", icon = 'INFO'):
	def draw(self, context):
		self.layout.label(text = message)
		self.layout.alignment = 'CENTER'
	bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def format_motion_data(frame_count, records):
	formatted_records = {} #{boneNumber: POSX[], POSY[], POSZ[], ROTX[], ROTY[], ROTZ[], SCALEX[], SCALEY[], SCALEZ[]}
	
	for record in records:
		bone_records = formatted_records.setdefault(record.bone_id, [None]*9)
		if 0 <= record.valueType <= 5: # 0-5 index no change
			frames = []
			for i in range(frame_count):
				frames.append(record.get_frame(i))
				#print('[MOT-Info] Bone: %d, ValueType: %d' % (record.bone_id, record.valueType))
			bone_records[record.valueType] = frames
			
			for i,value in enumerate(bone_records[record.valueType]):
				if value is None:
					print(record.offset, record.bone_id, i, record.valueType, record.recordType)
		elif 7 <= record.valueType <= 9: # 7-9 index need to (-1), because valueType:6 skipped.
			frames = []
			for i in range(frame_count):
				frames.append(record.get_frame(i))
				#print('[MOT-Info] Bone: %d, ValueType: %d' % (record.bone_id, record.valueType))
			bone_records[record.valueType - 1] = frames
			
			for i,value in enumerate(bone_records[record.valueType - 1]):
				if value is None:
					print(record.offset, record.bone_id, i, record.valueType, record.recordType)
		else:
			print('[MOT-Error] Unknown value type:%d' % record.valueType)
		
	#fill in missing records
	default_value = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
	for bone_id, bone_records in formatted_records.items():
		for i in range(len(bone_records)):
			if bone_records[i] is None:
				bone_records[i] = [default_value[i]] * frame_count
	
	motion_data = {} #{boneNumber: POS[(frameIndex, x, y, z)], ROT[(frameIndex, x, y, z, w)], SCALE[(frameIndex, x, y, z)]}
	for bone_id, bone_records in formatted_records.items():
		pos_frames = []
		rot_frames = []
		scale_frames = []
		for i in range(frame_count):
			pos_frames.append([i, mathutils.Vector([bone_records[0][i], bone_records[1][i], bone_records[2][i]])])
			rot = mathutils.Euler((bone_records[3][i], bone_records[4][i], bone_records[5][i]), 'XYZ')
			quat = rot.to_quaternion()
			rot_frames.append([i, quat])
			scale_frames.append([i, mathutils.Vector([bone_records[6][i], bone_records[7][i], bone_records[8][i]])])
	
		motion_data[bone_id] = [pos_frames, rot_frames, scale_frames]
		
	return motion_data

def construct_action(mot, motion_data, armature): #(mot.py MOT object, motion data from above, blender armature object)
	print('[+] importing motion %s' % mot.motionName)
	action = bpy.data.actions.new(name=mot.motionName)
	action.use_fake_user = True
	if armature.animation_data is None:
		armature.animation_data_create()
	armature.animation_data.action = action
	
	bpy.context.view_layer.objects.active = armature 
	bpy.ops.object.mode_set(mode='POSE') #Set armature to pose mode
	bone_mapping = armature["bone_mapping"] #Get bones from armature
	pose_bones = bpy.context.view_layer.objects.active.pose.bones 
	
	print('[MOT-Info] armature.name: %s' % armature.name)
	print('[MOT-Info] bpy.context.view_layer.objects.active.name: %s' % bpy.context.view_layer.objects.active.name)
	
	used_bones = []
	for bone_number, values in motion_data.items(): #loop through bones
		pos_values, rot_values, scale_values = values
		bone_name = bone_mapping.get(str(bone_number))
		
		if bone_name is None:
			print('[MOT-Error] bone_number = %d not found in bone_mapping.' % bone_number)
			continue
			
		pose_bone = pose_bones.get(bone_name)
		if pose_bone is None:
			print('[MOT-Error] %s not found in armature.pose.bones.' % bone_name)
			continue
		
		if bone_name not in used_bones:
			used_bones.append(bone_name)
	
		#position/translation keyframes
		if pos_values is not None:
			for pos_value in pos_values:
				frame = pos_value[0] + 1 #set initial frame to 1
				pose_bone.location = pos_value[1]
				pose_bone.keyframe_insert("location", index=-1, frame=frame)
				#print('[MOT-Info] Inserting location keyframe for %s at %s on frame %d' % (bone_name, str(pose_bone.location), frame))
		else:
			pose_bone.location = mathutils.Vector([0,0,0]) #if no position values, set to 0,0,0, not moving the bone
			pose_bone.keyframe_insert("location", index=-1, frame=1)
			#print('[MOT-Info] Inserting location keyframe for %s at %s on frame %d' % (bone_name, str(pose_bone.location), frame))
		print('[MOT-Info] Finished inserting %d location keyframes' % len(pos_values))
		
		#rotation keyframes
		if rot_values is not None:
			for rot_value in rot_values:
				frame = rot_value[0] + 1
				pose_bone.rotation_quaternion = rot_value[1]
				pose_bone.keyframe_insert("rotation_quaternion", index=-1, frame=frame)
				#print('[MOT-Info] Inserting rotation keyframe for %s at %s on frame %d' % (bone_name, str(pose_bone.rotation_quaternion), frame))
		else:
			pose_bone.rotation_quaternion = mathutils.Quaternion([1, 0, 0, 0])
			pose_bone.keyframe_insert("rotation_quaternion", index=-1, frame=frame)
			#print('[MOT-Info] Inserting rotation keyframe for %s at %s on frame %d' % (bone_name, str(pose_bone.rotation_quaternion), frame))
		print('[MOT-Info] Finished inserting %d rotation keyframes' % len(rot_values))

		#scale keyframe
		if scale_values is not None:
			for scale_value in scale_values:
				frame = scale_value[0] + 1
				pose_bone.scale = scale_value[1]
				pose_bone.keyframe_insert("scale", index=-1, frame=frame)
				#print('[MOT-Info] Inserting scale keyframe for %s at %s on frame %d' % (bone_name, str(pose_bone.scale), frame))
		else:
			pose_bone.scale = mathutils.Vector([1, 1, 1])
			pose_bone.keyframe_insert("scale", index=-1, frame=1)
			#print('[MOT-Info] Inserting scale keyframe for %s at %s on frame %d' % (bone_name, str(pose_bone.scale), frame))
		print('[MOT-Info] Finished inserting %d scale keyframes' % len(scale_values))
			
	print('[MOT-Info] Motion Bones Used: ')
	uBones = ''
	for boneNum in used_bones:
		uBones += boneNum + ', '
	print(uBones)
	
	for fcurve in action.fcurves:
		for keyframe_point in fcurve.keyframe_points:
			keyframe_point.interpolation = 'LINEAR'
			
	bpy.ops.object.mode_set(mode='OBJECT')
	
def main(mot_fp, armature):	
	bpy.ops.object.mode_set()
	
	mot = MOT.MOT(mot_fp)
	motion = format_motion_data(mot.frameCount, mot.records)
	construct_action(mot, motion, armature)
	
	print('Motion importing finished.')
	return {'FINISHED'}

if __name__ == '__main__':
		main('', None)
