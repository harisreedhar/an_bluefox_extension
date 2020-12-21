import bpy
from bpy.props import *
from animation_nodes . base_types import AnimationNode
from . c_utils import stretchDeform, bendDeform, taperDeform, twistDeform
from animation_nodes . nodes . vector . c_utils import calculateVectorLengths

DeformTypeItems = [
    ("BEND", "Bend", "", "", 0),
    ("STRETCH", "Stretch", "", "", 1),
    ("TAPER", "Taper", "", "", 2),
    ("TWIST", "Twist", "", "", 3)
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
        self.newInput("Vector List", "Vertices", "verticesIn")
        self.newInput("Matrix", "Matrix", "matrix")
        self.newInput("Float", "Factor", "factor", value = 0)
        self.newInput("Falloff", "falloff", "falloff")
        self.newOutput("Vector List", "Vertices", "vertices")

    def draw(self, layout):
        layout.prop(self, "deformType", text = "")
        col = layout.column()
        col.row().prop(self, "axis", expand = True)

    def execute(self, verticesIn, matrix, factor, falloff):
        vertices = verticesIn.copy()
        if len(vertices) == 0:
            return vertices

        strengths = self.getFalloffStrengths(falloff, vertices)
        vertices.transform(matrix.inverted_safe())

        if self.deformType == "BEND":
            vertices = bendDeform(vertices, strengths, factor, axis = self.axis)
        elif self.deformType == "STRETCH":
            vertices = stretchDeform(vertices, strengths, factor, axis = self.axis)
        elif self.deformType == "TAPER":
            vertices = taperDeform(vertices, strengths, factor, axis = self.axis)
        elif self.deformType == "TWIST":
            vertices = twistDeform(vertices, strengths, factor, axis = self.axis)

        vertices.transform(matrix)
        return vertices

    def getFalloffStrengths(self, falloff, vectors):
        try:
            falloffEvaluator = falloff.getEvaluator("LOCATION")
            strengths = falloffEvaluator.evaluateList(vectors)
            return strengths
        except:
            self.raiseErrorMessage("This falloff cannot be evaluated for vectors")
