import os
import bpy
import sys
from bpy.props import *
from . import addon_updater_ops

addonName = os.path.basename(os.path.dirname(__file__))

class AnimationNodesPreferences(bpy.types.AddonPreferences):
    bl_idname = addonName

    # addon updater preferences from `__init__`, be sure to copy all of them
    auto_check_update = bpy.props.BoolProperty(
        name = "Auto-check for Update",
        description = "If enabled, auto-check for updates using an interval",
        default = False,
    )

    updater_intrval_months = bpy.props.IntProperty(
        name='Months',
        description = "Number of months between checking for updates",
        default=0,
        min=0
    )
    updater_intrval_days = bpy.props.IntProperty(
        name='Days',
        description = "Number of days between checking for updates",
        default=7,
        min=0,
    )
    updater_intrval_hours = bpy.props.IntProperty(
        name='Hours',
        description = "Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
    )
    updater_intrval_minutes = bpy.props.IntProperty(
        name='Minutes',
        description = "Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59
    )

    showUninstallInfo: BoolProperty(name = "Show Deinstall Info", default = False,
        options = {"SKIP_SAVE"})

    def draw(self, context):
        layout = self.layout
        addon_updater_ops.update_settings_ui(self,context)
        col = layout.column(align = True)
        col.split(factor = 0.25).prop(self, "showUninstallInfo", text = "How to Uninstall?",
            toggle = True, icon = "INFO")
        if self.showUninstallInfo:
            col.label(text = "1. Disable Animation Nodes and save the user settings.")
            col.label(text = "2. Restart Blender and remove the addon (without enabling it first).")
