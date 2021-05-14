import bpy
from animation_nodes . base_types import AnimationNode
from animation_nodes . nodes . number . c_utils import mapRange_DoubleList_Interpolated

class BF_AutoFitFloatsNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_AutoFitFloatsNode"
    bl_label = "Auto Fit Floats"

    def create(self):
        self.newInput("Float List", "Number List", "numbers")
        self.newInput("Float", "Min", "outMin", value = 0)
        self.newInput("Float", "Max", "outMax", value = 1)
        self.newInput("Interpolation", "Interpolation", "interpolation", defaultDrawType = "PROPERTY_ONLY")
        self.newOutput("Float List", "Result", "result")

    def execute(self, numbers, outMin, outMax, interpolation):
        inMin = numbers.getMinValue() if len(numbers) > 0 else 0
        inMax = numbers.getMaxValue() if len(numbers) > 0 else 0
        return mapRange_DoubleList_Interpolated(numbers, interpolation, inMin, inMax, outMin, outMax)
