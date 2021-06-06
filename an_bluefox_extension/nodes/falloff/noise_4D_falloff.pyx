import bpy
from bpy.props import *
from animation_nodes . math cimport Vector3, toVector3
from animation_nodes . base_types import AnimationNode
from ... libs . noise cimport fractalNoise, fractalPNoise
from animation_nodes . data_structures cimport BaseFalloff

class BF_Noise4DFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_Noise4DFalloffNode"
    bl_label = "Noise 4D Falloff"

    __annotations__ = {}
    __annotations__["periodic"] = BoolProperty(update = AnimationNode.refresh)

    def create(self):
        self.newInput("Float", "W", "w")
        self.newInput("Float", "Amplitude", "amplitude", value = 1)
        self.newInput("Float", "Frequency", "frequency", value = 0.1)
        self.newInput("Vector", "Offset", "offset")
        self.newInput("Integer", "Octaves", "octaves", value = 1, minValue = 1, maxValue = 16)
        if self.periodic:
            self.newInput("Integer", "PX", "px", value = 1, minValue = 1)
            self.newInput("Integer", "PY", "py", value = 1, minValue = 1)
            self.newInput("Integer", "PZ", "pz", value = 1, minValue = 1)
            self.newInput("Integer", "PW", "pw", value = 1, minValue = 1)
        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        layout.prop(self, "periodic", text = "Periodic")

    def getExecutionFunctionName(self):
        if self.periodic:
            return "execute_Periodic_Perlin"
        return "execute_Perlin"

    def execute_Perlin(self, w, amplitude, frequency, offset, octaves):
        return Noise4DFalloff(w, 1, 1, 1, 1, amplitude, frequency, offset, octaves, self.periodic)

    def execute_Periodic_Perlin(self, w, amplitude, frequency, offset, octaves, px, py, pz, pw):
        return Noise4DFalloff(w, px, py, pz, pw, amplitude, frequency, offset, octaves, self.periodic)

cdef class Noise4DFalloff(BaseFalloff):
    cdef:
        float w, amplitude, frequency
        Vector3 offset
        int octaves, px, py, pz, pw
        bint periodic

    def __cinit__(self, w, px, py, pz, pw, amplitude, frequency, offset, octaves, periodic):
        self.w = w
        self.px = max(abs(px), 1)
        self.py = max(abs(py), 1)
        self.pz = max(abs(pz), 1)
        self.pw = max(abs(pw), 1)
        self.amplitude = amplitude
        self.frequency = frequency
        self.offset = toVector3(offset)
        self.octaves = octaves
        self.periodic = periodic

        self.dataType = "LOCATION"

    cdef float evaluate(self, void *value, Py_ssize_t index):
        cdef Vector3* v = <Vector3*>value
        v.x += self.offset.x
        v.y += self.offset.y
        v.z += self.offset.z

        if self.periodic:
            return fractalPNoise(v, self.w,
                        self.px, self.py, self.pz, self.pw,
                        self.amplitude, self.frequency, self.octaves)
        return fractalNoise(v, self.w,
                    self.amplitude, self.frequency, self.octaves)

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                           Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef Vector3* v

        if self.periodic:
            for i in range(amount):
                v = <Vector3*>values + i
                v.x += self.offset.x
                v.y += self.offset.y
                v.z += self.offset.z
                target[i] = fractalPNoise(v, self.w,
                                self.px, self.py, self.pz, self.pw,
                                self.amplitude, self.frequency, self.octaves)
        else:
            for i in range(amount):
                v = <Vector3*>values + i
                v.x += self.offset.x
                v.y += self.offset.y
                v.z += self.offset.z
                target[i] = fractalNoise(v, self.w,
                                self.amplitude, self.frequency, self.octaves)
