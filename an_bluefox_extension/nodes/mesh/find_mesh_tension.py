import bpy
from bpy.props import *
from . c_utils import findMeshTension
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures import DoubleList

class BF_FindMeshTensionNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_FindMeshTensionNode"
    bl_label = "Find Mesh Tension"
    bl_width = 150
    errorHandlingType = "EXCEPTION"

    def create(self):
        self.newInput("Mesh", "Original", "original")
        self.newInput("Mesh", "Deformed", "deformed")
        self.newInput("Float", "Strength", "strength", value = 1)
        self.newInput("Float", "Bias", "bias")
        self.newInput("Float", "Min", "minValue", value = 0, hide = True)
        self.newInput("Float", "Max", "maxValue", value = 1, hide = True)

        self.newOutput("Float List", "Values", "values")
        self.newOutput("Color List", "Colors", "colors")

    def execute(self, original, deformed, strength, bias, minValue, maxValue):
        if len(original.edges) != len(deformed.edges):
            self.raiseErrorMessage("Number of vertices and edges should be same in both meshes")
            return DoubleList()
        values, colors = findMeshTension(original, deformed, strength, bias)
        values.clamp(minValue, maxValue)
        return values, colors
