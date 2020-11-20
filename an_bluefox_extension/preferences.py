import os
import bpy
from bpy.props import *
from . import addon_updater

addonName = os.path.basename(os.path.dirname(__file__))

class AN_BlueFoxExtension_Preferences(bpy.types.AddonPreferences):
    bl_idname = addonName
    updateButton: BoolProperty(name = "update", default = False,
        options = {"SKIP_SAVE"})

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "updateButton", text = "Update addon(WIP)", toggle = True)
        if self.updateButton:
            addon_updater.update()
            self.updateButton = False
