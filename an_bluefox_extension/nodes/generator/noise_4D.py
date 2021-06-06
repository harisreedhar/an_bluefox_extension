import bpy
from bpy.props import *
from animation_nodes . base_types import AnimationNode, VectorizedSocket

class BF_Noise4DNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_Noise4DNode"
    bl_label = "Noise 4D"

    useWList: VectorizedSocket.newProperty()
    periodic: BoolProperty(update = AnimationNode.refresh)

    def create(self):
        self.newInput("Vector List", "Vectors", "vectors", dataIsModified = True)
        self.newInput(VectorizedSocket("Float", "useWList",
            ("W", "w"), ("Ws", "w")))
        self.newInput("Float", "Amplitude", "amplitude", value = 1)
        self.newInput("Float", "Frequency", "frequency", value = 0.1)
        self.newInput("Vector", "Offset", "offset")
        self.newInput("Integer", "Octaves", "octaves", value = 1, minValue = 1, maxValue = 16)
        if self.periodic:
            self.newInput("Integer", "PX", "px", value = 1, minValue = 1)
            self.newInput("Integer", "PY", "py", value = 1, minValue = 1)
            self.newInput("Integer", "PZ", "pz", value = 1, minValue = 1)
            self.newInput("Integer", "PW", "pw", value = 1, minValue = 1)
        self.newOutput("Float List", "Values", "values")

    def draw(self, layout):
        layout.prop(self, "periodic", text = "Periodic")

    def getExecutionCode(self, required):
        if not self.useWList:
            yield "w = DoubleList.fromValue(w)"
        yield "noise4D = an_bluefox_extension.libs.noise.noise4D"
        yield "vectors.transform(Matrix.Translation(offset))"
        yield  "_vectors = VirtualVector3DList.create(vectors, (0,0,0))"
        yield "_w = VirtualDoubleList.create(w, 0)"
        yield "amount = VirtualVector3DList.getMaxRealLength(_vectors, _w)"
        if self.periodic:
            yield "values = DoubleList.fromValues(noise4D(_vectors, _w, amount, amplitude, frequency, octaves, px, py, pz, pw, True))"
        else:
            yield "values = DoubleList.fromValues(noise4D(_vectors, _w, amount, amplitude, frequency, octaves, 1, 1, 1, 1, False))"

    def getUsedModules(self):
        return ['an_bluefox_extension']
