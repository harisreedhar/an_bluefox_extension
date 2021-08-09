import bpy
from bpy.props import *
from libc . math cimport sin, cos
from animation_nodes . math cimport Vector3
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures cimport ColorList, Vector3DList, DoubleList

class BF_MagicColorsNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_MagicColorsNode"
    bl_label = "Magic Colors"

    __annotations__ = {}

    def create(self):
        self.newInput("Vector List", "Vectors", "vectors")
        self.newInput("Integer", "Depth", "depth", value = 2, minValue = 0)
        self.newInput("Float", "Scale", "scale", value = 0.25)
        self.newInput("Float", "Distortion", "distortion", value = 2)

        self.newOutput("Color List", "Colors", "colors")
        self.newOutput("Float List", "Values", "values")

    def execute(self, vectors, depth, scale, distortion):
        return magicColors(vectors, depth, scale, distortion)

def magicColors(Vector3DList vectors, Py_ssize_t n, float scale, float distortion):
    cdef Vector3 vector
    cdef float dist, x, y, z
    cdef float divisor = 1 / 3
    cdef Py_ssize_t i
    cdef Py_ssize_t amount = vectors.length
    cdef ColorList colors = ColorList(length = amount)
    cdef DoubleList values = DoubleList(length = amount)

    for i in range(amount):
        dist = distortion
        vector.x = vectors.data[i].x * scale
        vector.y = vectors.data[i].y * scale
        vector.z = vectors.data[i].z * scale

        x = sin((vector.x + vector.y + vector.z) * 5)
        y = cos((-vector.x + vector.y - vector.z) * 5)
        z = -cos((-vector.x - vector.y + vector.z) * 5)

        if n > 0:
            x *= dist
            y *= dist
            z *= dist
            y = -cos(x - y + z)
            y *= dist
            if n > 1:
                x = cos(x - y - z)
                x *= dist
                if n > 2:
                    z = sin(-x - y - z)
                    z *= dist
                    if n > 3:
                        x = -cos(-x + y - z)
                        x *= dist
                        if n > 4:
                            y = -sin(-x + y + z)
                            y *= dist
                            if n > 5:
                                y = -cos(-x + y + z)
                                y *= dist
                                if n > 6:
                                    x = cos(x + y + z)
                                    x *= dist
                                    if n > 7:
                                        z = sin(x + y - z)
                                        z *= dist
                                        if n > 8:
                                            x = -cos(-x - y + z)
                                            x *= dist
                                            if n > 9:
                                                y = -sin(x - y + z)
                                                y *= dist

        if dist != 0:
            dist *= 2
            x /= dist
            y /= dist
            z /= dist

        colors.data[i].r = 0.5 - x
        colors.data[i].g = 0.5 - y
        colors.data[i].b = 0.5 - z
        colors.data[i].a = 1

        values.data[i] = (colors.data[i].r + colors.data[i].g + colors.data[i].b) * divisor

    return colors, values
