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
    ("CHEN", "Chen", "", "", 9),
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
            self.createFloatInputs(values=[10, 28, 2.6667])
        if self.chaoticModel == 'ROSSLER':
            self.createFloatInputs(values=[0.2, 0.2, 5.7])
        if self.chaoticModel == 'DEQUAN_LI':
            self.createFloatInputs(values=[40, 1.833, 0.16, 0.65, 55, 20])
        if self.chaoticModel == 'RIKITAKE':
            self.createFloatInputs(values=[5, 2])
        if self.chaoticModel == 'CHUA':
            self.createFloatInputs(values=[15.6, 28, -1.143, -0.714])
        if self.chaoticModel == 'HADLEY':
            self.createFloatInputs(values=[0.2, 4, 8, 1])
        if self.chaoticModel == 'AIZAWA':
            self.createFloatInputs(values=[0.95, 0.7, 0.6, 3.5])
        if self.chaoticModel == 'CHEN':
            self.createFloatInputs(values=[35, 2.6667, 28])
        if self.chaoticModel in ('WANG', 'NOSE_HOOVER'):
            self.createFloatInputs(values=[1, 1, 1])
        self.newInput("Float", "Scale", "scale", value = 1)

        self.newOutput("Vector List", "Vectors", "vectors")

    def createFloatInputs(self, values=[], number=6):
        name = self.chaoticModel.lower()
        sockets = []
        for i in range(number):
            charValue = chr(65 + i)
            inputName = f"{name}_param_{charValue}"
            socket = self.newInput("Float", f"Param {charValue}", inputName, value = 1, hide = True)
            sockets.append(socket)
        for i, value in enumerate(values):
            sockets[i].value = value
            sockets[i].hide = False

    def draw(self, layout):
        layout.prop(self, "chaoticModel", text = "")

    def execute(self, *args):
        chaoticModel = self.chaoticModel
        attractor = Lorenz(args)
        if chaoticModel == "ROSSLER":
            attractor = Rossler(args)
        elif chaoticModel == "DEQUAN_LI":
            attractor = DequanLi(args)
        elif chaoticModel == "RIKITAKE":
            attractor = Rikitake(args)
        elif chaoticModel == "CHUA":
            attractor = Chua(args)
        elif chaoticModel == "HADLEY":
            attractor = Hadley(args)
        elif chaoticModel == "AIZAWA":
            attractor = Aizawa(args)
        elif chaoticModel == "WANG":
            attractor = Wang(args)
        elif chaoticModel == "NOSE_HOOVER":
            attractor = NoseHoover(args)
        elif chaoticModel == "CHEN":
            attractor = Chen(args)
        vectors = attractor.generate()
        return vectors

cdef class AttractorBase:
    cdef Py_ssize_t iterations
    cdef float dt, x, y, z, paramA, paramB, paramC, paramD, paramE, paramF, scale

    def __cinit__(self, args):
        self.iterations = args[0]
        self.dt = args[1]
        self.x = args[2].x
        self.y = args[2].y
        self.z = args[2].z
        self.paramA = args[3]
        self.paramB = args[4]
        self.paramC = args[5]
        self.paramD = args[6]
        self.paramE = args[7]
        self.paramF = args[8]
        self.scale = args[9]

    cdef void attractor(self):
        pass

    cdef Vector3DList generate(self):
        cdef Vector3DList vectors = Vector3DList(length = self.iterations)
        for i in range(self.iterations):
            self.attractor()
            vectors.data[i].x = self.x * self.scale
            vectors.data[i].y = self.y * self.scale
            vectors.data[i].z = self.z * self.scale
        return vectors

cdef class Lorenz(AttractorBase):
    cdef void attractor(self):
        self.x += (self.paramA * (self.y - self.x)) * self.dt
        self.y += (self.paramB * self.x - self.y - self.x * self.z) * self.dt
        self.z += (self.x * self.y - self.paramC * self.z) * self.dt

cdef class Rossler(AttractorBase):
    cdef void attractor(self):
        self.x += -(self.y + self.z) * self.dt
        self.y += (self.x + self.paramA * self.y) * self.dt
        self.z += (self.paramB + self.z * (self.x - self.paramC)) * self.dt

cdef class DequanLi(AttractorBase):
    cdef void attractor(self):
        self.x += (self.paramA * (self.y - self.x) + self.paramC * self.x * self.z) * self.dt * 0.1
        self.y += (self.paramE * self.x + self.paramF * self.y - self.x * self.z) * self.dt * 0.1
        self.z += (self.paramB * self.z + self.x * self.y - self.paramD * self.x * self.x) * self.dt * 0.1

cdef class Rikitake(AttractorBase):
    cdef void attractor(self):
        self.x += (-self.paramB * self.x + self.z * self.y) * self.dt
        self.y += (-self.paramB * self.y + self.x * (self.z - self.paramA)) * self.dt
        self.z += (1 - self.x * self.y) * self.dt

cdef class Chua(AttractorBase):
    cdef void attractor(self):
        cdef float var = self.paramD * self.x + 0.5 * (self.paramC - self.paramD) * (fabs(self.x + 1) - fabs(self.x - 1))
        self.x += (self.paramA * (self.y - self.x - var)) * self.dt
        self.y += (self.x - self.y + self.z) * self.dt
        self.z += (-self.paramB * self.y) * self.dt

cdef class Hadley(AttractorBase):
    cdef void attractor(self):
        self.x += (-self.y**2 - self.z**2 - self.paramA * self.x + self.paramA * self.paramC) * self.dt
        self.y += (self.x * self.y - self.paramB * self.x * self.z - self.y + self.paramD) * self.dt
        self.z += (self.paramB * self.x * self.y + self.x * self.z - self.z) * self.dt

cdef class Aizawa(AttractorBase):
    cdef void attractor(self):
        self.x += ((self.z - self.paramB) * self.x - self.paramD * self.y) * self.dt
        self.y += (self.paramD * self.x + (self.z - self.paramB) * self.y) * self.dt
        self.z += (self.paramC + self.paramA * self.z - (self.z**3 / 3) - (self.x*self.x + self.y*self.y) *
                  (1 + 0.25 * self.z) + 0.1 * self.z * self.x**3) * self.dt

cdef class Wang(AttractorBase):
    cdef void attractor(self):
        self.x += (self.x - self.y * self.z) * self.paramA * self.dt
        self.y += (self.x - self.y + self.x * self.z) * self.paramB * self.dt
        self.z += (-3 * self.z + self.x * self.y) * self.paramC * self.dt

cdef class NoseHoover(AttractorBase):
    cdef void attractor(self):
        self.x += self.y * self.paramA * self.dt
        self.y += (self.y * self.z - self.x) * self.paramB * self.dt
        self.z += (1 - self.y * self.y) * self.paramC * self.dt

cdef class Chen(AttractorBase):
    cdef void attractor(self):
        self.x += self.paramA * (self.y - self.x) * self.dt * 0.1
        self.y += ((self.paramC - self.paramA) * self.x - self.x * self.z + self.paramC * self.y) * self.dt * 0.1
        self.z += (self.x * self.y - self.paramB * self.z) * self.dt * 0.1
