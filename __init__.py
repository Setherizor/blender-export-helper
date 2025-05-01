# How To
# https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html

# Panel How To
# https://blender.stackexchange.com/questions/57306/how-to-create-a-custom-ui

bl_info = {
    "name": "Blender Export Helper",
    "author": "setherizor",
    "version": (0, 8, 2),
    "blender": (4, 4, 0),
    "location": "File > Import-Export",
    "description": "Simplify exporting your work with popular tools",
    "warning": "",
    "wiki_url": "",
    "category": "Animation",
}

import bpy
from bpy.app.handlers import persistent, load_post
from bpy.types import Panel, PropertyGroup, Operator
from bpy.props import (
    StringProperty,
    IntProperty,
    FloatProperty,
    BoolProperty,
    PointerProperty,
    EnumProperty,
    CollectionProperty,
)

from .animation_exporter import ExportHelper
from bpy.utils import register_class, unregister_class

default_opts = {"ANIMATABLE"}


def has_rig_animdata(settings):
    if settings is None:
        return False

    control_anims = (
        settings.control_rig() is not None
        and settings.control_rig().animation_data is not None
    )
    armature_anims = (
        settings.armature() is not None
        and settings.armature().animation_data is not None
    )

    return control_anims or armature_anims


def has_bones_and_no_dupes(self, object):
    settings = bpy.context.scene.export_helper_settings
    try:
        hasBones = any(object.data.bones)
        inArms = object in list(map(lambda x: x.armature, settings.armature_collection))
        # inControls = object in list(
        #     map(lambda x: x.control_rig, settings.control_rig_collection)
        # )
        # allow 1 rig to 2 armatures
        return hasBones and not inArms  # and not inControls
    except:
        return False


@persistent
def add_collection_opts(_=None, __=None):
    try:
        load_post.remove(add_collection_opts)
    except:
        pass
    bpy.ops.export_helper_collections.get()


class ArmatureCollection(bpy.types.PropertyGroup):
    armature: PointerProperty(
        type=bpy.types.Object,
        name="Armature",
        options=default_opts,
        poll=has_bones_and_no_dupes,
        update=lambda self, context: add_collection_opts(),
    )


class ControlRigCollection(bpy.types.PropertyGroup):
    control_rig: PointerProperty(
        type=bpy.types.Object,
        name="Control Rig",
        options=default_opts,
        poll=has_bones_and_no_dupes,
        update=lambda self, context: add_collection_opts(),
    )


class SelectionCollectionTracker(Operator):
    bl_idname = "export_helper_collections.get"
    bl_description = "Add Armature & Control Rig Option"
    bl_label = "Add More Options"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = context.scene.export_helper_settings
        a = settings.armature_collection

        # Delete spare slots
        for i, pair in enumerate(
            list(zip(settings.armature_collection, settings.control_rig_collection))
        ):
            if pair[0].armature == None:
                settings.armature_collection.remove(i)
                settings.control_rig_collection.remove(i)

        # add back in one
        count = 0
        for prop in a:
            if prop.armature != None:
                count += 1

        if count == len(a):
            settings.control_rig_collection.add()
            settings.armature_collection.add()

        return {"FINISHED"}


class PropertyCollection(bpy.types.PropertyGroup):
    name: StringProperty(name="", default="")
    checked: BoolProperty(
        name="",
        default=True,
        update=lambda self, context: self.select_action(context),
    )
    fps: IntProperty(name="", default=0)

    def select_action(self, context):
        pass
        # settings = context.scene.export_helper_settings

        # Disallow multiple actions selection
        # x = 0
        # for prop in settings.action_collection:
        #     if prop.checked:
        #         x = x + 1
        #         if x > 1:
        #             print("Cannot select " + self.name + " because of export method")
        #             self.checked = False


class HelperProperties(PropertyGroup):
    armature_collection: CollectionProperty(
        type=ArmatureCollection, options=default_opts
    )
    control_rig_collection: CollectionProperty(
        type=ControlRigCollection, options=default_opts
    )

    def armature(self, idx=0):
        try:
            return self.armature_collection[idx].armature
        except:
            # print("Problem fetching armature")
            return None

    def control_rig(self, idx=0):
        try:
            return self.control_rig_collection[idx].control_rig
        except:
            # print("Problem fetching control rig")
            return None

    # Export Settings
    GLOBAL_EXPORT_PREFIX = "Output_"
    scale: FloatProperty(
        name="Export Scale",
        default=1.0,
        min=0,
        soft_max=100,
        subtype="UNSIGNED",
        options=default_opts,
    )

    native_fbx_axis_forward: EnumProperty(
        name="Native FBX Axis Forward",
        description="Native FBX Axis Forward",
        items=(
            ("X", "X Forward", "X Forward"),
            ("Y", "Y Forward", "Y Forward"),
            ("Z", "Z Forward", "Z Forward"),
            ("-X", "-X Forward", "-X Forward"),
            ("-Y", "-Y Forward", "-Y Forward"),
            ("-Z", "-Z Forward", "-Z Forward"),
        ),
        default="-Z",
    )

    native_fbx_axis_up: EnumProperty(
        name="Native FBX Axis Up",
        description="Native FBX Axis Up",
        items=(
            ("X", "X Up", "X Up"),
            ("Y", "Y Up", "Y Up"),
            ("Z", "Z Up", "Z Up"),
            ("-X", "-X Up", "-X Up"),
            ("-Y", "-Y Up", "-Y Up"),
            ("-Z", "-Z Up", "-Z Up"),
        ),
        default="Y",
    )

    # taken from better FBX
    scale_unit: EnumProperty(
        name="Scale Unit",
        description="Scale Unit",
        items=(
            ("mm", "Millimeter", "Millimeter"),
            ("dm", "Decimeter", "Decimeter"),
            ("cm", "Centimeter", "Centimeter"),
            ("m", "Meter", "Meter"),
            ("km", "Kilometer", "Kilometer"),
            ("Inch", "Inch", "Inch"),
            ("Foot", "Foot", "Foot"),
            ("Mile", "Mile", "Mile"),
            ("Yard", "Yard", "Yard"),
        ),
        default="m",
    )

    better_fbx_axis: EnumProperty(
        name="Better FBX Axis",
        description="Better FBX Axis",
        items=(
            ("MayaZUp", "MayaZUp", "Compatible with Maya"),
            ("OpenGL", "OpenGL", "Compatible with OpenGL"),
            (
                "Unity",
                "Unity",
                "Rotate all contents 180 degrees around the vertical axis, let the character face you in Unity Editor. Warning: This pose is not compatible with the 'Humanoid' animation type, if you want to use the 'Humanoid' animation type in Unity Editor, please use 'MayaZUp' or 'OpenGL'",
            ),
            (
                "Unreal1",
                "Unreal1",
                "Rotate all contents -90 degrees around the vertical axis, let the character face you in Unreal Editor",
            ),
            (
                "Unreal2",
                "Unreal2",
                "Rotate all contents 90 degrees around the vertical axis, let the character turn his back on you in Unreal Editor",
            ),
        ),
        default="MayaZUp",
    )

    my_primary_bone_axis: EnumProperty(
        name="Primary Bone Axis",
        description="Primary Bone Axis",
        items=(
            ("X", "X Axis", "X Axis"),
            ("Y", "Y Axis", "Y Axis"),
            ("Z", "Z Axis", "Z Axis"),
            ("-X", "-X Axis", "-X Axis"),
            ("-Y", "-Y Axis", "-Y Axis"),
            ("-Z", "-Z Axis", "-Z Axis"),
        ),
        default="Y",
    )

    my_secondary_bone_axis: EnumProperty(
        name="Secondary Bone Axis",
        description="Secondary Bone Axis",
        items=(
            ("X", "X Axis", "X"),
            ("Y", "Y Axis", "Y"),
            ("Z", "Z Axis", "Z"),
            ("-X", "-X Axis", "-X"),
            ("-Y", "-Y Axis", "-Y"),
            ("-Z", "-Z Axis", "-Z"),
        ),
        default="X",
    )

    only_deform_bones: BoolProperty(
        name="Only Deform Bones",
        default=False,
        options=default_opts,
    )

    make_rigify_armature: BoolProperty(
        name="Make Game-Friendly Rigify Armature",
        default=False,
        options=default_opts,
    )

    keep_rigify_root_bone: BoolProperty(
        name="Keep Rigify Root Bone",
        default=True,
        options=default_opts,
    )

    export_path: StringProperty(
        name="Export Path",
        default="//",
        # maxlen=1024,
        subtype="DIR_PATH",
        options={"OUTPUT_PATH"},
    )

    export_method: EnumProperty(
        name="Export Method",
        description="What library to export your animation(s) with",
        items=(
            (
                "internal",
                "Internal FBX Exporter",
                "Use Blender's build in FBX exporter",
            ),
            ("betterfbx", "Better FBX Addon", "Use Better FBX Import & Export Addon") if "better_fbx" in bpy.context.preferences.addons.keys() else None,
        ),
        default="internal",
        options=default_opts,
    )

    export_use_asset_actions: BoolProperty(
        name="Enable Exporting Assets",
        default=True,
        options=default_opts,
    )

    action_prefix: StringProperty(name="Action Prefix", options=default_opts)
    action_suffix: StringProperty(name="Action Suffix", options=default_opts)

    action_collection: CollectionProperty(type=PropertyCollection, options=default_opts)

    def update_actions(self, context):
        settings = context.scene.export_helper_settings

        if has_rig_animdata(settings):
            opts = []

            for a in bpy.data.actions:
                get_assets = settings.export_use_asset_actions or a.asset_data == None
                if get_assets and not a.name.startswith(settings.GLOBAL_EXPORT_PREFIX):
                    opts.append(a.name)

            opts.sort()

            settings.action_collection.clear()
            for i in opts:
                item = settings.action_collection.add()
                item.name = i
                item.checked = False
                item.fps = 0


class ActionTracker(Operator):
    bl_idname = "export_helper_actions.get"
    bl_description = "Get Rig Actions"
    bl_label = "Action Tracker"
    bl_options = {"REGISTER"}

    def execute(self, context):
        HelperProperties.update_actions(self, context)
        return {"FINISHED"}


class ActionPanel(Panel):
    bl_idname = "HELPER_PT_ExportHelperActionPanel"
    bl_label = "Action Options (& FPS Override)"
    bl_description = "Select Actions for Export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Export Helper"
    use_pin = True

    @classmethod
    def poll(self, context):
        settings = context.scene.export_helper_settings
        return has_rig_animdata(settings)

    def draw(self, context):
        layout = self.layout
        settings = context.scene.export_helper_settings

        for prop in settings.action_collection:
            row = layout.row()
            row.prop(prop, "checked", text=prop["name"])
            c = row.column(align=True)
            c.alignment = "RIGHT"
            c.prop(prop, "fps", expand=False)


class ExportButton(Panel):
    bl_idname = "HELPER_PT_ExportHelperExportButton"
    bl_label = "Export"
    bl_description = "Export selected actions"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Export Helper"
    use_pin = True

    @classmethod
    def poll(self, context):
        settings = context.scene.export_helper_settings
        return has_rig_animdata(settings)

    def draw(self, context):
        layout = self.layout
        settings = context.scene.export_helper_settings

        row = layout.row(align=True)

        row.operator(ActionTracker.bl_idname, text="Get Options")
        row.operator(ExportHelper.bl_idname, text="Export")


# Handles UI for most of the settings
class ExportHelperSetupPanel(Panel):
    bl_idname = "HELPER_PT_ExportHelperSetupPanel"
    bl_label = "Export Helper"
    bl_description = "Helpful Exporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Export Helper"
    use_pin = True

    # How To
    # https://docs.blender.org/api/current/bpy.types.UILayout.html
    def draw(self, context):
        layout = self.layout
        settings = context.scene.export_helper_settings

        col = layout.column(align=True)

        col.label(text="Select Armature(s) & Control Rig(s)")

        row = layout.row(align=True)
        rowcol = row.column(align=True)
        rowcol.label(text="Armature(s)")
        for prop in settings.armature_collection:
            rowcol.prop(prop, "armature", icon_only=True)

        rowcol = row.column(align=True)
        rowcol.label(text="Control Rig(s)")
        for prop in settings.control_rig_collection:
            rowcol.prop(prop, "control_rig", icon_only=True)

        col.operator(SelectionCollectionTracker.bl_idname, text="Setup Selections")
        col.separator()

        col = layout.column(align=True)
        col.label(text="Setup Export Settings")
        row = layout.row(align=True)

        rowcol = row.column(align=True)
        rowcol.label(text="Action Prefix")
        rowcol.prop(settings, "action_prefix", icon_only=True)

        rowcol = row.column(align=True)
        rowcol.label(text="Action Suffix")
        rowcol.prop(settings, "action_suffix", icon_only=True)

        col = layout.column(align=True)
        col.label(text="Export Method:")
        col.prop(settings, "export_method", icon_only=False, expand=True)
        col.prop(settings, "export_path", icon_only=False, expand=True)

        col.prop(settings, "scale", icon_only=False, expand=True)
        if settings.export_method == "internal":
            col.prop(settings, "native_fbx_axis_forward")
            col.prop(settings, "native_fbx_axis_up")
        if settings.export_method == "betterfbx":
            col.prop(settings, "scale_unit", icon_only=False, expand=False)
            col.prop(settings, "better_fbx_axis")
        col.prop(settings, "my_primary_bone_axis", icon_only=False, expand=False)
        col.prop(settings, "my_secondary_bone_axis", icon_only=False, expand=False)
        col.prop(settings, "only_deform_bones")
        if settings.export_method == "betterfbx":
            col.prop(settings, "make_rigify_armature")
            col.prop(settings, "keep_rigify_root_bone")
        col.prop(settings, "export_use_asset_actions")


# Registration
classes = (
    ArmatureCollection,
    ControlRigCollection,
    PropertyCollection,
    HelperProperties,
    SelectionCollectionTracker,
    ActionTracker,
    ExportHelper,
    ExportHelperSetupPanel,
    ActionPanel,
    ExportButton,
)


def register():
    for cls in classes:
        try:
            register_class(cls)
        except:
            print("COULD NOT REGISTER CLASS")
            print(cls)

    bpy.types.Scene.export_helper_settings = PointerProperty(type=HelperProperties)
    load_post.append(add_collection_opts)  # TODO: this doesn't work...


def unregister():
    for cls in classes:
        unregister_class(cls)

    del bpy.types.Scene.export_helper_settings


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.

# F3 -> Reload Scripts
if __name__ == "__main__":
    register()
