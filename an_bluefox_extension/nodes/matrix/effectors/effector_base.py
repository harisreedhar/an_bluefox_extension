from bpy.props import *
from animation_nodes . nodes . falloff . mix_falloffs import MixFalloffs
from animation_nodes . nodes . falloff . custom_falloff import CustomFalloff
from animation_nodes . nodes.matrix.c_utils import (
    extractMatrixTranslations,
    extractMatrixRotations,
    extractMatrixScales
)
from animation_nodes . data_structures import (
    VirtualVector3DList,
    VirtualEulerList,
    Interpolation
)
from animation_nodes . nodes.falloff.remap_falloff import RemapInterpolatedFalloff
from animation_nodes . events import propertyChanged, executionCodeChanged
from animation_nodes . base_types import AnimationNode, VectorizedSocket
from animation_nodes . algorithms.matrices import (
    translateMatrixList,
    getRotatedMatrixList,
    scaleMatrixList
)

mixTypeItems = [
    ("ADD", "Add", "", "NONE", 0),
    ("MULTIPLY", "Multiply", "", "NONE", 1),
    ("MAX", "Max", "", "NONE", 2),
    ("MIN", "Min", "", "NONE", 3),
    ("NONE", "None", "", "NONE", 4)
]

class EffectorBase:
    def checkedPropertiesChanged(self, context):
            self.updateSocketVisibility()
            executionCodeChanged()

    mixType: EnumProperty(name = "Mix Type", items = mixTypeItems,
        description = "falloff and effector mix method",
        default = "MULTIPLY", update = AnimationNode.refresh)

    useTranslation: BoolProperty(name = "Use Translation", default = False,
        update = checkedPropertiesChanged)
    useRotation: BoolProperty(name = "Use Rotation", default = False,
        update = checkedPropertiesChanged)
    useScale: BoolProperty(name = "Use Scale", default = False,
        update = checkedPropertiesChanged)

    useTranslationList: VectorizedSocket.newProperty()
    useRotationList: VectorizedSocket.newProperty()
    useScaleList: VectorizedSocket.newProperty()

    def createBasicInputs(self):
        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput(VectorizedSocket("Vector", "useTranslationList",
            ("Translation", "translation"),
            ("Translations", "translation")))
        self.newInput(VectorizedSocket("Euler", "useRotationList",
            ("Rotation", "rotation"),
            ("Rotations", "rotation")))
        self.newInput(VectorizedSocket("Vector", "useScaleList",
            ("Scale", "scale", dict(value = (1, 1, 1))),
            ("Scales", "scale")))
        self.newInput("Float", "Min", "minValue", value = 0, hide = True)
        self.newInput("Float", "Max", "maxValue", value = 1, hide = True)
        self.newInput("Interpolation", "Interpolation", "interpolation",
            defaultDrawType = "PROPERTY_ONLY")

    def updateSocketVisibility(self):
        self.inputs[-6].hide = not self.useTranslation
        self.inputs[-5].hide = not self.useRotation
        self.inputs[-4].hide = not self.useScale

    def drawFalloffMixType(self, layout):
        layout.prop(self, "mixType", text="")

    def draw_MatrixTransformationProperties(self, layout):
        col = layout.column()
        row = col.row(align = True)
        row.prop(self, "useTranslation", text = "Loc", icon = "EXPORT")
        row.prop(self, "useRotation", text = "Rot", icon = "FILE_REFRESH")
        row.prop(self, "useScale", text = "Scale", icon = "FULLSCREEN_ENTER")

    def offsetMatrixList(self, matrices, influences, translations, rotations, scales):
        if self.useScale:
            _scales = VirtualVector3DList.create(scales, (1,1,1))
            scaleMatrixList(matrices, "LOCAL_AXIS", _scales, influences)
        if self.useRotation:
            _rotations = VirtualEulerList.create(rotations, (0,0,0))
            matrices = getRotatedMatrixList(matrices, "GLOBAL_AXIS__LOCAL_PIVOT", _rotations, influences)
        if self.useTranslation:
            _translations = VirtualVector3DList.create(translations, (0,0,0))
            translateMatrixList(matrices, "GLOBAL_AXIS", _translations, influences)
        return matrices

    def getInfluences(self, falloff, matrices):
        try: evaluator = falloff.getEvaluator("TRANSFORMATION_MATRIX")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for matrices")
        return evaluator.evaluateList(matrices)

    def getMatriceComponents(self, matrices):
        translations = extractMatrixTranslations(matrices)
        rotations = extractMatrixRotations(matrices)
        scales = extractMatrixScales(matrices)
        return translations, rotations, scales

    def mixEffectorAndFalloff(self, effectorStrengths, falloff, interpolation, outMin = 0, outMax = 1):
        custom = CustomFalloff(effectorStrengths, 0)
        newFalloff = custom
        if self.mixType != "NONE":
            newFalloff = MixFalloffs([falloff, custom], self.mixType, default = 1)
        newFalloff = RemapInterpolatedFalloff(newFalloff, 0, 1, outMin, outMax, interpolation)
        return newFalloff
