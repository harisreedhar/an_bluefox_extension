import bpy
from bpy.props import *
from mathutils import Matrix
from . effector_base import EffectorBase
from animation_nodes . events import propertyChanged
from animation_nodes . base_types import AnimationNode
from animation_nodes . algorithms.rotations import directionsToMatrices
from animation_nodes . nodes . number . c_utils import range_DoubleList_StartStep
from animation_nodes . nodes . spline . spline_evaluation_base import SplineEvaluationBase
from . c_utils import inheritMatrixOverSpline, matrixTranslationLerp, matrixRotationLerp, matrixScaleLerp
from animation_nodes . nodes . matrix . c_utils import setLocations, rotationsFromVirtualEulers, scalesFromVirtualVectors, multiplyMatrixLists
from animation_nodes . data_structures import FloatList, VirtualMatrix4x4List, VirtualEulerList, VirtualVector3DList, Vector3DList, EulerList, Matrix4x4List

trackAxisItems = [(axis, axis, "") for axis in ("X", "Y", "Z", "-X", "-Y", "-Z")]
guideAxisItems  = [(axis, axis, "") for axis in ("X", "Y", "Z")]

selectModeItems = [
    ("LINEAR", "Linear", "Linear interpolation", "", 0),
    ("SPLINE", "Spline", "Along Curve", "", 1)
]

class BF_InheritanceEffectorNode(bpy.types.Node, AnimationNode, EffectorBase, SplineEvaluationBase):
    bl_idname = "an_bf_InheritanceEffector"
    bl_label = "Inheritance Effector"
    bl_width_default = 200
    errorHandlingType = "EXCEPTION"

    align: BoolProperty(name = "Align", default = False,
        description = "Align to Spline",
        update = AnimationNode.refresh)

    trackAxis: EnumProperty(items = trackAxisItems, update = propertyChanged, default = "Z")
    guideAxis: EnumProperty(items = guideAxisItems, update = propertyChanged, default = "X")

    selectMode: EnumProperty(name = "Mode", default = "LINEAR",
        items = selectModeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Matrix List", "Matrices", "matrices", dataIsModified = True)
        if self.selectMode == "SPLINE":
            self.newInput("Spline", "Spline", "spline", defaultDrawType = "PROPERTY_ONLY")
            self.newInput("Integer", "Samples", "samples", minValue = 1, value = 30)
        self.createBasicInputs()

        self.newOutput("Matrix List", "Matrices", "matrices")
        self.newOutput("Float List", "Values", "effectorValues", hide = True)
        self.updateSocketVisibility()

    def draw(self, layout):
        layout.prop(self, "selectMode", text = "")
        if self.selectMode == "SPLINE":
            row = layout.row(align = True)
            label = "Align on spline"
            if self.align:
                label = ""
            row.prop(self, "align", text = label)
            if self.align:
                row.prop(self, "trackAxis", index = 0, expand = True)
                row2 = row.row(align = True)
                row2.active = False
                row2.prop(self, "guideAxis", index = 1, expand = True)
                if self.trackAxis[-1:] == self.guideAxis[-1:]:
                    layout.label(text = "Must be different", icon = "ERROR")
        self.draw_MatrixTransformationProperties(layout)

    def drawAdvanced(self, layout):
        if self.selectMode == "SPLINE":
            layout.prop(self, "resolution")

    def getExecutionCode(self, required):
        if "matrices" in required or "effectorValues" in required:
            yield "effectorValues = AN.data_structures.DoubleList()"
            yield "newfalloff = self.remapFalloff(falloff, interpolation, outMin=minValue, outMax=maxValue)"
            yield "influences = self.getInfluences(newfalloff, matrices)"
            if self.selectMode == "SPLINE":
                yield "matrices = self.executeSpline(matrices, spline, samples, translation, rotation, scale, influences)"
            else:
                yield "matrices = self.executeLinear(matrices, translation, rotation, scale, influences)"
            if "effectorValues" in required:
                    yield "effectorValues = AN.data_structures.DoubleList.fromValues(influences)"

    def executeLinear(self, matrices, translation, rotation, scale, influences):
        if not self.useTranslationList: translation = Vector3DList.fromValues([translation])
        if not self.useRotationList: rotation = EulerList.fromValues([rotation])
        if not self.useScaleList: scale = Vector3DList.fromValues([scale])

        if self.useTranslation:
            _translation = VirtualVector3DList.create(translation, (0,0,0))
            matrices = matrixTranslationLerp(matrices, _translation, influences)
        if self.useRotation:
            _rotation = VirtualEulerList.create(rotation, (0,0,0))
            rotationMatrices = matrixRotationLerp(matrices, _rotation, influences)
            matrices = multiplyMatrixLists(matrices, rotationMatrices)
        if self.useScale:
            _scales = VirtualVector3DList.create(scale, (1,1,1))
            scaleMatrices = matrixScaleLerp(matrices, _scales, influences)
            matrices = multiplyMatrixLists(matrices, scaleMatrices)
        return matrices

    def executeSpline(self, matrices, spline, samples, translation, rotation, scale, influences):
        try:
            amount = len(matrices)
            if amount:
                if not self.useTranslationList: translation = Vector3DList.fromValues([translation])
                if not self.useRotationList: rotation = EulerList.fromValues([rotation])
                if not self.useScaleList: scale = Vector3DList.fromValues([scale])
                matrices2 = Matrix4x4List(length = amount)
                matrices2.fill(Matrix.Identity(4))
                if self.useTranslation:
                    _translation = VirtualVector3DList.create(translation, (0,0,0))
                    setLocations(matrices2, _translation)
                if self.useRotation:
                    _rotation = VirtualEulerList.create(rotation, (0,0,0))
                    rotationMatrix = rotationsFromVirtualEulers(amount, _rotation)
                    matrices2 = multiplyMatrixLists(matrices2, rotationMatrix)
                if self.useScale:
                    _scale = VirtualVector3DList.create(scale, (1,1,1))
                    scaleMatrix = scalesFromVirtualVectors(amount, _scale)
                    matrices2 = multiplyMatrixLists(matrices2, scaleMatrix)

                samples = max(1, samples)
                pathPoints, splineRotations = self.evalSpline(spline, samples)
                result = inheritMatrixOverSpline(matrices, matrices2, pathPoints, splineRotations, influences, self.align)
                return result
        except:
            return matrices

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
