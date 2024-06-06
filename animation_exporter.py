import bpy
import os
from math import radians
from bpy.types import Operator

ARMATURE = 0
CONTROL_RIG = 1


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

    # Gets an object to a desired selected & hidden state
    def select(self, obj, selected, hidden):
        obj.hide_set(False)
        obj.select_set(selected)
        obj.hide_set(hidden)

    @classmethod
    def poll(self, context):
        settings = context.scene.export_helper_settings

        # Execution Checks
        if settings.armature() == None:
            # print("No Armature")
            return False
        if settings.export_path == None:
            # print("No Export Path")
            return False
        if not any(settings.action_collection):
            # print("No Selected Actions")
            return False

        return True

    def save_actions(self, action_name):
        action = bpy.data.actions.get(action_name)
        if action == None:
            self.error("Could not find action: " + action_name)
        # Prevent garbage collection from nuking the action
        action.use_fake_user = True

    def execute(self, context):
        settings = context.scene.export_helper_settings

        setting_frame_before_start = settings.frame_start
        setting_frame_before_end = settings.frame_end

        # Setup frame start and frame end
        if settings.frame_start == None or settings.frame_start == 0:
            settings.frame_start = bpy.context.scene.frame_start

        if settings.frame_end == None or settings.frame_end == 0:
            settings.frame_end = bpy.context.scene.frame_end

        # Attempt to process each of the rig's selected actions

        actions = settings.action_collection

        if any(actions):
            self.log("Export Helper Started with " + str(len(actions)) + " actions")
            # protect from garbage collection
            for prop in actions:
                if prop.checked and not prop.name in (None, ""):
                    self.save_actions(prop.name)
            # do the work
            for prop in actions:
                if prop.checked and not prop.name in (None, ""):
                    self.process(settings, prop.name)
                    # clean out animation bakes to avoid name collisions
                    bpy.ops.outliner.orphans_purge(do_recursive=True)
            # select first action after exporting
            # self.select_action(settings, actions[0].name)
            self.log("Export Helper Finished")

            # this is probably not needed
            arm = context.scene.export_helper_settings.armature()
            rig = context.scene.export_helper_settings.control_rig()

            if rig is not None:
                self.select(arm, False, True)
                self.select(rig, True, False)
                bpy.context.view_layer.objects.active = rig
            else:
                self.select(arm, True, False)
                bpy.context.view_layer.objects.active = arm
            settings.frame_start = setting_frame_before_start
            settings.frame_end = setting_frame_before_end
            return {"FINISHED"}
        else:
            settings.frame_start = setting_frame_before_start
            settings.frame_end = setting_frame_before_end
            return {"CANCELLED"}

    def select_action(self, settings, action_name, control_pair):
        # Select the current action from the rig
        action = bpy.data.actions.get(action_name)
        if action == None:
            self.error("Could not find action: " + action_name)

        if control_pair[CONTROL_RIG] is None:
            control_pair[ARMATURE].animation_data.action = action
        else:
            control_pair[CONTROL_RIG].animation_data.action = action

    def process(self, settings, action):
        self.log("Start Processing for " + action)

        pair_list = list(
            zip(
                list(map(lambda x: x.armature, settings.armature_collection)),
                list(map(lambda x: x.control_rig, settings.control_rig_collection)),
            )
        )

        pair_list = list(filter(lambda x: x[ARMATURE] is not None, pair_list))

        # some steps must be ran for each rig/armature pair, others run on all at once with selections
        # data fmt: (armature, control_rig)
        for pair in pair_list:
            print("Processing control_pair ")
            print(pair)
            # cleanup issues that could have come from failed previous executions
            self.cleanup_bake(settings, pair)
            self.select_action(settings, action, pair)

            # select armature
            self.step1(settings, pair)
            # select all the bones in pose mode
            self.step2(settings)
            # new action & bake animation
            self.step3(settings, pair)

        # object mode and export prep
        self.step4()
        # export animation
        self.step5(settings)
        # undo "prep" rotation
        self.step4()

        # cleanup to allow multiple runs without ... wierdness
        for pair in pair_list:
            self.cleanup_bake(settings, pair)

        self.log("Finished Processing for " + action)

    def step1(self, settings, control_pair):
        try:
            bpy.ops.object.mode_set(mode="OBJECT")
        except:
            pass

        bpy.context.scene.frame_current = 0

        bpy.ops.object.select_all(action="DESELECT")

        if control_pair[CONTROL_RIG] is not None:
            self.select(control_pair[CONTROL_RIG], False, True)
        self.select(control_pair[ARMATURE], True, False)

        bpy.context.view_layer.objects.active = control_pair[ARMATURE]

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

    def step3(self, settings, control_pair):
        action_source = (
            control_pair[CONTROL_RIG]
            if control_pair[CONTROL_RIG] is not None
            else control_pair[ARMATURE]
        )

        # Setup the baked action
        control_action = action_source.animation_data.action
        if control_action == None:
            self.error("Step 3: Could not find Rig Animation Action")

        # Decide to manually bake or allow the better fbx addon to take over
        if settings.export_method == "betterfbx":
            control_pair[ARMATURE].animation_data.action = control_action
            return

        # Prefix is added globally to prevent action name overlapping
        # same goes for the object we are baking this action to
        bake_action_name = (
            settings.GLOBAL_EXPORT_PREFIX
            + settings.action_prefix
            + control_action.name.replace("|", " ").replace("/", "-")
            + settings.action_suffix
            # + "_"
            # + action_source.name # allow bakes to be all put into the same action
        )

        bake_action = bpy.data.actions.get(bake_action_name)
        print("About to bake action: " + bake_action_name)

        if bake_action == None:
            area_before = bpy.context.area.type

            bpy.context.area.type = "DOPESHEET_EDITOR"
            bpy.context.space_data.mode = "ACTION"
            control_pair[ARMATURE].animation_data_clear()  # can crash without this
            control_pair[ARMATURE].animation_data_create()  # can crash without this

            new_action = bpy.data.actions.new("DeleteMePlease")

            if new_action == None:
                self.error("Step 3: There was an issue creation an action to bake to")

            control_pair[ARMATURE].animation_data.action = new_action
            new_action.name = bake_action_name

            bpy.context.area.type = area_before
        else:
            control_pair[ARMATURE].animation_data.action = bake_action

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

        self.log("Finished baking animation to action: " + bake_action_name)

    def step4(self):
        # settings = bpy.context.scene.export_helper_settings
        try:
            bpy.ops.object.mode_set(mode="OBJECT")
        except:
            pass

    def native_fbx_export(self, settings, file):
        # Merge armatures for single take in fbx file
        bpy.ops.object.duplicate()
        bpy.ops.object.join()

        tmp = bpy.context.view_layer.objects.active
        bpy.ops.object.select_all(action="DESELECT")
        tmp.name = " "
        bpy.context.view_layer.objects.active = tmp
        self.select(tmp, True, False)

        bpy.ops.export_scene.fbx(
            path_mode="AUTO",
            filepath=file,
            check_existing=False,
            use_selection=True,
            # use_visible=True,
            global_scale=settings.scale,
            apply_unit_scale=True,
            object_types={"ARMATURE"},
            add_leaf_bones=False,
            bake_anim=True,
            bake_anim_use_all_bones=True,
            bake_anim_use_all_actions=False,
            bake_anim_use_nla_strips=False,
        )

        bpy.ops.object.delete()

    def better_fbx_export(self, settings, file):
        frame_before_start = bpy.context.scene.frame_start
        frame_before_end = bpy.context.scene.frame_end

        bpy.context.scene.frame_start = settings.frame_start
        bpy.context.scene.frame_end = settings.frame_end

        bpy.ops.better_export.fbx(
            filepath=file,
            check_existing=False,
            my_file_type=".fbx",
            my_fbx_unit=settings.scale_unit,
            use_selection=True,
            use_animation=True,
            use_timeline_range=True,
            my_scale=settings.scale,
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

        bpy.context.scene.frame_start = frame_before_start
        bpy.context.scene.frame_end = frame_before_end

    def step5(
        self,
        settings,
    ):
        output_dir = settings.export_path

        action_name = (
            settings.armature()
            .animation_data.action.name.replace(" ", "")
            .replace(settings.GLOBAL_EXPORT_PREFIX, "")
        )
        fbx_file_name = action_name + ".fbx"
        target_file = bpy.path.abspath(output_dir + fbx_file_name)

        method = settings.export_method

        # have multiple items selected for export process
        for cr in settings.control_rig_collection:
            if cr.control_rig is not None:
                self.select(cr.control_rig, False, True)

        for o in settings.armature_collection:
            if o.armature is not None:
                self.select(o.armature, True, False)

        if method == "internal":
            self.native_fbx_export(settings, target_file)
        elif method == "betterfbx":
            self.better_fbx_export(settings, target_file)

    def cleanup_bake(self, settings, control_pair):
        arm = control_pair[ARMATURE]
        rig = control_pair[CONTROL_RIG]

        arm.animation_data_create()  # can crash without this

        if settings.export_method == "betterfbx":
            arm.animation_data.action = None
        else:
            # Clear out animation bake
            action = arm.animation_data.action

            if action is not None and action.name.startswith(
                settings.GLOBAL_EXPORT_PREFIX
            ):
                bpy.data.actions.remove(action, do_unlink=True)

        # Go back to the rig
        if rig is not None:
            self.select(arm, False, True)
            self.select(rig, True, False)
            bpy.context.view_layer.objects.active = rig
        else:
            self.select(arm, True, False)
            bpy.context.view_layer.objects.active = arm
