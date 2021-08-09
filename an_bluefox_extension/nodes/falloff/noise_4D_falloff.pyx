import bpy
from ... libs . noise import Noise4DNodeBase
from animation_nodes . math cimport Vector3, Vector4
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures cimport BaseFalloff
from ... libs . noise cimport perlin4D_Single, periodicPerlin4D_Single, voronoi4D_Single

class BF_Noise4DFalloffNode(bpy.types.Node, AnimationNode, Noise4DNodeBase):
    bl_idname = "an_bf_Noise4DFalloffNode"
    bl_label = "Noise 4D Falloff"

    def create(self):
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
        return PeriodicPerlin4DFalloff(w, amplitude, frequency, offset, octaves, lacunarity, persistance, px, py, pz, pw)

    def execute_Voronoi(self, w, amplitude, frequency, offset, randomness):
        return Voronoi4DFalloff(w, amplitude, frequency, offset, randomness, self.distanceMethod)

cdef class Perlin4DFalloff(BaseFalloff):
    cdef:
        float w, amplitude, frequency, lacunarity, persistance
        Vector4 offset
        int octaves

    def __cinit__(self, w, amplitude, frequency, offset, octaves, lacunarity, persistance):
        self.w = w
        self.amplitude = amplitude
        self.frequency = frequency
        self.offset = Vector4(offset.x, offset.y, offset.z, w)
        self.octaves = octaves
        self.lacunarity = lacunarity
        self.persistance = persistance

        self.dataType = "LOCATION"

    cdef float evaluate(self, void *value, Py_ssize_t index):
        return perlin4D_Single(<Vector3*>value,
                               self.amplitude,
                               self.frequency,
                               self.offset,
                               self.octaves,
                               self.lacunarity,
                               self.persistance)

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                           Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        for i in range(amount):
            target[i] = perlin4D_Single(<Vector3*>values + i,
                                        self.amplitude,
                                        self.frequency,
                                        self.offset,
                                        self.octaves,
                                        self.lacunarity,
                                        self.persistance)

cdef class PeriodicPerlin4DFalloff(BaseFalloff):
    cdef:
        float w, amplitude, frequency, lacunarity, persistance
        Vector4 offset
        int octaves, px, py, pz, pw
        int[4] period

    def __cinit__(self, w, amplitude, frequency, offset, octaves, lacunarity, persistance, px, py, pz, pw):
        self.w = w
        self.amplitude = amplitude
        self.frequency = frequency
        self.offset = Vector4(offset.x, offset.y, offset.z, w)
        self.octaves = octaves
        self.lacunarity = lacunarity
        self.persistance = persistance
        self.period[0] = max(abs(px), 1)
        self.period[1] = max(abs(py), 1)
        self.period[2] = max(abs(pz), 1)
        self.period[3] = max(abs(pw), 1)

        self.dataType = "LOCATION"

    cdef float evaluate(self, void *value, Py_ssize_t index):
        return periodicPerlin4D_Single(<Vector3*>value,
                                       self.period,
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
            target[i] = periodicPerlin4D_Single(<Vector3*>values + i,
                                                self.period,
                                                self.amplitude,
                                                self.frequency,
                                                self.offset,
                                                self.octaves,
                                                self.lacunarity,
                                                self.persistance)

cdef class Voronoi4DFalloff(BaseFalloff):
    cdef:
        float w, amplitude, frequency, randomness
        Vector4 offset
        str distanceMethod

    def __cinit__(self, w, amplitude, frequency, offset, randomness, distanceMethod):
        self.w = w
        self.amplitude = amplitude
        self.frequency = frequency
        self.offset = Vector4(offset.x, offset.y, offset.z, w)
        self.randomness = randomness
        self.distanceMethod = distanceMethod

        self.dataType = "LOCATION"

    cdef float evaluate(self, void *value, Py_ssize_t index):
        return voronoi4D_Single(<Vector3*>value,
                                self.amplitude,
                                self.frequency,
                                self.offset,
                                self.randomness,
                                self.distanceMethod)

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                           Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        for i in range(amount):
            target[i] = voronoi4D_Single(<Vector3*>values + i,
                                         self.amplitude,
                                         self.frequency,
                                         self.offset,
                                         self.randomness,
                                         self.distanceMethod)
