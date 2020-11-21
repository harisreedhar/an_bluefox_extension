import bpy
from bpy.props import *
from mathutils import Matrix
from . effector_base import EffectorBase
from animation_nodes . base_types import AnimationNode
from . c_utils import inheritMatrixOverSpline, matrixListLerp
from animation_nodes . algorithms.rotations import directionsToMatrices
from animation_nodes . events import executionCodeChanged, propertyChanged
from animation_nodes . data_structures import FloatList, VirtualMatrix4x4List
from animation_nodes . nodes . number . c_utils import range_DoubleList_StartStep
from animation_nodes . nodes . spline . spline_evaluation_base import SplineEvaluationBase

trackAxisItems = [(axis, axis, "") for axis in ("X", "Y", "Z", "-X", "-Y", "-Z")]
guideAxisItems  = [(axis, axis, "") for axis in ("X", "Y", "Z")]

selectModeItems = [
    ("LINEAR", "Linear", "Linear interpolation", "", 0),
    ("SPLINE", "Spline", "Along Curve", "", 1)
]

class BF_InheritanceEffectorNode(bpy.types.Node, AnimationNode, EffectorBase, SplineEvaluationBase):
    bl_idname = "an_bf_InheritanceEffector"
    bl_label = "Inheritance Effector"
    errorHandlingType = "EXCEPTION"

    align: BoolProperty(name = "Align", default = False,
        description = "Align to Spline",
        update = AnimationNode.refresh)

    trackAxis: EnumProperty(items = trackAxisItems, update = propertyChanged, default = "Z")
    guideAxis: EnumProperty(items = guideAxisItems, update = propertyChanged, default = "X")

    selectMode: EnumProperty(name = "Mode", default = "LINEAR",
        items = selectModeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Matrix List", "Matrices A", "mA", dataIsModified = True)
        self.newInput("Matrix List", "Matrices B", "mB")
        if self.selectMode == "SPLINE":
            self.newInput("Spline", "Spline", "spline", defaultDrawType = "PROPERTY_ONLY")
            self.newInput("Integer", "Samples", "samples", minValue = 1, value = 30)
        self.newInput("Falloff", "Falloff", "falloff")
        self.createMinMaxInterpolationInputs()

        self.newOutput("Matrix List", "Matrices", "matrices")
        self.newOutput("Float List", "Values", "effectorValues", hide = True)

    def draw(self, layout):
        layout.prop(self, "selectMode", text = "")
        if self.selectMode == "SPLINE":
            layout.prop(self, "align")
            if self.align:
                layout.prop(self, "trackAxis", expand = True)
                layout.prop(self, "guideAxis", expand = True)
                if self.trackAxis[-1:] == self.guideAxis[-1:]:
                    layout.label(text = "Must be different", icon = "ERROR")

    def drawAdvanced(self, layout):
        layout.prop(self, "resolution")

    def getExecutionCode(self, required):
        if "matrices" in required or "effectorValues" in required:
            yield "effectorValues = AN.data_structures.DoubleList()"
            yield "falloff = self.remapFalloff(falloff, interpolation, outMin=minValue, outMax=maxValue)"
            yield "influences = self.getInfluences(falloff, mA)"
            if self.selectMode == "SPLINE":
                yield "matrices = self.executeSpline(mA, mB, spline, samples, influences)"
            else:
                yield "matrices = self.executeLinear(mA, mB, influences)"
            if "effectorValues" in required:
                    yield "effectorValues = AN.data_structures.DoubleList.fromValues(influences)"

    def executeLinear(self, mA, mB, influences):
        amount = len(mA)
        if amount:
            if amount != len(mB):
                mB = VirtualMatrix4x4List.create(mB, Matrix.Identity(4)).materialize(amount)
            return matrixListLerp(mA, mB, influences)
        else:
            return mA

    def executeSpline(self, mA, mB, spline, samples, influences):
        amount = len(mA)
        if amount:
            if amount != len(mB):
                mB = VirtualMatrix4x4List.create(mB, Matrix.Identity(4)).materialize(amount)
            samples = max(1, samples)
            pathPoints, splineRotations = self.evalSpline(spline, samples)
            result = inheritMatrixOverSpline(mA, mB, pathPoints, splineRotations, influences, self.align)
            return result
        else:
            return mA

    def evalSpline(self, spline, samples):
        spline.ensureUniformConverter(self.resolution)
        spline.ensureNormals()
        evalRange = range_DoubleList_StartStep(samples, 0, 1/samples)
        parameters = FloatList.fromValues(evalRange)
        parameters = spline.toUniformParameters(parameters)

        locations = spline.samplePoints(parameters, False, 'RESOLUTION')
        tangents = spline.sampleTangents(parameters, False, 'RESOLUTION')
        normals = spline.sampleNormals(parameters, False, 'RESOLUTION')

        rotationMatrices = directionsToMatrices(tangents, normals, self.trackAxis, self.guideAxis)
        return locations, rotationMatrices
