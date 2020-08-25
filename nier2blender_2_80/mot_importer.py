"""
import importlib
import nier2blender_2_80.mot_importer
importlib.reload(nier2blender_2_80.mot_importer)
"""
import bpy, bmesh, math, mathutils
import nier2blender_2_80.mot as MOT

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
			print('[MOT-Error] Unknown value type: %d' % record.valueType)
		
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
			rot_frames.append([i, mathutils.Euler((bone_records[3][i], bone_records[4][i], bone_records[5][i]), 'XYZ')])
			scale_frames.append([i, mathutils.Vector([bone_records[6][i], bone_records[7][i], bone_records[8][i]])])
	
		motion_data[bone_id] = [pos_frames, rot_frames, scale_frames]
		
	return motion_data

def construct_action(mot, motion_data, active, bind_pose): #(mot.py MOT object, motion data from above, blender active object)
	print('[+] importing motion %s' % mot.motionName)
	action = bpy.data.actions.new(name=mot.motionName)
	action.use_fake_user = True
	if active.animation_data is None:
		active.animation_data_create()
	active.animation_data.action = action
	
	bpy.context.view_layer.objects.active = active
	bpy.ops.object.mode_set(mode='POSE') #Set active to pose mode
	bone_mapping = active["bone_mapping"] #Get bones from active
	pose_bones = bpy.context.view_layer.objects.active.pose.bones 
	
	print('[MOT-Info] active.name: %s' % active.name)
	print('[MOT-Info] bpy.context.view_layer.objects.active.name: %s' % bpy.context.view_layer.objects.active.name)
	
	used_bones = []
	i = 0
	for bone_number, values in motion_data.items(): #loop through bones
		i+=1
		pos_values, rot_values, scale_values = values
		bone_name = bone_mapping.get(str(bone_number))
		if bone_number == 65535 and bone_name is None:
			bone_name = bone_mapping.get(str(4095))

		if bone_name is None:
			print('[MOT-Error] bone_number = %d not found in bone_mapping' % bone_number)
			continue
			
		pose_bone = pose_bones.get(bone_name)
		if pose_bone is None:
			print('[MOT-Error] %s not found in active.pose.bones' % bone_name)
			continue

		edit_bone_matrix = bind_pose[bone_name]
		if edit_bone_matrix is None:
			print('[MOT-Error] %s not found in bind_pose' % bone_name)
			continue
		
		if bone_name not in used_bones:
			used_bones.append(bone_name)
	
		#position/translation keyframes
		if pos_values is not None:
			for pos_value in pos_values:
				frame = pos_value[0] + 1 #set initial frame to 1
				if pos_value[1] == mathutils.Vector():
					pose_bone.location = mathutils.Vector([0,0,0])
				else:
					pose_bone.location = -(pose_bone.bone.head - pos_value[1])
				pose_bone.keyframe_insert("location", index=-1, frame=frame)
				#print('[MOT-Info] Inserting location keyframe for %s at %s on frame %d' % (bone_name, str(pose_bone.location), frame))
				#if frame == 1:
					#print('bone.head: %s, pos_value[1]" %s' % (str(pose_bone.bone.head), str(pos_value[1])))
		else:
			pose_bone.location = mathutils.Vector([0,0,0])
			pose_bone.keyframe_insert("location", index=-1, frame=1)
			#print('[MOT-Info] Inserting location keyframe for %s at %s on frame %d' % (bone_name, str(pose_bone.location), frame))
		
		#rotation keyframes
		if rot_values is not None:
			for rot_value in rot_values:
				frame = rot_value[0] + 1
				quat = rot_value[1].to_quaternion()
				pose_bone.rotation_quaternion = quat
				pose_bone.keyframe_insert("rotation_quaternion", index=-1, frame=frame)
				#print('[MOT-Info] Inserting rotation keyframe for %s at %s on frame %d' % (bone_name, str(pose_bone.rotation_quaternion), frame))
		else:
			pose_bone.rotation_quaternion = mathutils.Quaternion([1, 0, 0, 0])
			pose_bone.keyframe_insert("rotation_quaternion", index=-1, frame=1)
			#print('[MOT-Info] Inserting rotation keyframe for %s at %s on frame %d' % (bone_name, str(pose_bone.rotation_quaternion), frame))

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
		print('[MOT-Info] Finished inserting keyframes for bone %d / %d' % (i, len(motion_data.items())))

	uBones = ''
	for boneNum in used_bones:
		uBones += boneNum + ', '
	print('[MOT-Info] Motion Bones Used: ' + uBones)
	
	for fcurve in action.fcurves:
		for keyframe_point in fcurve.keyframe_points:
			keyframe_point.interpolation = 'LINEAR'
			
	bpy.ops.object.mode_set(mode='OBJECT')

def get_bind_pose(active):
	bpy.ops.object.mode_set(mode='EDIT')
	matrices = {}
	for bone in bpy.data.armatures[active.name + 'Amt'].edit_bones:
		matrices[bone.name] = bone.matrix
	bpy.ops.object.mode_set()
	return matrices

def main(mot_fp, active):
	bpy.ops.object.mode_set()
	
	mot = MOT.MOT(mot_fp)
	motion = format_motion_data(mot.frameCount, mot.records)
	bind_pose = get_bind_pose(active)
	construct_action(mot, motion, active, bind_pose)
	
	print('Motion importing finished.')
	return {'FINISHED'}

if __name__ == '__main__':
	print('[MOTError] Cant use through command line.')
