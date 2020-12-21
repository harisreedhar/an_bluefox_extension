import bpy
import numpy as np
from bpy.props import *
from . effex_base import EffexBase
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures import FloatList

class BF_StepEffexNode(bpy.types.Node, AnimationNode, EffexBase):
    bl_idname = "an_bf_StepEffexNode"
    bl_label = "Step Effex"
    bl_width_default = 200
    errorHandlingType = "EXCEPTION"

    def create(self):
        self.newInput("Matrix List", "Matrices", "matrices", dataIsModified = True)
        self.newInput("Float", "Step", "step")
        self.createBasicInputs()
        self.newOutput("Matrix List", "Matrices", "matrices")
        self.newOutput("Float List", "Values", "effexValues", hide = True)
        self.updateSocketVisibility()

    def draw(self, layout):
        self.draw_MatrixTransformationProperties(layout)

    def drawAdvanced(self, layout):
        self.drawFalloffMixType(layout)

    def getExecutionCode(self, required):
        if "matrices" in required or "effexValues" in required:
            yield "effexValues = AN.data_structures.DoubleList()"
            if any([self.useTranslation, self.useRotation, self.useScale]):
                yield "efStrengths = self.getStepStrengths(len(matrices), step)"
                yield "mixedFalloff = self.mixEffexAndFalloff(efStrengths, falloff, interpolation, outMin=minValue, outMax=maxValue)"
                yield "influences = self.getInfluences(mixedFalloff, matrices)"
                yield "matrices = self.offsetMatrixList(matrices, influences, translation, rotation, scale)"
                if "effexValues" in required:
                    yield "effexValues = AN.data_structures.DoubleList.fromValues(influences)"

    def getStepStrengths(self, amount, step):
        amount = max(1, amount)
        array = np.linspace(0, 1, num = amount, dtype = np.float32)
        if step != 0:
            array = np.round_(array / step) * step
        strengths = FloatList.fromNumpyArray(array)
        return strengths
