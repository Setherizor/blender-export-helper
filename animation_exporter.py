# S&Box Citizen's Blender Animation Exporter
# @Author Setherizor
# @LastUpdated <deploy-type>
# @LastUpdated <deploy-date>

# bpy.ops.export_helper.fbx()

# Warning: This export script will replace the exported files when ran. This could be descructive if you have colliding filenames.
# To understand what this script does, reference the following document and start reading from the bottom of the code here
# https://github.com/Ali3nSystems/Blender-Control-Rig-for-Terry/blob/main/Documentation/B.%20Poses%2C%20Animations%20and%20Shape%20Keys/c.%20Exporting%20Poses%20and%20Animations.pdf

# If you run into issues, you may need to clear out your "Unused Data Blocks" in the "File > Clean Up" Menu.

import bpy
import os
from math import radians
from bpy.types import Operator

GLOBAL_EXPORT_PREFIX = "Output_"


class ExportHelper(Operator):
    bl_idname = "export_helper.fbx"
    bl_description = "Export animation(s)"
    bl_label = "Export Helper"
    bl_options = {"REGISTER", "UNDO"}

    def log(self, message):
        self.report({"INFO"}, message)
        # print(message)

    def error(self, message):
        self.report({"WARNING"}, "Something isn't right: " + message)
        raise Exception(message)

    @classmethod
    def poll(self, context):
        settings = context.scene.export_helper_settings

        # Execution Checks
        if settings.armature == None:
            print("No Armature")
            return False
        if settings.control_rig == None:
            print("No Rig")
            return False
        if settings.export_path == None:
            print("No Export Path")
            return False
        if not any(settings.action_collection):
            print("No Selected Actions")
            return False

        return True

    def execute(self, context):
        settings = context.scene.export_helper_settings

        # Setup frame start and frame end
        if settings.frame_start == None or settings.frame_start == 0:
            settings.frame_start = bpy.context.scene.frame_start

        if settings.frame_end == None or settings.frame_end == 0:
            settings.frame_end = bpy.context.scene.frame_end

        # Attempt to process each of the control rig's selected actions

        settings = context.scene.export_helper_settings
        actions = settings.action_collection

        if any(actions):
            self.log("Export Helper Started")
            for prop in actions:
                if prop.checked and not prop.name in (None, ""):
                    self.process(settings, prop.name)
            # select first action after exporting
            # self.select_action(settings, actions[0].name)
            self.log("Export Helper Finished")

            settings.armature.select_set(False)
            settings.armature.hide_set(True)

            settings.control_rig.hide_set(False)
            settings.control_rig.select_set(True)

            return {"FINISHED"}
        else:
            return {"CANCELLED"}

    def select_action(self, settings, action_name):
        # Select the current action from the control rig
        action = bpy.data.actions.get(action_name)
        if action == None:
            self.error("Could not find action: " + action_name)

        settings.control_rig.animation_data.action = action

    def process(self, settings, action):
        self.log("Start Processing for " + action)

        self.select_action(settings, action)

        # cleanup issues that could have come from failed previous executions
        self.cleanup_bake(settings, True)
        # select armature
        self.step1(settings)
        # select bones in pose mode
        self.step2(settings)
        # new action & bake animation
        self.step3(settings)
        # object mode and export prep
        self.step4(settings)
        # export animation
        self.step5(settings)
        # cleanup to allow multiple runs without ... wierdness
        self.cleanup_bake(settings, False)

        self.log("Finished Processing for " + action)

    def step1(
        self,
        settings,
    ):
        try:
            bpy.ops.object.mode_set(mode="OBJECT")
        except:
            pass

        bpy.context.scene.frame_current = 0

        bpy.ops.object.select_all(action="DESELECT")

        settings.control_rig.select_set(False)
        settings.control_rig.hide_set(True)
        settings.armature.hide_set(False)
        settings.armature.select_set(True)
        bpy.context.view_layer.objects.active = settings.armature

    def step2(
        self,
        settings,
    ):
        try:
            status = bpy.ops.object.mode_set(mode="POSE")
            if not status == {"FINISHED"}:
                self.error("Step 2: could not get into pose mode")
        except:
            self.error("Step 2: something went wrong with posemode")

        bpy.ops.pose.select_all(action="SELECT")

    def step3(
        self,
        settings,
    ):
        control_action = settings.control_rig.animation_data.action
        if control_action == None:
            self.error("Step 3: Could not find Control Rig Animation Action")

        # Decide to manually bake or allow the better fbx addon to take over
        if settings.export_method == "betterfbx":
            settings.armature.animation_data.action = control_action
            return

        # Setup the new action
        control_action = settings.control_rig.animation_data.action

        if control_action == None:
            self.error("Step3: Could not get control rig action")

        # Prefix is added globally to prevent action name overlapping
        bake_action_name = (
            GLOBAL_EXPORT_PREFIX
            + settings.action_prefix
            + control_action.name
            + settings.action_suffix
        )

        bake_action = bpy.data.actions.get(bake_action_name)

        if bake_action == None:
            area_before = bpy.context.area.type

            bpy.context.area.type = "DOPESHEET_EDITOR"
            bpy.context.space_data.mode = "ACTION"
            settings.armature.animation_data_create()  # can crash without this
            bpy.ops.action.new()

            new_action = bpy.data.actions.get("Action")
            settings.armature.animation_data.action = new_action
            new_action.name = bake_action_name

            bpy.context.area.type = area_before

        # Bake
        bpy.ops.nla.bake(
            frame_start=settings.frame_start,
            frame_end=settings.frame_end,
            step=1,
            only_selected=True,
            visual_keying=True,
            clear_constraints=False,  # VERY IMPORTANT FOR BACK TO BACK EXPORTS
            use_current_action=True,
            bake_types={"POSE"},
        )

        self.log("Finished baking animation to armature")

    def step4(self, settings, undo=False):
        try:
            bpy.ops.object.mode_set(mode="OBJECT")
        except:
            pass

        if (
            settings.export_method == "sourcetools"
            and settings.export_fix_forward_axis == True
        ):
            settings.control_rig.hide_set(False)
            settings.control_rig.select_set(True)
            angle = 90 if undo else -90
            angle = radians(angle)
            bpy.ops.transform.rotate(value=angle, orient_axis="Z")
            settings.control_rig.select_set(False)
            settings.control_rig.hide_set(True)

    def native_fbx_export(self, settings, file):
        bpy.ops.export_scene.fbx(
            path_mode="AUTO",
            filepath=file,
            check_existing=False,
            use_selection=True,
            global_scale=1.0,
            apply_unit_scale=True,
            add_leaf_bones=False,
            bake_anim=True,
            bake_anim_use_all_bones=True,
        )

    def better_fbx_export(self, settings, file):
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

        filename = (
            settings.armature.animation_data.action.name.replace(" ", "") + ".fbx"
        )

        try:
            os.remove(GLOBAL_EXPORT_PREFIX + filename)
        except:
            pass

        os.rename(filename, GLOBAL_EXPORT_PREFIX + filename)

    def source_tools_export(self, settings, file):
        collection = settings.armature.users_collection[0]

        if settings.export_fix_forward_axis == True:
            bpy.context.scene.vs.export_path = settings.export_path
            bpy.context.scene.vs.dmx_encoding = "9"
            bpy.context.scene.vs.dmx_format = "22_modeldoc"

        try:
            os.remove(file.replace(".fbx", ".dmx"))
        except:
            self.log("Something odd happened with dmx file removal")

        try:
            os.remove(collection.name + ".dmx")
        except:
            self.log("Something odd happened with dmx collection removal")

        try:
            bpy.ops.export_scene.smd(collection=collection.name, export_scene=False)
        except:
            self.log("Something odd happened with dmx export")
        try:
            os.rename(collection.name + ".dmx", file.replace(".fbx", ".dmx"))
        except:
            self.log("Something odd happened with dmx export rename")

    def step5(
        self,
        settings,
    ):
        # TODO: name output files based on action
        output_dir = settings.export_path

        action_name = settings.armature.animation_data.action.name.replace(" ", "")
        fbx_file_name = action_name + ".fbx"
        target_file = bpy.path.abspath(output_dir + fbx_file_name)

        method = settings.export_method

        if method == "internal":
            self.native_fbx_export(settings, target_file)
        elif method == "betterfbx":
            self.better_fbx_export(settings, target_file)
        elif method == "sourcetools":
            self.source_tools_export(settings, target_file)

    def cleanup_bake(self, settings, preclean=False):
        arm = bpy.context.scene.export_helper_settings.armature
        rig = bpy.context.scene.export_helper_settings.armature

        arm.animation_data_create()  # can crash without this

        if settings.export_method == "betterfbx":
            arm.animation_data.action = None
        else:
            # Clear out animation bake
            action = arm.animation_data.action

            if not action == None:
                action.user_clear()
                bpy.ops.outliner.orphans_purge(do_recursive=True)

        # Undo source tools' specific rotation
        if not preclean:
            self.step4(settings, True)

        # Go back to the rig
        rig.hide_set(False)
        rig.select_set(True)
        arm.select_set(False)
        arm.hide_set(True)
        bpy.context.view_layer.objects.active = rig
