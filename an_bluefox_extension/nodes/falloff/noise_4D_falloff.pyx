import bpy
from ... libs . noise import Noise4DNodeBase
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures cimport BaseFalloff
from animation_nodes . math cimport Vector3, Vector4, toVector3
from ... libs . noise cimport perlin4D_Single, periodicPerlin4D_Single, voronoi4D_Single

class BF_Noise4DFalloffNode(bpy.types.Node, AnimationNode, Noise4DNodeBase):
    bl_idname = "an_bf_Noise4DFalloffNode"
    bl_label = "Noise 4D Falloff"

    def create(self):
        self.newInput("Float", "W", "w")
        self.createInputs()
        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        self.drawNoiseSettings(layout)

    def getExecutionFunctionName(self):
        if self.noiseType == 'PERLIN':
            return "execute_Perlin"
        elif self.noiseType == 'PERIODIC_PERLIN':
            return "execute_Periodic_Perlin"
        elif self.noiseType == 'VORONOI':
            return "execute_Voronoi"

    def execute_Perlin(self, w, amplitude, frequency, offset, octaves, lacunarity, persistance):
        return Perlin4DFalloff(w, amplitude, frequency, offset, octaves, lacunarity, persistance)

    def execute_Periodic_Perlin(self, w, amplitude, frequency, offset, octaves, lacunarity, persistance, px, py, pz, pw):
        return PeriodicPerlin4DFalloff(w, px, py, pz, pw, amplitude, frequency, offset, octaves, lacunarity, persistance)

    def execute_Voronoi(self, w, amplitude, frequency, offset, randomness, exponent):
        return Voronoi4DFalloff(w, amplitude, frequency, offset, randomness, exponent, self.distanceMethod)

cdef class Perlin4DFalloff(BaseFalloff):
    cdef:
        float w, amplitude, frequency, lacunarity, persistance
        Vector3 offset
        int octaves

    def __cinit__(self, w, amplitude, frequency, offset, octaves, lacunarity, persistance):
        self.w = w
        self.amplitude = amplitude
        self.frequency = frequency
        self.offset = toVector3(offset)
        self.octaves = octaves
        self.lacunarity = lacunarity
        self.persistance = persistance

        self.dataType = "LOCATION"

    cdef float evaluate(self, void *value, Py_ssize_t index):
        cdef Vector3* _v = <Vector3*>value
        return perlin4D_Single(_v, self.w, self.amplitude, self.frequency, self.offset, self.octaves, self.lacunarity, self.persistance)

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                           Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef Vector3* _v
        for i in range(amount):
            _v = <Vector3*>values + i
            target[i] = perlin4D_Single(_v, self.w, self.amplitude, self.frequency, self.offset, self.octaves, self.lacunarity, self.persistance)

cdef class PeriodicPerlin4DFalloff(BaseFalloff):
    cdef:
        float w, amplitude, frequency, lacunarity, persistance
        Vector3 offset
        int octaves, px, py, pz, pw

    def __cinit__(self, w, px, py, pz, pw, amplitude, frequency, offset, octaves, lacunarity, persistance):
        self.w = w
        self.px = max(abs(px), 1)
        self.py = max(abs(py), 1)
        self.pz = max(abs(pz), 1)
        self.pw = max(abs(pw), 1)
        self.amplitude = amplitude
        self.frequency = frequency
        self.offset = toVector3(offset)
        self.octaves = octaves
        self.lacunarity = lacunarity
        self.persistance = persistance

        self.dataType = "LOCATION"

    cdef float evaluate(self, void *value, Py_ssize_t index):
        cdef Vector3* _v = <Vector3*>value
        return periodicPerlin4D_Single(_v,
                                       self.w,
                                       self.px,
                                       self.py,
                                       self.pz,
                                       self.pw,
                                       self.amplitude,
                                       self.frequency,
                                       self.offset,
                                       self.octaves,
                                       self.lacunarity,
                                       self.persistance)

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                           Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef Vector3* _v

        for i in range(amount):
            _v = <Vector3*>values + i
            target[i] = periodicPerlin4D_Single(_v,
                                                self.w,
                                                self.px,
                                                self.py,
                                                self.pz,
                                                self.pw,
                                                self.amplitude,
                                                self.frequency,
                                                self.offset,
                                                self.octaves,
                                                self.lacunarity,
                                                self.persistance)

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
        return voronoi4D_Single(_v,
                                self.w,
                                self.amplitude,
                                self.frequency,
                                self.offset,
                                self.randomness,
                                self.exponent,
                                self.distanceMethod)

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                           Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef Vector3* _v
        for i in range(amount):
            _v = <Vector3*>values + i
            target[i] = voronoi4D_Single(_v,
                                         self.w,
                                         self.amplitude,
                                         self.frequency,
                                         self.offset,
                                         self.randomness,
                                         self.exponent,
                                         self.distanceMethod)
