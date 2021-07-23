import bpy
from bpy.props import *
from mathutils import Matrix
from libc.math cimport sqrt, pow, sin, cos, atan2
from animation_nodes . events import propertyChanged
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures cimport BaseFalloff
from animation_nodes . math cimport Vector3, transformVec3AsPoint, Matrix4, setMatrix4

class BF_MandelBulbFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_MandelBulbFalloffNode"
    bl_label = "Mandelbulb Falloff"

    def create(self):
        self.newInput("Matrix", "Origin", "origin", dataIsModified = True)
        self.newInput("Integer", "Iteration", "iteration", value = 5, minValue = 1)
        self.newInput("Float", "n", "n", value = 5)
        self.newInput("Float", "Power", "power", value = 3)
        self.newInput("Float", "Phase", "phase")
        self.newInput("Float", "Size", "size", value = 1)
        self.newInput("Float", "Falloff Width", "falloffWidth", value = 0.25)
        self.newOutput("Falloff", "Falloff", "falloff")

    def execute(self, origin, iteration, n, power, phase, size, falloffWidth,):
        invertedMatrix = origin.inverted(Matrix.Identity(4))
        return MandelBulbFalloff(invertedMatrix, iteration, n, size, falloffWidth, power, phase)

cdef class MandelBulbFalloff(BaseFalloff):
    cdef:
        Matrix4 origin
        float factor
        float minDistance, maxDistance
        float power, phase, n
        int iteration

    def __cinit__(self, origin, int iteration, float n, float size, float falloffWidth, float power, float phase):
        if falloffWidth < 0:
            size += falloffWidth
            falloffWidth = -falloffWidth
        self.minDistance = size
        self.maxDistance = size + falloffWidth
        self.power = power
        self.phase = phase
        self.iteration = iteration
        self.n = n

        if self.minDistance == self.maxDistance:
            self.minDistance -= 0.00001
        self.factor = 1 / (self.maxDistance - self.minDistance)
        setMatrix4(&self.origin, origin)

        self.dataType = "LOCATION"
        self.clamped = True

    cdef float evaluate(self, void *value, Py_ssize_t index):
        return calcShapeStrength(self, <Vector3*>value)

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                           Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        for i in range(amount):
            target[i] = calcShapeStrength(self, <Vector3*>values + i)

cdef inline float calcShapeStrength(MandelBulbFalloff self, Vector3 *v):
    cdef Vector3 p
    transformVec3AsPoint(&p, v, &self.origin)

    cdef int i
    cdef float n = self.n
    cdef float xxyy, ntheta, nphi, power, psint
    cdef float xxyyzz = 0
    cdef float x = p.x
    cdef float y = p.y
    cdef float z = p.z

    for i in range(self.iteration):
        xxyy = x*x + y*y
        xxyyzz = xxyy + z*z

        if xxyyzz > n:
            break

        ntheta = n * (atan2(sqrt(xxyy), z) + self.phase)
        nphi = n * atan2(y, x)
        power = (xxyyzz) ** self.power
        psint = power * sin(ntheta)

        x = psint * cos(nphi) + p.x
        y = psint * sin(nphi) + p.y
        z = power * cos(ntheta) + p.z

    if xxyyzz <= self.minDistance: return 1
    if xxyyzz <= self.maxDistance: return 1 - (xxyyzz - self.minDistance) * self.factor
    return 0
