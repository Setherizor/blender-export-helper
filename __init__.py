# How To
# https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html

# Panel How To
# https://blender.stackexchange.com/questions/57306/how-to-create-a-custom-ui

bl_info = {
    "name": "Blender Export Helper",
    "author": "setherizor",
    "version": (0, 5, 0),
    "blender": (3, 4, 1),
    "location": "File > Import-Export",
    "description": "Simplify exporting your work with popular tools",
    "warning": "",
    "wiki_url": "",
    "category": "Animation",
}

import bpy
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
    return not (
        settings == None
        or settings.control_rig == None
        or settings.control_rig.animation_data == None
    )


def has_bones(self, object):
    try:
        return any(object.data.bones)
    except:
        return False


class PropertyCollection(bpy.types.PropertyGroup):
    name: StringProperty(name="", default="")
    checked: BoolProperty(
        name="",
        default=True,
        update=lambda self, context: self.select_action(context),
    )

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
    armature: PointerProperty(
        type=bpy.types.Object, name="Armature", options=default_opts, poll=has_bones
    )
    control_rig: PointerProperty(
        type=bpy.types.Object,
        name="Control Rig",
        options=default_opts,
        update=lambda self, context: self.update_actions(context),
        poll=has_bones,
    )
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
    # taken from better FBX
    scale_unit: EnumProperty(
        name="Scale Unit",
        description="Scale Unit",
        items=(
            ("mm", "mm", "mm"),
            ("dm", "dm", "dm"),
            ("cm", "cm", "cm"),
            ("m", "m", "m"),
            ("km", "km", "km"),
            ("Inch", "Inch", "Inch"),
            ("Foot", "Foot", "Foot"),
            ("Mile", "Mile", "Mile"),
            ("Yard", "Yard", "Yard"),
        ),
        default="m",
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
            ("betterfbx", "Better FBX Addon", "Use Better FBX Import & Export Addon"),
        ),
        default="internal",
        options=default_opts,
        update=lambda self, context: self.update_export_method(context),
    )
    export_use_asset_actions: BoolProperty(
        name="Enable Exporting Assets",
        default=True,
        options=default_opts,
        update=lambda self, context: self.update_actions(context),
    )

    action_prefix: StringProperty(name="Action Prefix", options=default_opts)
    action_suffix: StringProperty(name="Action Suffix", options=default_opts)

    frame_start: IntProperty(name="Override Start Frame", options=default_opts)
    frame_end: IntProperty(name="Override End Frame", options=default_opts)

    action_collection: CollectionProperty(type=PropertyCollection, options=default_opts)

    def update_export_method(self, context):
        pass
        # settings = context.scene.export_helper_settings

    def update_actions(self, context):
        settings = context.scene.export_helper_settings

        if has_rig_animdata(settings):
            opts = []

            ad = settings.control_rig.animation_data

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


class ActionTracker(Operator):
    bl_idname = "export_helper_actions.get"
    bl_description = "Get Control Rig Actions"
    bl_label = "Action Tracker"
    bl_options = {"REGISTER"}

    def execute(self, context):
        HelperProperties.update_actions(self, context)
        return {"FINISHED"}


class ActionPanel(Panel):
    bl_idname = "HELPER_PT_ExportHelperActionPanel"
    bl_label = "Control Rig Actions For Export"
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
            layout.prop(prop, "checked", text=prop["name"])

        layout.separator()

        row = layout.row(align=True)

        row.operator(ActionTracker.bl_idname, text="Get Options")
        row.operator(ExportHelper.bl_idname, text="Export")


# Handles UI for most of the settings
class ExportHelperSetupPanel(Panel):
    bl_idname = "HELPER_PT_ExportHelperSetupPanel"
    bl_label = "Awesome Exporter"
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

        col.label(text="Select Armature & Control Rig")

        row = layout.row(align=True)
        rowcol = row.column(align=True)
        rowcol.label(text="Armature Object")
        rowcol.prop(settings, "armature", icon_only=True)

        rowcol = row.column(align=True)
        rowcol.label(text="Control Rig Object")
        rowcol.prop(settings, "control_rig", icon_only=True)

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

        row = layout.row(align=True)

        rowcol = row.column(align=True)
        rowcol.label(text="Bake Frame Start")
        rowcol.prop(settings, "frame_start", icon_only=True)

        rowcol = row.column(align=True)
        rowcol.label(text="Bake Frame End")
        rowcol.prop(settings, "frame_end", icon_only=True)

        col = layout.column(align=True)
        col.label(text="Export Method")
        col.prop(settings, "export_method", icon_only=False, expand=True)
        col.prop(settings, "export_path", icon_only=False, expand=True)

        col.prop(settings, "scale", icon_only=False, expand=True)
        col.prop(settings, "export_use_asset_actions")

        if settings.export_method == "betterfbx":
            col.prop(settings, "scale_unit", icon_only=False, expand=False)


# Registration
classes = (
    PropertyCollection,
    HelperProperties,
    ActionTracker,
    ExportHelper,
    ExportHelperSetupPanel,
    ActionPanel,
)


def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.export_helper_settings = PointerProperty(type=HelperProperties)


def unregister():
    del bpy.types.Scene.export_helper_settings

    for cls in classes:
        unregister_class(cls)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.

# F3 -> Reload Scripts
if __name__ == "__main__":
    register()
