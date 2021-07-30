import bpy
from bpy.props import *
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures cimport BaseFalloff
from animation_nodes . math cimport Vector3, Vector4, toVector3
from ... libs . noise cimport perlin4D_Single, periodicPerlin4D_Single, voronoi4D_Single

noiseTypeItems = [
    ("PERLIN", "Perlin", "", "", 0),
    ("PERIODIC_PERLIN", "Periodic Perlin", "", "", 1),
    ("VORONOI", "Voronoi", "", "", 2),
]

voronoiDistanceTypeItems = [
    ("EUCLIDEAN", "Euclidean", "", "", 0),
    ("MANHATTAN", "Manhattan", "", "", 1),
    ("CHEBYCHEV", "Chebychev", "", "", 2),
    ("MINKOWSKI", "Minkowski", "", "", 3),
]

class BF_Noise4DFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_Noise4DFalloffNode"
    bl_label = "Noise 4D Falloff"

    __annotations__ = {}
    __annotations__["noiseType"] = EnumProperty(name = "Noise Type", items = noiseTypeItems, update = AnimationNode.refresh)
    __annotations__["distanceMethod"] = EnumProperty(name = "Distance Method", items = voronoiDistanceTypeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Float", "W", "w")
        self.newInput("Float", "Amplitude", "amplitude", value = 1)
        self.newInput("Float", "Frequency", "frequency", value = 0.1)
        self.newInput("Vector", "Offset", "offset")

        if self.noiseType != 'VORONOI':
            self.newInput("Integer", "Octaves", "octaves", value = 1, minValue = 1, maxValue = 16)
        if self.noiseType == 'PERIODIC_PERLIN':
            self.newInput("Integer", "PX", "px", value = 1, minValue = 1)
            self.newInput("Integer", "PY", "py", value = 1, minValue = 1)
            self.newInput("Integer", "PZ", "pz", value = 1, minValue = 1)
            self.newInput("Integer", "PW", "pw", value = 1, minValue = 1)
        if self.noiseType == 'VORONOI':
            self.newInput("Float", "Randomness", "randomness", value = 1, minValue = 0, maxValue = 1)
            self.newInput("Float", "Exponent", "exponent", value = 2)

        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        layout.prop(self, "noiseType", text = "")
        if self.noiseType == 'VORONOI':
            layout.prop(self, "distanceMethod", text = "")

    def getExecutionFunctionName(self):
        if self.noiseType == 'PERLIN':
            return "execute_Perlin"
        elif self.noiseType == 'PERIODIC_PERLIN':
            return "execute_Periodic_Perlin"
        elif self.noiseType == 'VORONOI':
            return "execute_Voronoi"

    def execute_Perlin(self, w, amplitude, frequency, offset, octaves):
        return Perlin4DFalloff(w, amplitude, frequency, offset, octaves)

    def execute_Periodic_Perlin(self, w, amplitude, frequency, offset, octaves, px, py, pz, pw):
        return PeriodicPerlin4DFalloff(w, px, py, pz, pw, amplitude, frequency, offset, octaves)

    def execute_Voronoi(self, w, amplitude, frequency, offset, randomness, exponent):
        return Voronoi4DFalloff(w, amplitude, frequency, offset, randomness, exponent, self.distanceMethod)

cdef class Perlin4DFalloff(BaseFalloff):
    cdef:
        float w, amplitude, frequency
        Vector3 offset
        int octaves

    def __cinit__(self, w, amplitude, frequency, offset, octaves):
        self.w = w
        self.amplitude = amplitude
        self.frequency = frequency
        self.offset = toVector3(offset)
        self.octaves = octaves

        self.dataType = "LOCATION"

    cdef float evaluate(self, void *value, Py_ssize_t index):
        cdef Vector3* _v = <Vector3*>value
        cdef Vector3 v
        v.x = _v.x + self.offset.x
        v.y = _v.y + self.offset.y
        v.z = _v.z + self.offset.z
        return perlin4D_Single(&v, self.w, self.amplitude, self.frequency, self.octaves)

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                           Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef Vector3* _v
        cdef Vector3 v
        for i in range(amount):
            _v = <Vector3*>values + i
            v.x = _v.x + self.offset.x
            v.y = _v.y + self.offset.y
            v.z = _v.z + self.offset.z
            target[i] = perlin4D_Single(&v, self.w, self.amplitude, self.frequency, self.octaves)

cdef class PeriodicPerlin4DFalloff(BaseFalloff):
    cdef:
        float w, amplitude, frequency
        Vector3 offset
        int octaves, px, py, pz, pw

    def __cinit__(self, w, px, py, pz, pw, amplitude, frequency, offset, octaves):
        self.w = w
        self.px = max(abs(px), 1)
        self.py = max(abs(py), 1)
        self.pz = max(abs(pz), 1)
        self.pw = max(abs(pw), 1)
        self.amplitude = amplitude
        self.frequency = frequency
        self.offset = toVector3(offset)
        self.octaves = octaves

        self.dataType = "LOCATION"

    cdef float evaluate(self, void *value, Py_ssize_t index):
        cdef Vector3* _v = <Vector3*>value
        cdef Vector3 v
        v.x = _v.x + self.offset.x
        v.y = _v.y + self.offset.y
        v.z = _v.z + self.offset.z
        return periodicPerlin4D_Single(&v,
                                       self.w,
                                       self.px,
                                       self.py,
                                       self.pz,
                                       self.pw,
                                       self.amplitude,
                                       self.frequency,
                                       self.octaves)

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                           Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef Vector3* _v
        cdef Vector3 v

        for i in range(amount):
            _v = <Vector3*>values + i
            v.x = _v.x + self.offset.x
            v.y = _v.y + self.offset.y
            v.z = _v.z + self.offset.z
            target[i] = periodicPerlin4D_Single(&v,
                                                self.w,
                                                self.px,
                                                self.py,
                                                self.pz,
                                                self.pw,
                                                self.amplitude,
                                                self.frequency,
                                                self.octaves)

cdef class Voronoi4DFalloff(BaseFalloff):
    cdef:
        float w, amplitude, frequency, randomness, exponent
        Vector3 offset
        str distanceMethod

    def __cinit__(self, w, amplitude, frequency, offset, randomness, exponent, distanceMethod):
        self.w = w
        self.amplitude = amplitude
        self.frequency = frequency
        self.offset = toVector3(offset)
        self.randomness = randomness
        self.exponent = exponent
        self.distanceMethod = distanceMethod

        self.dataType = "LOCATION"

    cdef float evaluate(self, void *value, Py_ssize_t index):
        cdef Vector3* _v = <Vector3*>value
        cdef Vector3 point
        point.x = _v.x + self.offset.x
        point.y = _v.y + self.offset.y
        point.z = _v.z + self.offset.z
        return voronoi4D_Single(&point,
                                self.w,
                                self.amplitude,
                                self.frequency,
                                self.randomness,
                                self.exponent,
                                self.distanceMethod)

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                           Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef Vector3* _v
        cdef Vector3 point
        for i in range(amount):
            _v = <Vector3*>values + i
            point.x = _v.x + self.offset.x
            point.y = _v.y + self.offset.y
            point.z = _v.z + self.offset.z
            target[i] = voronoi4D_Single(&point,
                                         self.w,
                                         self.amplitude,
                                         self.frequency,
                                         self.randomness,
                                         self.exponent,
                                         self.distanceMethod)
