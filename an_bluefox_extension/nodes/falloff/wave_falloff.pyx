import bpy
cimport cython
from bpy.props import *
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from animation_nodes . utils.clamp cimport clampLong
from libc.math cimport M_PI, asin, atan
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures cimport BaseFalloff
from animation_nodes . math cimport Vector3, setVector3, distanceVec3, sin, tan
from animation_nodes . math cimport signedDistancePointToPlane_Normalized as signedDistance

WaveTypeItems = [
    ("SINE", "Sine", "Sine wave", "", 0),
    ("SQUARE", "Square", "Square wave", "", 1),
    ("TRIANGULAR", "Triangular", "Triangular wave", "", 2),
    ("SAW", "Saw", "saw wave", "", 3)
]

FalloffTypeItems = [
    ("POINT", "Point", "Point distance based wave", "", 0),
    ("DIRECTIONAL", "Directional", "Direction based wave", "", 1),
    ("INDEX", "Index", "Index based wave", "", 2),
    ("MESH", "Mesh", "Mesh distance based wave", "", 3)
]

class BF_WaveFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_wavefalloff"
    bl_label = "Wave falloff"
    errorHandlingType = "EXCEPTION"

    __annotations__ = {}
    __annotations__["waveType"] = EnumProperty(name = "Wave Type", default = "SINE",
        items = WaveTypeItems, update = AnimationNode.refresh)
    __annotations__["falloffType"] = EnumProperty(name = "Falloff Type", default = "POINT",
        items = FalloffTypeItems, update = AnimationNode.refresh)

    def create(self):
        if self.falloffType == "POINT":
            self.newInput("Vector", "Origin", "origin")
        elif self.falloffType == "DIRECTIONAL":
            self.newInput("Vector", "Origin", "origin")
            self.newInput("Vector", "Direction", "direction", value = (1, 0, 0))
            self.newInput("Float", "Size", "size", value = 2.0)
        elif self.falloffType == "INDEX":
            self.newInput("Integer", "Index", "index", value = 0)
            self.newInput("Integer", "Amount", "amount", value = 10, minValue = 0)
        elif self.falloffType == "MESH":
            self.newInput("Mesh", "Mesh", "mesh")
            self.newInput("Float", "Max Distance", "bvhMaxDistance", minValue = 0, value = 1e6, hide = True)
            self.newInput("Float", "Epsilon", "epsilon", minValue = 0, hide = True)
        self.newInput("Float", "Frequency", "frequency", value = 1)
        self.newInput("Float", "Offset", "offset", value = 0)
        self.newInput("Float", "Amplitude", "amplitude", value = 1)
        self.newInput("Float", "Damping", "damping")

        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        layout.prop(self, "falloffType", text = "")
        layout.prop(self, "waveType", text = "")

    def getExecutionFunctionName(self):
        if self.falloffType == "POINT":
            return "executePoint"
        elif self.falloffType == "DIRECTIONAL":
            return "executeDirectional"
        elif self.falloffType == "INDEX":
            return "executeIndex"
        elif self.falloffType == "MESH":
            return "executeMesh"

    def executePoint(self, origin, frequency, offset, amplitude, damping):
        return WavePointFalloff(origin, frequency, offset, amplitude, damping, self.waveType)

    def executeDirectional(self, origin, direction, size, frequency, offset, amplitude, damping):
        return WaveDirectionalFalloff(origin, direction, size, frequency, offset, amplitude, damping, self.waveType)

    def executeIndex(self, index, amount, frequency, offset, amplitude, damping):
        return WaveIndexFalloff(index, index + amount - 1, frequency, offset, amplitude, damping, self.waveType)

    def executeMesh(self, mesh, bvhMaxDistance, epsilon, frequency, offset, amplitude, damping):
        vectorList, polygonsIndices = self.validMesh(mesh)
        bvhTree = BVHTree.FromPolygons(vectorList, polygonsIndices, epsilon = max(epsilon, 0))

        return WaveMeshFalloff(bvhTree, bvhMaxDistance, frequency, offset, amplitude, damping, self.waveType)

    def validMesh(self, mesh):
        vectorList = mesh.vertices
        if len(vectorList) == 0:
            self.raiseErrorMessage("Invalid Mesh.")

        polygonsIndices = mesh.polygons
        if len(polygonsIndices.indices) == 0:
            self.raiseErrorMessage("Invalid Mesh.")

        return vectorList, polygonsIndices

################################## Point Distance based falloff ##################################

cdef class WavePointFalloff(BaseFalloff):
    cdef:
        float frequency, offset, amplitude, damping
        str waveType
        Vector3 origin

    def __cinit__(self, origin, frequency, offset, amplitude, damping, waveType):
        self.frequency = frequency
        self.offset = offset
        self.amplitude = amplitude
        self.damping = damping
        self.waveType = waveType
        self.clamped = True
        setVector3(&self.origin, origin)
        self.dataType = "LOCATION"

    @cython.cdivision(True)
    cdef float evaluate(self, void *object, Py_ssize_t index):
        cdef float influence = distanceVec3(<Vector3*>object, &self.origin)
        return wave(influence, self.frequency, self.offset, self.amplitude, self.damping, self.waveType)

################################## Direction based falloff ##################################

cdef class WaveDirectionalFalloff(BaseFalloff):
    cdef:
        float frequency, offset, amplitude, damping, size
        str waveType
        Vector3 origin, direction

    def __cinit__(self, origin, direction, size, frequency, offset, amplitude, damping, waveType):
        self.size = size
        self.frequency = frequency
        self.offset = offset
        self.amplitude = amplitude
        self.damping = damping
        self.waveType = waveType
        self.clamped = True
        setVector3(&self.origin, origin)
        setVector3(&self.direction, direction)
        self.dataType = "LOCATION"

    @cython.cdivision(True)
    cdef float evaluate(self, void *object, Py_ssize_t index):
        cdef float distance = signedDistance(&self.origin, &self.direction, <Vector3*>object)
        cdef float influence = 1 - distance / self.size
        influence = max(min(influence, 1), 0)

        return wave(influence, self.frequency, self.offset, self.amplitude, self.damping, self.waveType)

################################## Index based falloff ##################################

cdef class WaveIndexFalloff(BaseFalloff):
    cdef:
        long index, amount
        float indexDiff
        float frequency, offset, amplitude, damping
        str waveType

    def __cinit__(self, index, amount, frequency, offset, amplitude, damping, waveType):
        self.index = clampLong(index)
        self.amount = clampLong(amount)
        self.indexDiff = <float>(self.amount - self.index)
        self.frequency = frequency
        self.offset = offset
        self.amplitude = amplitude
        self.damping = damping
        self.waveType = waveType
        self.clamped = True
        self.dataType = "NONE"

    @cython.cdivision(True)
    cdef float evaluate(self, void *object, Py_ssize_t index):
        cdef float influence
        if index <= self.index:
            influence = 0
        if index >= self.amount:
            influence = 1
        else:
            influence = <float>(index - self.index) / self.indexDiff

        return wave(influence, self.frequency, self.offset, self.amplitude, self.damping, self.waveType)

################################## Mesh Distance based falloff ##################################

cdef class WaveMeshFalloff(BaseFalloff):
    cdef:
        bvhTree
        double bvhMaxDistance
        float frequency, offset, amplitude, damping
        str waveType
        Vector3 origin

    def __cinit__(self, bvhTree, bvhMaxDistance, frequency, offset, amplitude, damping, waveType):
        self.bvhTree = bvhTree
        self.bvhMaxDistance = bvhMaxDistance
        self.frequency = frequency
        self.offset = offset
        self.amplitude = amplitude
        self.damping = damping
        self.waveType = waveType
        self.clamped = True
        self.dataType = "LOCATION"

    @cython.cdivision(True)
    cdef float evaluate(self, void *object, Py_ssize_t index):
        cdef float influence
        cdef Vector3* v = <Vector3*>object
        influence = self.bvhTree.find_nearest(Vector((v.x, v.y, v.z)), self.bvhMaxDistance)[3]

        return wave(influence, self.frequency, self.offset, self.amplitude, self.damping, self.waveType)

################################## Wave Function ##################################

@cython.cdivision(True)
cdef float wave(float influence, float frequency, float offset, float amplitude, float damping, str waveType):
    cdef float temp
    cdef float result = 0
    frequency *= -1

    if waveType == "SINE":
        result = sin(2 * M_PI * influence * frequency + offset)
    elif waveType == "SQUARE":
        temp = sin(2 * M_PI * influence * frequency + offset)
        if temp < 0:
            result = -1
        else:
            result = 1
    elif waveType == "TRIANGULAR":
        temp = asin(sin((2 * M_PI * influence * frequency) + offset)) # ranges b/w -pi/2 and pi/2
        result = (temp / M_PI + 0.5) * 2 - 1 # make range -1 to 1
    elif waveType == "SAW":
        result = 2 / M_PI * atan(1 / tan(influence * frequency * M_PI + offset))

    return result * amplitude * 2.71827 ** -(damping * influence)
