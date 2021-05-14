import bpy
from animation_nodes.ui.node_menu import insertNode

class BluefoxExtensionMenu(bpy.types.Menu):
    bl_idname = "AN_MT_bluefox_extension_menu"
    bl_label = "Bluefox Extension Menu"

    def draw(self, context):
        layout = self.layout
        layout.menu("AN_MT_BF_Color_menu", text = "Color")
        layout.menu("AN_MT_BF_Falloff_menu", text = "Falloff")
        layout.menu("AN_MT_BF_Generator_menu", text = "Generator")
        layout.menu("AN_MT_BF_Matrix_menu", text = "Matrix")
        layout.menu("AN_MT_BF_Mesh_menu", text = "Mesh")
        layout.menu("AN_MT_BF_Object_menu", text = "Object")
        layout.menu("AN_MT_BF_Spline_menu", text = "Spline")
        layout.menu("AN_MT_BF_Utility_menu", text = "Utility")

def drawMenu(self, context):
    if context.space_data.tree_type != "an_AnimationNodeTree": return

    layout = self.layout
    layout.operator_context = "INVOKE_DEFAULT"

    layout.separator()
    layout.menu("AN_MT_bluefox_extension_menu", text = "Bluefox Nodes", icon = "MESH_MONKEY")

class BF_ColorMenu(bpy.types.Menu):
    bl_idname = "AN_MT_BF_Color_menu"
    bl_label = "Colors Menu"

    def draw(self, context):
        layout = self.layout
        insertNode(layout, "an_bf_MixRGB", "Mix RGB")

class BF_FalloffMenu(bpy.types.Menu):
    bl_idname = "AN_MT_BF_Falloff_menu"
    bl_label = "Falloff Menu"

    def draw(self, context):
        layout = self.layout
        insertNode(layout, "an_bf_MathFalloffNode", "Math Falloff")
        insertNode(layout, "an_bf_MandelBulbFalloffNode", "Mandelbulb Falloff")
        insertNode(layout, "an_bf_MemoryFalloffNode", "Memory Falloff")
        insertNode(layout, "an_bf_ShapeFalloffNode", "Shape Falloff")
        insertNode(layout, "an_bf_wavefalloff", "Wave Falloff")

class BF_GeneratorMenu(bpy.types.Menu):
    bl_idname = "AN_MT_BF_Generator_menu"
    bl_label = "Generator Menu"

    def draw(self, context):
        layout = self.layout
        insertNode(layout, "an_bf_ChaoticAttractorsNode", "Chaotic Attractors")

class BF_MatrixMenu(bpy.types.Menu):
    bl_idname = "AN_MT_BF_Matrix_menu"
    bl_label = "Matrix Menu"

    def draw(self, context):
        layout = self.layout
        layout.label(text = "Effex Nodes")
        insertNode(layout, "an_bf_FormulaEffexNode", "Formula Effex")
        insertNode(layout, "an_bf_InheritanceEffexNode", "Inheritance Effex")
        insertNode(layout, "an_bf_StepEffexNode", "Step Effex")
        insertNode(layout, "an_bf_TimeEffexNode", "Time Effex")
        layout.separator()

class BF_MeshMenu(bpy.types.Menu):
    bl_idname = "AN_MT_BF_Mesh_menu"
    bl_label = "Mesh Menu"

    def draw(self, context):
        layout = self.layout
        insertNode(layout, "an_bf_FindMeshTensionNode", "Find Mesh Tension")
        insertNode(layout, "an_bf_MarchingCubesNode", "Marching Cubes")
        insertNode(layout, "an_bf_SimpleDeformNode", "Simple Deform")
        insertNode(layout, "an_bf_VoronoiFractureNode", "Voronoi Fracture")

class BF_ObjectMenu(bpy.types.Menu):
    bl_idname = "AN_MT_BF_Object_menu"
    bl_label = "Object Menu"

    def draw(self, context):
        layout = self.layout
        insertNode(layout, "an_bf_DupliInstancer", "Dupli Instancer")
        insertNode(layout, "an_bf_ObjectFractureNode", "Object Fracture")
        insertNode(layout, "an_bf_RigidBodyTriggerNode", "Rigidbody Trigger")

class BF_SplineMenu(bpy.types.Menu):
    bl_idname = "AN_MT_BF_Spline_menu"
    bl_label = "Spline Menu"

    def draw(self, context):
        layout = self.layout
        insertNode(layout, "an_bf_SplineTracerNode", "Spline Tracer")

class BF_UtilityMenu(bpy.types.Menu):
    bl_idname = "AN_MT_BF_Utility_menu"
    bl_label = "Utility Menu"

    def draw(self, context):
        layout = self.layout
        insertNode(layout, "an_bf_AutoFitFloatsNode", "Auto Fit Floats")
        insertNode(layout, "an_bf_SverchokInterfaceNode", "Sverchok Interface")

def register():
    bpy.types.NODE_MT_add.append(drawMenu)

def unregister():
    bpy.types.NODE_MT_add.remove(drawMenu)
