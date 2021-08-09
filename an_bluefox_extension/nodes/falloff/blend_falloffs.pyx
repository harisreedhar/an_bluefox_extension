import bpy
from bpy.props import *
from animation_nodes . events import propertyChanged
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures cimport CompoundFalloff, Falloff
from ... utils . blend cimport (
    blendFloats, add, multiply, screen,
    overlay, subtract, divide, difference,
    darken, lighten, softLight, hardMix
)

blendModeItems = [
    ("MIX", "Mix", "", "", 0),
    ("MIN", "Min", "", "", 1), # darken
    ("MAX", "Max", "", "", 2), # lighten
    ("ADD", "Add", "", "", 3),
    ("SUBTRACT", "Subtract", "", "", 4),
    ("MULTIPLY", "Multiply", "", "", 5),
    ("DIVIDE", "Divide", "", "", 6),
    ("DIFFERENCE", "Difference", "", "", 7),
    ("SCREEN", "Screen", "", "", 8),
    ("OVERLAY", "Overlay", "", "", 9),
    ("SOFTLIGHT", "Soft Light", "", "", 10),
    ("HARDMIX", "Hard Mix", "", "", 11),
]

class BF_BlendFalloffsNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_BlendFalloffsNode"
    bl_label = "Blend Falloffs"
    errorHandlingType = "EXCEPTION"

    __annotations__ = {}

    __annotations__["clampLower"] = BoolProperty(name = "Clamp Lower", description = "Clamp values less than 0", update = propertyChanged)

    __annotations__["clampUpper"] = BoolProperty(name = "Clamp Upper", description = "Clamp values greater than 1", update = propertyChanged)

    __annotations__["blendMode"] = EnumProperty(name = "Blending Mode", default = "MIX",
        items = blendModeItems, update = propertyChanged)

    def create(self):
        self.newInput("Falloff", "Factor", "factor", value = 0)
        self.newInput("Falloff", "A", "a")
        self.newInput("Falloff", "B", "b")
        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        row = layout.row(align = True)
        subrow = row.row(align = True)
        subrow.prop(self, "blendMode", text = "")
        subrow = subrow.row(align = True)
        subrow.scale_x = 0.3
        subrow.prop(self, "clampLower", index = 1, text = "[", toggle = True)
        subrow.prop(self, "clampUpper", index = 2, text = "]", toggle = True)

    def execute(self, factor, a, b):
        mode = self.blendMode
        output = a

        if mode == 'MIX': output = BlendFalloff(a, b, factor)
        elif mode == 'MIN': output = Blend_MinFalloff(a, b, factor)
        elif mode == 'MAX': output = Blend_MaxFalloff(a, b, factor)
        elif mode == 'ADD': output = Blend_AddFalloff(a, b, factor)
        elif mode == 'SUBTRACT': output = Blend_SubtractFalloff(a, b, factor)
        elif mode == 'DIFFERENCE': output = Blend_DifferenceFalloff(a, b, factor)
        elif mode == 'MULTIPLY': output = Blend_MultipyFalloff(a, b, factor)
        elif mode == 'DIVIDE': output = Blend_DivideFalloff(a, b, factor)
        elif mode == 'SCREEN': output = Blend_ScreenFalloff(a, b, factor)
        elif mode == 'OVERLAY': output = Blend_OverlayFalloff(a, b, factor)
        elif mode == 'SOFTLIGHT': output = Blend_SoftLightFalloff(a, b, factor)
        elif mode == 'HARDMIX': output = Blend_HardMixFalloff(a, b, factor)

        clampLower = self.clampLower
        clampUpper = self.clampUpper
        if any([clampLower, clampUpper]):
            return ClampFalloff(output, clampLower, clampUpper)
        return output

cdef class ClampFalloff(CompoundFalloff):
    cdef:
        Falloff falloff
        bint clampLower, clampUpper

    def __cinit__(self, Falloff falloff, bint clampLower, bint clampUpper):
        self.falloff = falloff
        self.clampLower = clampLower
        self.clampUpper = clampUpper

    cdef list getDependencies(self):
        return [self.falloff]

    cdef float evaluate(self, float *dependencyResults):
        if self.clampLower and not self.clampUpper:
            return max(dependencyResults[0], 0)
        if self.clampUpper and not self.clampLower:
            return min(dependencyResults[0], 1)
        return min(max(dependencyResults[0], 0), 1)

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef float *data = dependencyResults[0]
        cdef Py_ssize_t i
        if self.clampLower and not self.clampUpper:
            for i in range(amount):
                target[i] = max(data[i], 0)
            return
        elif self.clampUpper and not self.clampLower:
            for i in range(amount):
                target[i] = min(data[i], 1)
            return
        for i in range(amount):
            target[i] = min(max(data[i], 0), 1)

cdef class BlendFalloffBase(CompoundFalloff):
    cdef:
        Falloff a, b, factor

    def __cinit__(self, Falloff a, Falloff b, Falloff factor):
        self.a = a
        self.b = b
        self.factor = factor

    cdef list getDependencies(self):
        return [self.a, self.b, self.factor]

cdef class BlendFalloff(BlendFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return blendFloats(dependencyResults[0], dependencyResults[1], dependencyResults[2])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        cdef float *factor = dependencyResults[2]
        for i in range(amount):
            target[i] = blendFloats(a[i], b[i], factor[i])

cdef class Blend_MultipyFalloff(BlendFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return multiply(dependencyResults[0], dependencyResults[1], dependencyResults[2])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        cdef float *factor = dependencyResults[2]
        for i in range(amount):
            target[i] = multiply(a[i], b[i], factor[i])

cdef class Blend_ScreenFalloff(BlendFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return screen(dependencyResults[0], dependencyResults[1], dependencyResults[2])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        cdef float *factor = dependencyResults[2]
        for i in range(amount):
            target[i] = screen(a[i], b[i], factor[i])

cdef class Blend_AddFalloff(BlendFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return add(dependencyResults[0], dependencyResults[1], dependencyResults[2])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        cdef float *factor = dependencyResults[2]
        for i in range(amount):
            target[i] = add(a[i], b[i], factor[i])

cdef class Blend_SubtractFalloff(BlendFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return subtract(dependencyResults[0], dependencyResults[1], dependencyResults[2])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        cdef float *factor = dependencyResults[2]
        for i in range(amount):
            target[i] = subtract(a[i], b[i], factor[i])

cdef class Blend_DivideFalloff(BlendFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return divide(dependencyResults[0], dependencyResults[1], dependencyResults[2])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        cdef float *factor = dependencyResults[2]
        for i in range(amount):
            target[i] = divide(a[i], b[i], factor[i])

cdef class Blend_OverlayFalloff(BlendFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return overlay(dependencyResults[0], dependencyResults[1], dependencyResults[2])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        cdef float *factor = dependencyResults[2]
        for i in range(amount):
            target[i] = overlay(a[i], b[i], factor[i])

cdef class Blend_SoftLightFalloff(BlendFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return softLight(dependencyResults[0], dependencyResults[1], dependencyResults[2])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        cdef float *factor = dependencyResults[2]
        for i in range(amount):
            target[i] = softLight(a[i], b[i], factor[i])

cdef class Blend_HardMixFalloff(BlendFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return hardMix(dependencyResults[0], dependencyResults[1], dependencyResults[2])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        cdef float *factor = dependencyResults[2]
        for i in range(amount):
            target[i] = hardMix(a[i], b[i], factor[i])

cdef class Blend_MinFalloff(BlendFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return darken(dependencyResults[0], dependencyResults[1], dependencyResults[2])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        cdef float *factor = dependencyResults[2]
        for i in range(amount):
            target[i] = darken(a[i], b[i], factor[i])

cdef class Blend_MaxFalloff(BlendFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return lighten(dependencyResults[0], dependencyResults[1], dependencyResults[2])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        cdef float *factor = dependencyResults[2]
        for i in range(amount):
            target[i] = lighten(a[i], b[i], factor[i])

cdef class Blend_DifferenceFalloff(BlendFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return difference(dependencyResults[0], dependencyResults[1], dependencyResults[2])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        cdef float *factor = dependencyResults[2]
        for i in range(amount):
            target[i] = difference(a[i], b[i], factor[i])
