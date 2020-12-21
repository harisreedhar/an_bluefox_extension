import bpy
import numpy as np
from bpy.props import *
from . effex_base import EffexBase
from animation_nodes . base_types import AnimationNode, VectorizedSocket
from animation_nodes . data_structures import FloatList, VirtualDoubleList, VirtualBooleanList

class BF_TimeEffexNode(bpy.types.Node, AnimationNode, EffexBase):
    bl_idname = "an_bf_TimeEffexNode"
    bl_label = "Time Effex"
    bl_width_default = 200
    errorHandlingType = "EXCEPTION"

    useDurationList: VectorizedSocket.newProperty()
    useSpeedList: VectorizedSocket.newProperty()
    useInfiniteList: VectorizedSocket.newProperty()

    def create(self):
        self.newInput("Matrix List", "Matrices", "matrices", dataIsModified = True)
        self.newInput("Float", "Time", "time")
        self.newInput(VectorizedSocket("Boolean", "useInfiniteList",
            ("Infinite", "infinites"),
            ("Infinites", "infinites")))
        self.newInput(VectorizedSocket("Float", "useDurationList",
            ("Duration", "durations", dict(value = 20)),
            ("Durations", "durations")))
        self.newInput(VectorizedSocket("Float", "useSpeedList",
            ("Speed", "speeds", dict(value = 1)),
            ("Speeds", "speeds")))
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
                yield "efStrengths = self.getTimeStrengths(time, infinites, durations, speeds, len(matrices))"
                yield "mixedFalloff = self.mixEffexAndFalloff(efStrengths, falloff, interpolation, outMin=minValue, outMax=maxValue)"
                yield "influences = self.getInfluences(mixedFalloff, matrices)"
                yield "matrices = self.offsetMatrixList(matrices, influences, translation, rotation, scale)"
                if "effexValues" in required:
                    yield "effexValues = AN.data_structures.DoubleList.fromValues(influences)"

    def getTimeStrengths(self, time, infinites, durations, speeds, amount):
        amount = max(1, amount)
        _durations = VirtualDoubleList.create(durations, 0).materialize(amount)
        _speeds = VirtualDoubleList.create(speeds, 0).materialize(amount)
        _infinites = VirtualBooleanList.create(infinites, 0).materialize(amount)

        array = time / _durations.asNumpyArray() * _speeds.asNumpyArray()
        mask = _infinites.asNumpyArray() == b''
        array[mask] = np.clip(array[mask], 0, 1)

        strengths = FloatList.fromNumpyArray(array.astype('f'))
        return strengths
