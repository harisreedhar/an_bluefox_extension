import os
import bpy
import sys
from bpy.props import *
from . utils import module_util
from . operators import module_installer

addonName = os.path.basename(os.path.dirname(__file__))

class AnimationNodesPreferences(bpy.types.AddonPreferences):
    bl_idname = addonName

    def draw(self, context):
        layout = self.layout
        drawModuleInstaller(context, layout)

def drawModuleInstaller(context: bpy.types.Context, layout: bpy.types.UILayout):
    modules = ["numpy"]

    box = layout.box()
    box.label(text = "Install modules:")
    col = box.column(align = True)

    for module in modules:
        title = module.title()
        if module_util.isInstalled(module):
            row = col.row(align = True)
            row.label(text = f'{title} is installed', icon = 'CHECKMARK')
        else:
            row = col.row(align = True)
            #row.label(text = f'{title} is missing', icon = 'ERROR')
            op = row.operator(module_installer.BF_InstallModule.bl_idname,
                      text = f'Install {title}', icon = 'IMPORT')
            op.name = module
