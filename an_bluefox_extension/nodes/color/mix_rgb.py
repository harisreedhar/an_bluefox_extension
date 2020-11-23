import bpy
from bpy.props import *
from . c_utils import colorMixList
from animation_nodes . base_types import AnimationNode, VectorizedSocket
from animation_nodes . events import executionCodeChanged, propertyChanged
from animation_nodes . data_structures import(
    Color, ColorList,
    VirtualColorList,
    VirtualDoubleList,
    DoubleList
)

colormodeItems = [
    ("MIX", "Mix", "Mix", "", 0),
    ("DARKEN", "Darken", "Darken", "", 1),
    ("MULTIPLY", "Multiply", "Multiply", "", 2),
    ("COLORBURN", "Color Burn", "colorburn", "", 3),
    ("LINEARBURN", "Linear Burn", "linearburn", "", 4),
    ("LIGHTEN", "Lighten", "Lighten", "", 5),
    ("SCREEN", "Screen", "Screen", "", 6),
    ("COLORDODGE", "Color Dodge", "colordodge", "", 7),
    ("ADD", "Add", "Add", "", 8),
    ("OVERLAY", "Overlay", "Overlay", "", 9),
    ("SOFTLIGHT", "Soft Light", "softlight", "", 10),
    ("HARDLIGHT", "Hard Light", "hardlight", "", 11),
    ("LINEARLIGHT", "Linear Light", "linearlight", "", 12),
    ("HARDMIX", "Hard Mix", "hardmix", "", 13),
    ("DIFFERENCE", "Difference", "difference", "", 14),
    ("SUBTRACT", "Subtract", "subtract", "", 15),
    ("DIVIDE", "Divide", "divide", "", 16)
]

class BF_MixRGBNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_MixRGB"
    bl_label = "Mix RGB"
    errorHandlingType = "EXCEPTION"

    mode: EnumProperty(name = "Blending Mode", default = "MIX",
        items = colormodeItems, update = AnimationNode.refresh)

    clamp: BoolProperty(name = "Clamp", default = True, update = propertyChanged)

    usecolor1List: VectorizedSocket.newProperty()
    usecolor2List: VectorizedSocket.newProperty()
    usefactorList: VectorizedSocket.newProperty()

    def create(self):
        self.newInput(VectorizedSocket("Float", "usefactorList",
            ("Factor", "factor"), ("Factors", "factors")))
        self.newInput(VectorizedSocket("Color", "usecolor1List",
            ("Color1", "colors1"), ("Colors1", "colors1")))
        self.newInput(VectorizedSocket("Color", "usecolor2List",
            ("Color2", "colors2"), ("Colors2", "colors2")))

        if any([self.usecolor1List, self.usecolor2List, self.usefactorList]):
            self.newOutput("Color List", "Colors", "colors")
        else:
            self.newOutput("Color", "Color", "color")

    def draw(self, layout):
        layout.prop(self, "mode", text = "")
        layout.prop(self, "clamp")

    def execute(self, factors, colors1, colors2):
        if not self.usecolor1List: colors1 = ColorList.fromValues([colors1])
        if not self.usecolor2List: colors2 = ColorList.fromValues([colors2])
        if not self.usefactorList: factors = DoubleList.fromValues([factors])

        default = Color((0.5, 0.5, 0.5, 1))
        a = VirtualColorList.create(colors1, default)
        b = VirtualColorList.create(colors2, default)
        f = VirtualDoubleList.create(factors, 0)

        mode = self.mode
        result = colorMixList(a, b, f, mode, clamp = self.clamp)

        if any([self.usecolor1List, self.usecolor2List, self.usefactorList]):
            return result
        else:
            return result[0]
