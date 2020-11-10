import bpy
from animation_nodes.ui.node_menu import insertNode

class BluefoxExtensionMenu(bpy.types.Menu):
    bl_idname = "AN_MT_bluefox_extension_menu"
    bl_label = "Bluefox Extension Menu"

    def draw(self, context):
        layout = self.layout
        layout.menu("AN_MT_Colors_menu", text = "Color")

def drawMenu(self, context):
    if context.space_data.tree_type != "an_AnimationNodeTree": return

    layout = self.layout
    layout.operator_context = "INVOKE_DEFAULT"

    layout.separator()
    layout.menu("AN_MT_bluefox_extension_menu", text = "Bluefox Nodes", icon = "MESH_MONKEY")

class ColorMenu(bpy.types.Menu):
    bl_idname = "AN_MT_Colors_menu"
    bl_label = "Colors Menu"

    def draw(self, context):
        layout = self.layout
        insertNode(layout, "an_bf_ColorCompositeNode", "Color Composite")
        insertNode(layout, "an_bf_MarchingCubesNode", "Marching Cubes")

def register():
    bpy.types.NODE_MT_add.append(drawMenu)

def unregister():
    bpy.types.NODE_MT_add.remove(drawMenu)
