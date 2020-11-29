import bpy
from bpy.props import *
from mathutils import Matrix
from libc.math cimport fabs, sqrt, pow
from animation_nodes . events import propertyChanged
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures cimport BaseFalloff
from animation_nodes . math cimport Vector3, transformVec3AsPoint, Matrix4, setMatrix4

shapeListItems = [
    ("CYLINDER", "Cylinder", "", "NONE", 0),
    ("CUBE", "Cube", "", "NONE", 1),
    ("CONE", "Cone", "", "NONE", 2),
    ("SQUAREPYRAMID", "Square Pyramid", "", "NONE", 3),
]

class BF_ShapeFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_ShapeFalloffNode"
    bl_label = "Shape Falloff"
    bl_width_default = 150

    __annotations__ = {}

    __annotations__["shapeType"] = EnumProperty(name = "Shape", default = "CYLINDER",
        items = shapeListItems, update = propertyChanged)

    def create(self):
        self.newInput("Matrix", "Origin", "origin", dataIsModified = True)
        self.newInput("Float", "Size", "size", value = 2)
        self.newInput("Float", "Falloff Width", "falloffWidth", value = 0)
        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        layout.prop(self, "shapeType", text = "")

    def execute(self, origin, size, falloffWidth):
        invertedMatrix = origin.inverted(Matrix.Identity(4))
        if self.shapeType == 'CUBE':
            size *= 2
        if self.shapeType == 'CONE':
            size *= 0.5
        return ShapeFalloff(invertedMatrix, size, falloffWidth, self.shapeType)

cdef class ShapeFalloff(BaseFalloff):
    cdef:
        Matrix4 origin
        float factor
        float minDistance, maxDistance
        str shape

    def __cinit__(self, origin, float size, float falloffWidth, str shape):
        if falloffWidth < 0:
            size += falloffWidth
            falloffWidth = -falloffWidth
        self.minDistance = size
        self.maxDistance = size + falloffWidth
        self.shape = shape

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

cdef inline float calcShapeStrength(ShapeFalloff self, Vector3 *v):
    cdef Vector3 p
    transformVec3AsPoint(&p, v, &self.origin)
    cdef float distance = 0
    cdef float sqxy, xyxy, ax, axy, _axy
    if self.shape == 'CYLINDER':
        sqxy = sqrt(p.x * p.x + p.y * p.y)
        distance = (fabs(sqxy - p.z) + fabs(sqxy + p.z))
    if self.shape == 'CUBE':
        xyxy = fabs(p.x - p.y) + fabs(p.x + p.y)
        distance = (fabs(xyxy - 2 * p.z) + fabs(xyxy + 2 * p.z))
    if self.shape == 'CONE':
        sqxy = sqrt(p.x * p.x + p.y * p.y)
        distance = (fabs(sqxy + 2 * p.z) + sqxy)
    if self.shape == 'SQUAREPYRAMID':
        axy = fabs(p.x + p.y)
        _axy = fabs(p.x - p.y)
        distance = (fabs(_axy + axy + 3 * p.z) + _axy + axy)

    if distance <= self.minDistance: return 1
    if distance <= self.maxDistance: return 1 - (distance - self.minDistance) * self.factor
    return 0
