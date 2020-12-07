import bpy
from bpy.props import *
from animation_nodes . base_types import AnimationNode
from libc.math cimport sin, cos, tan, asin, acos, atan, M_PI
from animation_nodes . data_structures cimport CompoundFalloff, Falloff

WaveTypeItems = [
    ("SINE", "Sine", "Sine wave", "", 0),
    ("SQUARE", "Square", "Square wave", "", 1),
    ("TRIANGULAR", "Triangular", "Triangular wave", "", 2),
    ("SAW", "Saw", "saw wave", "", 3)
]

class BF_WaveFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_wavefalloff"
    bl_label = "Wave Falloff"
    errorHandlingType = "EXCEPTION"

    __annotations__ = {}

    __annotations__["waveType"] = EnumProperty(name = "Wave Type", items = WaveTypeItems,
        default = "SINE", update = AnimationNode.refresh)

    def create(self):
        self.newInput("Falloff", "Falloff", "falloff", dataIsModified = True)
        self.newInput("Float", "Frequency", "frequency", value = 1)
        self.newInput("Float", "Offset", "offset", value = 0)
        self.newInput("Float", "Amplitude", "amplitude", value = 1)
        self.newInput("Float", "Damping", "damping")

        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        row = layout.row(align = True)
        row.prop(self, "waveType", text = "")

    def execute(self, falloff, frequency, offset, amplitude, damping):
        return WaveFalloffs(falloff, self.waveType, frequency, offset, amplitude, damping)

class WaveFalloffs:
    def __new__(cls, Falloff falloff not None, str method not None, float frequency, float offset, float amplitude, float damping):
        if method == "SINE": return SinWaveFalloff(falloff, frequency, offset, amplitude, damping)
        elif method == "SQUARE": return SquareWaveFalloff(falloff, frequency, offset, amplitude, damping)
        elif method == "TRIANGULAR": return TriangularWaveFalloff(falloff, frequency, offset, amplitude, damping)
        elif method == "SAW": return SawWaveFalloff(falloff, frequency, offset, amplitude, damping)

cdef class WaveFalloffBase(CompoundFalloff):
    cdef:
        Falloff falloff
        float frequency
        float offset
        float amplitude
        float damping

    def __cinit__(self, Falloff falloff, float frequency, float offset, float amplitude, float damping):
        self.falloff = falloff
        self.frequency = frequency
        self.offset = offset
        self.amplitude = amplitude
        self.damping = damping

    cdef list getDependencies(self):
        return [self.falloff]

cdef class SinWaveFalloff(WaveFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef float result = sin(2 * M_PI * dependencyResults[0] * self.frequency + self.offset)
        return result * self.amplitude * 2.71827 ** -(self.damping * dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float result = 0
        for i in range(amount):
            result = sin(2 * M_PI * a[i] * self.frequency + self.offset)
            target[i] = result * self.amplitude * 2.71827 ** -(self.damping * a[i])

cdef class SquareWaveFalloff(WaveFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef float result = sin(2 * M_PI * dependencyResults[0] * self.frequency + self.offset)
        if result < 0:
            result = -1
        else:
            result = 1
        return result * self.amplitude * 2.71827 ** -(self.damping * dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float result = 0
        for i in range(amount):
            result = sin(2 * M_PI * a[i] * self.frequency + self.offset)
            if result < 0:
                result = -1
            else:
                result = 1
            target[i] = result * self.amplitude * 2.71827 ** -(self.damping * a[i])

cdef class TriangularWaveFalloff(WaveFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef float result = asin(sin((2 * M_PI * dependencyResults[0] * self.frequency) + self.offset))
        result = (result / M_PI + 0.5) * 2 - 1
        return result * self.amplitude * 2.71827 ** -(self.damping * dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float result = 0
        for i in range(amount):
            result = asin(sin((2 * M_PI * a[i] * self.frequency) + self.offset))
            result = (result / M_PI + 0.5) * 2 - 1
            target[i] = result * self.amplitude * 2.71827 ** -(self.damping * a[i])

cdef class SawWaveFalloff(WaveFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef float result = 2 / M_PI * atan(1 / tan(dependencyResults[0] * self.frequency * M_PI + self.offset))
        return result * self.amplitude * 2.71827 ** -(self.damping * dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float result = 0
        for i in range(amount):
            result = 2 / M_PI * atan(1 / tan(a[i] * self.frequency * M_PI + self.offset))
            target[i] = result * self.amplitude * 2.71827 ** -(self.damping * a[i])
