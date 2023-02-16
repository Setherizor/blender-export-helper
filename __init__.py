# How To
# https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html

# Panel How To
# https://blender.stackexchange.com/questions/57306/how-to-create-a-custom-ui

bl_info = {
    "name": "Blender Export Helper",
    "author": "setherizor",
    "version": (0, 0, 0),
    "blender": (3, 4, 1),
    "location": "File > Import-Export",
    "description": "Simplify exporting your work with popular tools",
    "warning": "",
    "wiki_url": "",
    "category": "Animation",
}

import bpy
from bpy.types import Panel, PropertyGroup
from bpy.props import (
    StringProperty,
    IntProperty,
    BoolProperty,
    PointerProperty,
    EnumProperty,
)

default_opts = {"ANIMATABLE"}


class HelperProperties(PropertyGroup):
    # Control Settings
    armature: PointerProperty(
        type=bpy.types.Object, name="Armature", options=default_opts
    )
    control_rig: PointerProperty(
        type=bpy.types.Object, name="Control Rig", options=default_opts
    )
    # Export Settings
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
            ("sourcetools", "Source Tools", "Use Valve's Source Tools Addon"),
        ),
        default="internal",
        options=default_opts,
    )
    export_fix_forward_axis: BoolProperty(
        name="Fix Forward Axis", default=True, options=default_opts
    )

    action_prefix: StringProperty(name="Action Prefix", options=default_opts)
    action_suffix: StringProperty(name="Action Suffix", options=default_opts)

    frame_start: IntProperty(name="Override Start Frame", options=default_opts)
    frame_end: IntProperty(name="Override End Frame", options=default_opts)


class EXPORTER_CONFIG_PT_ExampleAddonPanel(Panel):
    # bl_idname = __name__
    bl_label = "Awesome Exporter"
    bl_description = "Helpful Exporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    use_pin = True
    bl_category = "Export Helper"

    # How To
    # https://docs.blender.org/api/current/bpy.types.UILayout.html
    def draw(self, context):
        layout = self.layout
        settings = context.scene.export_helper_settings

        col = layout.column(align=True)

        col.label(text="Select Armature & Control Rig")

        row = layout.row(align=True)
        rowcol = row.column(align=True)
        rowcol.label(text="Armature")
        rowcol.prop(settings, "armature", icon_only=True)

        rowcol = row.column(align=True)
        rowcol.label(text="Control Rig")
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
        rowcol.label(text="Frame Start")
        rowcol.prop(settings, "frame_start", icon_only=True)

        rowcol = row.column(align=True)
        rowcol.label(text="Frame End")
        rowcol.prop(settings, "frame_end", icon_only=True)

        col = layout.column(align=True)
        col.label(text="Export Method")
        col.prop(settings, "export_method", icon_only=False, expand=True)

        col.prop(settings, "export_path", icon_only=False, expand=True)

        col.prop(settings, "export_fix_forward_axis", icon_only=False, expand=True)

        col.separator()

        col.operator("export_helper.fbx", text="Export")


# Registration
from .animation_exporter import ExportHelper
from bpy.utils import register_class, unregister_class

classes = (
    HelperProperties,
    ExportHelper,
    EXPORTER_CONFIG_PT_ExampleAddonPanel,
)


if "bpy" in locals():
    import importlib

    if "exporter" in locals():
        importlib.reload(animation_exporter)


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
