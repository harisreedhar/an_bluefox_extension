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
        self.newInput("Mesh", "Initial Mesh", "initial")
        self.newInput("Mesh", "Deformed Mesh", "deformed")
        self.newInput("Float", "Intensity", "intensity", value = 1)
        self.newInput("Float", "Influence", "influence", value = 0.75, minValue = 0, maxValue = 1)
        self.newInput("Float", "Min", "minValue", value = 0, hide = True)
        self.newInput("Float", "Max", "maxValue", value = 1, hide = True)

        self.newOutput("Float List", "Values", "values")

    def execute(self, initial, deformed, strength, influence, minValue, maxValue):
        if len(initial.edges) != len(deformed.edges):
            self.raiseErrorMessage("Number of vertices and edges should be same in both meshes")
            return DoubleList()
        values = findMeshTension(initial, deformed, strength, influence)
        values.clamp(minValue, maxValue)
        return values
