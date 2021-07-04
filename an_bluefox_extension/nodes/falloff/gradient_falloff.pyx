import bpy
from bpy.props import *
from mathutils import Matrix
from libc.math cimport M_2_PI
from libc.math cimport sqrt, atan2
from animation_nodes . events import propertyChanged
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures cimport BaseFalloff
from animation_nodes . math cimport Vector3, transformVec3AsPoint, Matrix4, setMatrix4

gradientTypeItems = [
    ("LINEAR", "Linear", "", "NONE", 0),
    ("QUADRATIC", "Quadratic", "", "NONE", 1),
    ("EASING", "Easing", "", "NONE", 2),
    ("DIAGONAL", "Diagonal", "", "NONE", 3),
    ("RADIAL", "Radial", "", "NONE", 4),
    ("QUADRATIC_SPHERE", "Quadratic Sphere", "", "NONE", 5),
    ("SPHERICAL", "Spherical", "", "NONE", 6),
]

class BF_GradientFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_GradientFalloffNode"
    bl_label = "Gradient Falloff"

    __annotations__ = {}

    __annotations__["gradientType"] = EnumProperty(name = "Gradient Type", default = "LINEAR",
        items = gradientTypeItems, update = propertyChanged)

    def create(self):
        self.newInput("Matrix", "Matrix", "matrix")
        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        layout.prop(self, "gradientType", text = "")

    def execute(self, matrix):
        invertedMatrix = matrix.inverted(Matrix.Identity(4))
        return GradientFalloff(invertedMatrix, self.gradientType)

cdef class GradientFalloff(BaseFalloff):
    cdef:
        Matrix4 origin
        str gradientType

    def __cinit__(self, origin, str gradientType):
        setMatrix4(&self.origin, origin)
        self.gradientType = gradientType
        self.dataType = "LOCATION"

    cdef float evaluate(self, void *value, Py_ssize_t index):
        cdef Vector3* v = <Vector3*>value
        if self.gradientType == 'LINEAR':
            return linear(self, v)
        elif self.gradientType == 'QUADRATIC':
            return quadratic(self, v)
        elif self.gradientType == 'EASING':
            return easing(self, v)
        elif self.gradientType == 'DIAGONAL':
            return diagonal(self, v)
        elif self.gradientType == 'RADIAL':
            return radial(self, v)
        elif self.gradientType == 'QUADRATIC_SPHERE':
            return quadraticSphere(self, v)
        elif self.gradientType == 'SPHERICAL':
            return spherical(self, v)

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                           Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        if self.gradientType == 'LINEAR':
            for i in range(amount):
                target[i] = linear(self, <Vector3*>values + i)
        elif self.gradientType == 'QUADRATIC':
            for i in range(amount):
                target[i] = quadratic(self, <Vector3*>values + i)
        elif self.gradientType == 'EASING':
            for i in range(amount):
                target[i] = easing(self, <Vector3*>values + i)
        elif self.gradientType == 'DIAGONAL':
            for i in range(amount):
                target[i] = diagonal(self, <Vector3*>values + i)
        elif self.gradientType == 'RADIAL':
            for i in range(amount):
                target[i] = radial(self, <Vector3*>values + i)
        elif self.gradientType == 'QUADRATIC_SPHERE':
            for i in range(amount):
                target[i] = quadraticSphere(self, <Vector3*>values + i)
        elif self.gradientType == 'SPHERICAL':
            for i in range(amount):
                target[i] = spherical(self, <Vector3*>values + i)

cdef float clampFloat(float value):
    return min(max(value, 0), 1)

cdef inline float linear(GradientFalloff self, Vector3 *v):
    cdef Vector3 p
    transformVec3AsPoint(&p, v, &self.origin)
    return clampFloat(p.x)

cdef inline float quadratic(GradientFalloff self, Vector3 *v):
    cdef Vector3 p
    transformVec3AsPoint(&p, v, &self.origin)
    cdef float r = max(p.x, 0)
    return clampFloat(r * r)

cdef inline float easing(GradientFalloff self, Vector3 *v):
    cdef Vector3 p
    transformVec3AsPoint(&p, v, &self.origin)
    cdef float r = min(max(p.x, 0), 1)
    cdef float t = r * r
    return clampFloat(3.0 * t - 2.0 * t * r)

cdef inline float diagonal(GradientFalloff self, Vector3 *v):
    cdef Vector3 p
    transformVec3AsPoint(&p, v, &self.origin)
    return clampFloat((p.x + p.y) * 0.5)

cdef inline float radial(GradientFalloff self, Vector3 *v):
    cdef Vector3 p
    transformVec3AsPoint(&p, v, &self.origin)
    return clampFloat(atan2(p.y, p.x) / M_2_PI + 0.5)

cdef inline float quadraticSphere(GradientFalloff self, Vector3 *v):
    cdef Vector3 p
    transformVec3AsPoint(&p, v, &self.origin)
    cdef float r = max(1.0 - sqrt(p.x * p.x + p.y * p.y + p.z * p.z), 0.0)
    return clampFloat(r * r)

cdef inline float spherical(GradientFalloff self, Vector3 *v):
    cdef Vector3 p
    transformVec3AsPoint(&p, v, &self.origin)
    cdef float r = max(1.0 - sqrt(p.x * p.x + p.y * p.y + p.z * p.z), 0.0)
    return clampFloat(r)
