import bpy
from bpy.props import *
from animation_nodes . math cimport Vector3, toVector3
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures cimport BaseFalloff
from ... libs . noise cimport fPerlin4D, fPeriodicPerlin4D, fSimplex4D

noiseTypeTypeItems = [
    ("PERLIN", "Perlin", "", "", 0),
    ("SIMPLEX", "Simplex", "", "", 1),
]

class BF_Noise4DFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_Noise4DFalloffNode"
    bl_label = "Noise 4D Falloff"

    __annotations__ = {}

    __annotations__["noiseType"] = EnumProperty(name = "Noise Type", default = "SIMPLEX",
        items = noiseTypeTypeItems, update = AnimationNode.refresh)
    __annotations__["periodic"] = BoolProperty(update = AnimationNode.refresh)

    def create(self):
        self.newInput("Float", "W", "w")
        self.newInput("Float", "Amplitude", "amplitude", value = 1)
        self.newInput("Float", "Frequency", "frequency", value = 0.1)
        self.newInput("Vector", "Offset", "offset")
        self.newInput("Integer", "Octaves", "octaves", value = 1, minValue = 1, maxValue = 8)
        if self.noiseType == "PERLIN":
            if self.periodic:
                self.newInput("Integer", "PX", "px", value = 1, minValue = 1)
                self.newInput("Integer", "PY", "py", value = 1, minValue = 1)
                self.newInput("Integer", "PZ", "pz", value = 1, minValue = 1)
                self.newInput("Integer", "PW", "pw", value = 1, minValue = 1)
        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        layout.prop(self, "noiseType", text = "")
        if self.noiseType == "PERLIN":
            layout.prop(self, "periodic", text = "Periodic")

    def getExecutionFunctionName(self):
        if self.noiseType == 'PERLIN':
            if self.periodic:
                return "execute_Periodic_Perlin"
            return "execute_Perlin"
        if self.noiseType == 'SIMPLEX':
            return "execute_Simplex"

    def execute_Perlin(self, w, amplitude, frequency, offset, octaves):
        return Noise4DFalloff(w, amplitude, frequency, offset, octaves, 1, 1, 1, 1, self.noiseType)

    def execute_Periodic_Perlin(self, w, amplitude, frequency, offset, octaves, px, py, pz, pw):
        return Noise4DFalloff(w, amplitude, frequency, offset, octaves, px, py, pz, pw, 'PERIODIC_PERLIN')

    def execute_Simplex(self, w, amplitude, frequency, offset, octaves):
        return Noise4DFalloff(w, amplitude, frequency, offset, octaves, 1, 1, 1, 1, self.noiseType)

cdef class Noise4DFalloff(BaseFalloff):
    cdef:
        float w, amplitude, frequency
        Vector3 offset
        int octaves, px, py, pz, pw
        str noiseType

    def __cinit__(self, w, amplitude, frequency, offset, octaves, px, py, pz, pw, noiseType):
        self.w = w
        self.amplitude = amplitude
        self.frequency = frequency
        self.offset = toVector3(offset)
        self.octaves = octaves
        self.px = max(abs(px), 1)
        self.py = max(abs(py), 1)
        self.pz = max(abs(pz), 1)
        self.pw = max(abs(pw), 1)
        self.noiseType = noiseType

        self.dataType = "LOCATION"

    cdef float evaluate(self, void *value, Py_ssize_t index):
        if self.noiseType == 'PERLIN':
            return calculatePerlin4D(self, <Vector3*>value)
        if self.noiseType == 'PERIODIC_PERLIN':
            return calculatePeriodicPerlin4D(self, <Vector3*>value)
        if self.noiseType == 'SIMPLEX':
            return calculateSimplex4D(self, <Vector3*>value)

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                           Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        if self.noiseType == 'PERLIN':
            for i in range(amount):
                target[i] = calculatePerlin4D(self, <Vector3*>values + i)
        if self.noiseType == 'PERIODIC_PERLIN':
            for i in range(amount):
                target[i] = calculatePeriodicPerlin4D(self, <Vector3*>values + i)
        if self.noiseType == 'SIMPLEX':
            for i in range(amount):
                target[i] = calculateSimplex4D(self, <Vector3*>values + i)

cdef inline float calculatePerlin4D(Noise4DFalloff self, Vector3 *v):
    cdef float x, y, z, w
    x = (v.x * self.frequency) + self.offset.x
    y = (v.y * self.frequency) + self.offset.y
    z = (v.z * self.frequency) + self.offset.z
    return fPerlin4D(x, y, z, self.w, self.octaves) * self.amplitude

cdef inline float calculatePeriodicPerlin4D(Noise4DFalloff self, Vector3 *v):
    cdef float x, y, z, w
    x = (v.x * self.frequency) + self.offset.x
    y = (v.y * self.frequency) + self.offset.y
    z = (v.z * self.frequency) + self.offset.z
    return fPeriodicPerlin4D(x, y, z, self.w, self.px, self.py, self.pz, self.pw, self.octaves) * self.amplitude

cdef inline float calculateSimplex4D(Noise4DFalloff self, Vector3 *v):
    cdef float x, y, z, w
    x = (v.x * self.frequency) + self.offset.x
    y = (v.y * self.frequency) + self.offset.y
    z = (v.z * self.frequency) + self.offset.z
    return fSimplex4D(x, y, z, self.w, self.octaves) * self.amplitude
