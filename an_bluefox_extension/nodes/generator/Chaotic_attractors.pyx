import bpy
from bpy.props import *
from mathutils import Vector
from libc . math cimport fabs
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures cimport Vector3DList

# http://www.3d-meier.de/
chaoticModelTypeItems = [
    ("LORENZ", "Lorenz", "", "", 0),
    ("ROSSLER", "Rossler", "", "", 1),
    ("DEQUAN_LI", "Dequan Li", "", "", 2),
    ("RIKITAKE", "Rikitake", "", "", 3),
    ("CHUA", "Chua", "", "", 4),
    ("HADLEY", "Hadley", "", "", 5),
    ("AIZAWA", "Aizawa", "", "", 6),
    ("WANG", "Wang", "", "", 7),
    ("NOSE_HOOVER", "Nose Hoover", "", "", 8),
]

class BF_ChaoticAttractorsNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_ChaoticAttractorsNode"
    bl_label = "Chaotic Attractors"
    errorHandlingType = "EXCEPTION"

    __annotations__ = {}

    __annotations__["chaoticModel"] = EnumProperty(name = "Chaotic Model",
        items = chaoticModelTypeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Integer", "Iterations", "iterations", value = 1, minValue = 1)
        self.newInput("Float", "Time Step", "dt", value = 0.01)
        self.newInput("Vector", "Intial Vector", "initialVector", value = Vector((0.1, 0, -0.1)))
        if self.chaoticModel == 'LORENZ':
            self.newInput("Float", "Param A", "paramA1", value = 10)
            self.newInput("Float", "Param B", "paramB1", value = 28)
            self.newInput("Float", "Param C", "paramC1", value = 2.6667)
            self.newInput("Float", "Param D", "paramD1", hide = True)
        if self.chaoticModel == 'ROSSLER':
            self.newInput("Float", "Param A", "paramA2", value = 0.2)
            self.newInput("Float", "Param B", "paramB2", value = 0.2)
            self.newInput("Float", "Param C", "paramC2", value = 5.7)
            self.newInput("Float", "Param D", "paramD2", hide = True)
        if self.chaoticModel == 'DEQUAN_LI':
            self.newInput("Float", "Param A", "paramA3", value = 40)
            self.newInput("Float", "Param B", "paramB3", value = 1.833)
            self.newInput("Float", "Param C", "paramC3", value = 0.16)
            self.newInput("Float", "Param D", "paramD3", value = 0.65)
        if self.chaoticModel == 'RIKITAKE':
            self.newInput("Float", "Param A", "paramA4", value = 5)
            self.newInput("Float", "Param B", "paramB4", value = 2)
            self.newInput("Float", "Param C", "paramC4", hide = True)
            self.newInput("Float", "Param D", "paramD4", hide = True)
        if self.chaoticModel == 'CHUA':
            self.newInput("Float", "Param A", "paramA5", value = 15.6)
            self.newInput("Float", "Param B", "paramB5", value = 28)
            self.newInput("Float", "Param C", "paramC5", value = -1.143)
            self.newInput("Float", "Param D", "paramD5", value = -0.714)
        if self.chaoticModel == 'HADLEY':
            self.newInput("Float", "Param A", "paramA6", value = 0.2)
            self.newInput("Float", "Param B", "paramB6", value = 4)
            self.newInput("Float", "Param C", "paramC6", value = 8)
            self.newInput("Float", "Param D", "paramD6", value = 1)
        if self.chaoticModel == 'AIZAWA':
            self.newInput("Float", "Param A", "paramA7", value = 0.95)
            self.newInput("Float", "Param B", "paramB7", value = 0.7)
            self.newInput("Float", "Param C", "paramC7", value = 0.6)
            self.newInput("Float", "Param D", "paramD7", value = 3.5)
        if self.chaoticModel in ('WANG', 'NOSE_HOOVER'):
            self.newInput("Float", "Param A", "paramA8", value = 1)
            self.newInput("Float", "Param B", "paramB8", value = 1)
            self.newInput("Float", "Param C", "paramC8", value = 1)
            self.newInput("Float", "Param D", "paramD8", hide = True)

        self.newInput("Float", "Scale", "scale", value = 1)

        self.newOutput("Vector List", "Vectors", "vectors")

    def draw(self, layout):
        layout.prop(self, "chaoticModel", text = "")

    def execute(self, iterations, dt, initialVector, paramA, paramB, paramC, paramD, scale):
        vectors = attractor(iterations, dt, initialVector,
                            paramA, paramB, paramC, paramD,
                            scale, self.chaoticModel)
        return vectors

cdef Vector3DList attractor(Py_ssize_t iterations,
                            float dt,
                            initialVector,
                            float paramA,
                            float paramB,
                            float paramC,
                            float paramD,
                            float scale,
                            str chaoticModel):

    cdef float x, y, z, var
    cdef Vector3DList vectors = Vector3DList(length = iterations)
    cdef Py_ssize_t i

    x = initialVector.x
    y = initialVector.y
    z = initialVector.z

    iterations = max(iterations, 1)

    if chaoticModel == "LORENZ":
        for i in range(iterations):
            x += (paramA * (y - x)) * dt
            y += (paramB * x - y - x * z) * dt
            z += (x * y - paramC * z) * dt
            vectors.data[i].x = x * scale
            vectors.data[i].y = y * scale
            vectors.data[i].z = z * scale

    elif chaoticModel == "ROSSLER":
        for i in range(iterations):
            x += -(y + z) * dt
            y += (x + paramA * y) * dt
            z += (paramB + z * (x - paramC)) * dt
            vectors.data[i].x = x * scale
            vectors.data[i].y = y * scale
            vectors.data[i].z = z * scale

    elif chaoticModel == "DEQUAN_LI":
        for i in range(iterations):
            x += (paramA * (y - x) + paramC * x * z) * dt * 0.1
            y += (55 * x + 20 * y - x * z) * dt * 0.1
            z += (paramB * z + x * y - paramD * x * x) * dt * 0.1
            vectors.data[i].x = x * scale
            vectors.data[i].y = y * scale
            vectors.data[i].z = z * scale

    elif chaoticModel == "RIKITAKE":
        for i in range(iterations):
            x += (-paramB * x + z * y) * dt
            y += (-paramB * y + x * (z - paramA)) * dt
            z += (1 - x * y) * dt
            vectors.data[i].x = x * scale
            vectors.data[i].y = y * scale
            vectors.data[i].z = z * scale

    elif chaoticModel == "CHUA":
        for i in range(iterations):
            var = paramD * x + 0.5 * (paramC - paramD) * (fabs(x + 1) - fabs(x - 1))
            x += (paramA * (y - x - var)) * dt
            y += (x - y + z) * dt
            z += (-paramB * y) * dt
            vectors.data[i].x = x * scale
            vectors.data[i].y = y * scale
            vectors.data[i].z = z * scale

    elif chaoticModel == "HADLEY":
        for i in range(iterations):
            x += (-y**2 - z**2 - paramA * x + paramA * paramC) * dt
            y += (x * y - paramB * x * z - y + paramD) * dt
            z += (paramB * x * y + x * z - z) * dt
            vectors.data[i].x = x * scale
            vectors.data[i].y = y * scale
            vectors.data[i].z = z * scale

    elif chaoticModel == "AIZAWA":
        for i in range(iterations):
            x += ((z - paramB) * x - paramD * y) * dt
            y += (paramD * x + (z - paramB) * y) * dt
            z += (paramC + paramA * z - (z**3 / 3) - (x*x + y*y) * (1 + 0.25 * z) + 0.1 * z * x**3) * dt
            vectors.data[i].x = x * scale
            vectors.data[i].y = y * scale
            vectors.data[i].z = z * scale

    elif chaoticModel == "WANG":
        for i in range(iterations):
            x += (x - y * z) * paramA * dt
            y += (x - y + x * z) * paramB * dt
            z += (-3 * z + x * y) * paramC * dt
            vectors.data[i].x = x * scale
            vectors.data[i].y = y * scale
            vectors.data[i].z = z * scale

    elif chaoticModel == "NOSE_HOOVER":
        for i in range(iterations):
            x += y * paramA * dt
            y += (y * z - x) * paramB * dt
            z += (1 - y * y) * paramC * dt
            vectors.data[i].x = x * scale
            vectors.data[i].y = y * scale
            vectors.data[i].z = z * scale

    return vectors
