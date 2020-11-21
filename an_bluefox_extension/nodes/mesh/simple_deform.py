import bpy
from bpy.props import *
from animation_nodes . base_types import AnimationNode
from . c_utils import stretchDeform, bendDeform, taperDeform, twistDeform
from animation_nodes . nodes . vector . c_utils import calculateVectorLengths

DeformTypeItems = [
    ("BEND", "Bend", "", "", 0),
    ("STRETCH", "Stretch", "", "", 1),
    ("TWIST", "Twist", "", "", 2),
    ("TAPER", "Taper", "", "", 3)
]

axisItems = [
    ("X", "X", "", "", 0),
    ("Y", "Y", "", "", 1),
    ("Z", "Z", "", "", 2)
]

class BF_SimpleDeformNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_SimpleDeformNode"
    bl_label = "Simple Deform"

    deformType: EnumProperty(name = "Deform Type", default = "BEND",
        items = DeformTypeItems, update = AnimationNode.refresh)

    axis: EnumProperty(name = "Axis", default = "Z",
        items = axisItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Vector List", "Vertices", "vertices", dataIsModified = True)
        self.newInput("Matrix", "Origin", "origin")
        self.newInput("Float", "Factor", "factor", value = 0)
        self.newOutput("Vector List", "Vertices", "vertices")

        if self.deformType in ("BEND", "TWIST"):
            self.inputs[-1].name = "Angle"

    def draw(self, layout):
        layout.prop(self, "deformType", text = "")
        col = layout.column()
        col.row().prop(self, "axis", expand = True)

    def execute(self, vertices, origin, factor):
        if len(vertices) == 0:
            return vertices

        vertices.transform(origin.inverted_safe())

        if self.deformType == "BEND":
            factor = self.getFactor(vertices, factor)
            vertices = bendDeform(vertices, factor, axis = self.axis)
        elif self.deformType == "STRETCH":
            vertices = stretchDeform(vertices, factor, axis = self.axis)
        elif self.deformType == "TAPER":
            vertices = taperDeform(vertices, factor, axis = self.axis)
        elif self.deformType == "TWIST":
            factor = self.getFactor(vertices, factor)
            vertices = twistDeform(vertices, factor, axis = self.axis)

        vertices.transform(origin)
        return vertices

    def getFactor(self, vertices, factor):
        length = calculateVectorLengths(vertices)
        maxValue = length.getMaxValue() + length.getMinValue() * 0.5
        if maxValue != 0:
            factor /= maxValue
        return factor
