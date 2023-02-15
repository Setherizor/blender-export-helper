# S&Box Citizen's Blender Animation Exporter
# @Author Setherizor
# @LastUpdated <deploy-type>
# @LastUpdated <deploy-date>

# Warning: This export script will replace the exported files when ran. This could be descructive if you have colliding filenames.
# To understand what this script does, reference the following document and start reading from the bottom of the code here
# https://github.com/Ali3nSystems/Blender-Control-Rig-for-Terry/blob/main/Documentation/B.%20Poses%2C%20Animations%20and%20Shape%20Keys/c.%20Exporting%20Poses%20and%20Animations.pdf

# If you run into issues, you may need to clear out your "Unused Data Blocks" in the "File > Clean Up" Menu.

import bpy
import os
import sys
import time
from math import radians

# Config & Variables

# Export Method's Options: native fbx, better fbx, source tools.
# EXPORT_METHOD = "native fbx"
# EXPORT_METHOD = "better fbx"  # addon handles animation baking process
# EXPORT_METHOD = "source tools"

# BAKE_ACTION_NAME = "Baked Animation"
# CONTROLRIG_ACTION = "Control RigAction"
# ARMATURE_NAME = "Armature"
# CONTROLRIG_NAME = "Control Rig"
# obj = bpy.data.objects[ARMATURE_NAME]
# rig = bpy.data.objects[CONTROLRIG_NAME]


def error(message):
    raise Exception(message)


# try:
#     EXPORT_METHOD
# except NameError:
#     error("SCRIPT HELP: Uncomment your selected export method at the top of the script")


def step1():
    bpy.ops.object.mode_set_with_submode(mode="OBJECT")
    bpy.context.scene.frame_current = 0

    bpy.ops.object.select_all(action="DESELECT")

    rig.select_set(False)
    rig.hide_set(True)
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def step2():
    status = bpy.ops.object.posemode_toggle()

    if not status == {"FINISHED"}:
        error("Step 1: could not get into pose mode")

    bpy.ops.pose.select_all(action="SELECT")


def step3():
    # Decide to manually bake or allow the better fbx addon to take over
    if EXPORT_METHOD == "better fbx":
        action = bpy.data.actions.get(CONTROLRIG_ACTION)
        if action == None:
            error(
                "Step 3: Coule not find Control Rig Animation Action: "
                + CONTROLRIG_ACTION
            )
        obj.animation_data.action = action
    else:
        # Setup the new action
        action = bpy.data.actions.get(BAKE_ACTION_NAME)

        if action == None:
            bpy.context.area.type = "DOPESHEET_EDITOR"
            bpy.context.space_data.mode = "ACTION"
            obj.animation_data_create()  # can crash without this
            bpy.ops.action.new()
            bpy.context.area.type = "TEXT_EDITOR"

            action = bpy.data.actions.get("Action")
            action.name = BAKE_ACTION_NAME
            obj.animation_data.action = action

        # Bake
        bpy.ops.nla.bake(
            frame_start=bpy.context.scene.frame_start,
            frame_end=bpy.context.scene.frame_end,
            step=1,
            only_selected=True,
            visual_keying=True,
            clear_constraints=False,  # VERY IMPORTANT FOR BACK TO BACK EXPORTS
            use_current_action=True,
            bake_types={"POSE"},
        )

        print("Finished baking animation to armature")


def step4(undo=False):
    bpy.ops.object.mode_set_with_submode(mode="OBJECT")

    if EXPORT_METHOD == "source tools":
        bpy.data.objects[CONTROLRIG_NAME].hide_set(False)
        bpy.data.objects[CONTROLRIG_NAME].select_set(True)
        angle = 90 if undo else -90
        angle = radians(angle)
        bpy.ops.transform.rotate(value=angle, orient_axis="Z")
        bpy.data.objects[CONTROLRIG_NAME].select_set(False)
        bpy.data.objects[CONTROLRIG_NAME].hide_set(True)


def native_fbx_export(file):
    bpy.ops.export_scene.fbx(
        path_mode="AUTO",
        filepath=file,
        check_existing=False,
        use_selection=True,
        global_scale=1.0,
        apply_unit_scale=True,
        add_leaf_bones=False,
        bake_anim=True,
    )


def better_fbx_export(file):
    bpy.ops.better_export.fbx(
        filepath=file,
        check_existing=False,
        my_file_type=".fbx",
        my_fbx_unit="m",
        use_selection=True,
        use_animation=True,
        my_scale=1,
        use_optimize_for_game_engine=True,
        use_reset_mesh_origin=True,
        use_reset_mesh_rotation=True,
        use_only_root_empty_node=True,
        use_ignore_armature_node=True,
        use_edge_crease=True,
        my_edge_smoothing="FBXSDK",
        my_edge_crease_scale=1,
        my_separate_files=False,
    )


def source_tools_export(file):
    bpy.context.scene.vs.export_path = "//"
    bpy.context.scene.vs.dmx_encoding = "9"
    bpy.context.scene.vs.dmx_format = "22_modeldoc"
    try:
        bpy.ops.export_scene.smd(collection="Terry", export_scene=False)
        os.remove(file.replace(".fbx", ".dmx"))
        os.rename("Terry.dmx", file.replace(".fbx", ".dmx"))
    except:
        pass


def step5():
    output_dir = ""
    blend_file_path = bpy.data.filepath
    blend_file_name = bpy.path.basename(bpy.context.blend_data.filepath)
    file_name = os.path.splitext(blend_file_name)[0]
    fbx_file_name = file_name + ".fbx"
    target_file = os.path.join(output_dir, fbx_file_name)

    if EXPORT_METHOD == "native fbx":
        native_fbx_export(target_file)
    elif EXPORT_METHOD == "better fbx":
        better_fbx_export(target_file)
    elif EXPORT_METHOD == "source tools":
        source_tools_export(target_file)


def cleanup_bake(preclean=False):
    obj.animation_data_create()  # can crash without this

    if EXPORT_METHOD == "better fbx":
        obj.animation_data.action = None
    else:
        # Clear out animation bake
        action = bpy.data.actions.get(BAKE_ACTION_NAME)

        if not action == None:
            action.user_clear()
            bpy.ops.outliner.orphans_purge(do_recursive=True)

    # Undo source tools' specific rotation
    if not preclean:
        step4(True)

    # Go back to the control rig
    bpy.data.objects[CONTROLRIG_NAME].hide_set(False)
    bpy.data.objects[CONTROLRIG_NAME].select_set(True)
    bpy.data.objects[ARMATURE_NAME].select_set(False)
    bpy.data.objects[ARMATURE_NAME].hide_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Control Rig"]


if __name__ == "__main__":
    cleanup_bake(
        True
    )  # cleanup issues that could have come from failed previous executions
    step1()  # select armature
    step2()  # select bones in pose mode
    step3()  # new action & bake animation
    step4()  # object mode and export prep
    step5()  # export animation
    cleanup_bake()  # cleanup to allow multiple runs without ... wierdness
