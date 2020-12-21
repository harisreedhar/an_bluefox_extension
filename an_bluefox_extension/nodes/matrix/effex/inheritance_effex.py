import bpy
from bpy.props import *
from mathutils import Matrix
from . effex_base import EffexBase
from animation_nodes . events import propertyChanged
from animation_nodes . algorithms.rotations import directionsToMatrices
from animation_nodes . base_types import AnimationNode, VectorizedSocket
from animation_nodes . nodes . number . c_utils import range_DoubleList_StartStep
from animation_nodes . nodes . spline . spline_evaluation_base import SplineEvaluationBase

from . c_utils import (
    inheritMatrixOverSpline, matrixTranslationLerp,
    matrixRotationLerp, matrixScaleLerp, inhertMatrixLinear,
    vectorListLerp, inheritPointsOverSpline
)
from animation_nodes . nodes . matrix . c_utils import (
    setLocations, rotationsFromVirtualEulers,
    scalesFromVirtualVectors, multiplyMatrixLists
)
from animation_nodes . data_structures import (
    FloatList, VirtualMatrix4x4List,
    VirtualEulerList, VirtualVector3DList,
    Vector3DList, EulerList, Matrix4x4List
)

trackAxisItems = [(axis, axis, "") for axis in ("X", "Y", "Z", "-X", "-Y", "-Z")]
guideAxisItems  = [(axis, axis, "") for axis in ("X", "Y", "Z")]

selectModeItems = [
    ("LINEAR", "Linear", "Linear interpolation", "", 0),
    ("SPLINE", "Spline", "Along Curve", "", 1)
]

dataModeItems = [
    ("MATRIX_COMPONENTS", "Matrices & Components", "", "", 0),
    ("MATRIX_MATRIX", "Matrices & Matrices", "", "", 1),
    ("VECTOR_VECTOR", "Vectors & Vectors", "", "", 2)
]

class BF_InheritanceEffexNode(bpy.types.Node, AnimationNode, EffexBase, SplineEvaluationBase):
    bl_idname = "an_bf_InheritanceEffexNode"
    bl_label = "Inheritance Effex"
    bl_width_default = 200
    errorHandlingType = "EXCEPTION"

    align: BoolProperty(name = "Align", default = False,
        description = "Align to Spline",
        update = AnimationNode.refresh)

    trackAxis: EnumProperty(items = trackAxisItems, update = propertyChanged, default = "Z")
    guideAxis: EnumProperty(items = guideAxisItems, update = propertyChanged, default = "X")

    selectMode: EnumProperty(name = "Mode", default = "LINEAR",
        items = selectModeItems, update = AnimationNode.refresh)

    dataMode: EnumProperty(name = "Data Mode", default = "MATRIX_COMPONENTS",
        items = dataModeItems, update = AnimationNode.refresh)

    useMatrixList: VectorizedSocket.newProperty()
    useVectorList: VectorizedSocket.newProperty()

    def create(self):
        if self.dataMode in ['MATRIX_COMPONENTS', 'MATRIX_MATRIX']:
            if self.dataMode == 'MATRIX_MATRIX':
                self.newInput("Matrix List", "Matrices 1", "matrices", dataIsModified = True)
                self.newInput(VectorizedSocket("Matrix", "useMatrixList",
                    ("Matrix 2", "matrices2"),
                    ("Matrices 2", "matrices2")))
                self.newInput("Falloff", "Falloff", "falloff")
            else:
                self.newInput("Matrix List", "Matrices", "matrices", dataIsModified = True)

            if self.selectMode == "SPLINE":
                self.newInput("Spline", "Spline", "spline", defaultDrawType = "PROPERTY_ONLY")
                self.newInput("Integer", "Samples", "samples", minValue = 1, value = 30)
            if self.dataMode == 'MATRIX_COMPONENTS':
                self.createBasicInputs()
            else:
                self.createMinMaxInterpolationInputs()

            self.newOutput("Matrix List", "Matrices", "matrices")
            self.newOutput("Float List", "Values", "effexValues", hide = True)
            if self.dataMode == 'MATRIX_COMPONENTS':
                self.updateSocketVisibility()

        if self.dataMode == 'VECTOR_VECTOR':
            self.newInput("Vector List", "Vectors 1", "vectors1", dataIsModified = True)
            self.newInput(VectorizedSocket("Vector", "useVectorList",
                    ("Vector 2", "vectors2"),
                    ("Vectors 2", "vectors2")))
            self.newInput("Falloff", "Falloff", "falloff")
            if self.selectMode == "SPLINE":
                self.newInput("Spline", "Spline", "spline", defaultDrawType = "PROPERTY_ONLY")
                self.newInput("Integer", "Samples", "samples", minValue = 1, value = 30)
            self.createMinMaxInterpolationInputs()

            self.newOutput("Vector List", "Vectors", "vectors")
            self.newOutput("Float List", "Values", "effexValues", hide = True)

    def draw(self, layout):
        #layout.prop(self, "selectMode", text = "")
        if self.dataMode != 'VECTOR_VECTOR':
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
        if self.dataMode == 'MATRIX_COMPONENTS':
            self.draw_MatrixTransformationProperties(layout)

    def drawAdvanced(self, layout):
        layout.prop(self, "dataMode", text = "")
        if self.selectMode == "SPLINE":
            layout.prop(self, "resolution")

    def getExecutionCode(self, required):
        if self.dataMode in ['MATRIX_COMPONENTS', 'MATRIX_MATRIX']:
            if "matrices" in required or "effexValues" in required:
                yield "effexValues = AN.data_structures.DoubleList()"
                yield "newfalloff = self.remapFalloff(falloff, interpolation, outMin=minValue, outMax=maxValue)"
                yield "influences = self.getInfluences(newfalloff, matrices)"
                if self.selectMode == "SPLINE":
                    if self.dataMode == 'MATRIX_COMPONENTS':
                        yield "matrices = self.executeSpline_MAT_COMP(matrices, spline, samples, translation, rotation, scale, influences)"
                    if self.dataMode == 'MATRIX_MATRIX':
                        yield "matrices = self.executeSpline_MAT_MAT(matrices, matrices2, spline, samples, influences)"
                else:
                    if self.dataMode == 'MATRIX_COMPONENTS':
                        yield "matrices = self.executeLinear_MAT_COMP(matrices, translation, rotation, scale, influences)"
                    if self.dataMode == 'MATRIX_MATRIX':
                        yield "matrices = self.executeLinear_MAT_MAT(matrices, matrices2, influences)"
                if "effexValues" in required:
                        yield "effexValues = AN.data_structures.DoubleList.fromValues(influences)"

        if self.dataMode == 'VECTOR_VECTOR':
            if "vectors" in required or "effexValues" in required:
                yield "effexValues = AN.data_structures.DoubleList()"
                yield "newfalloff = self.remapFalloff(falloff, interpolation, outMin=minValue, outMax=maxValue)"
                yield "evaluator = newfalloff.getEvaluator('LOCATION')"
                yield "influences = evaluator.evaluateList(vectors1)"
                if self.selectMode == "SPLINE":
                    yield "vectors = self.executeSpline_VEC_VEC(vectors1, vectors2, spline, samples, influences)"
                else:
                    yield "vectors = self.executeLinear_VEC_VEC(vectors1, vectors2, influences)"
                if "effexValues" in required:
                        yield "effexValues = AN.data_structures.DoubleList.fromValues(influences)"

    def executeLinear_MAT_COMP(self, matrices, translation, rotation, scale, influences):
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

    def executeLinear_MAT_MAT(self, matrices, matrices2, influences):
        if not self.useMatrixList: matrices2 = Matrix4x4List.fromValues([matrices2])
        try:
            return inhertMatrixLinear(matrices, matrices2, influences)
        except:
            return matrices

    def executeLinear_VEC_VEC(self, vectors1, vectors2, influences):
        if not self.useVectorList: vectors2 = Vector3DList.fromValues([vectors2])
        return vectorListLerp(vectors1, vectors2, influences)

    def executeSpline_MAT_COMP(self, matrices, spline, samples, translation, rotation, scale, influences):
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

    def executeSpline_MAT_MAT(self, matrices, matrices2, spline, samples, influences):
        try:
            amount = len(matrices)
            if amount:
                if not self.useMatrixList: matrices2 = Matrix4x4List.fromValues([matrices2])
                matrices2 = VirtualMatrix4x4List.create(matrices2, Matrix.Identity(4)).materialize(amount)
                samples = max(1, samples)
                pathPoints, splineRotations = self.evalSpline(spline, samples)
                result = inheritMatrixOverSpline(matrices, matrices2, pathPoints, splineRotations, influences, self.align)
                return result
        except:
            return matrices

    def executeSpline_VEC_VEC(self, vectors1, vectors2, spline, samples, influences):
        try:
            amount = len(vectors1)
            if amount:
                if not self.useVectorList: vectors2 = Vector3DList.fromValues([vectors2])
                vectors2 = VirtualVector3DList.create(vectors2, (0,0,0)).materialize(amount)
                samples = max(1, samples)
                pathPoints, splineRotations = self.evalSpline(spline, samples)
                result = inheritPointsOverSpline(vectors1, vectors2, pathPoints, influences)
                return result
        except:
            return vectors1

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
