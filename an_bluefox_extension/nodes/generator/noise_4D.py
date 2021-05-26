import bpy
from bpy.props import *
from animation_nodes . base_types import AnimationNode, VectorizedSocket

noiseTypeTypeItems = [
    ("PERLIN", "Perlin", "", "", 0),
    ("SIMPLEX", "Simplex", "", "", 1),
]

class BF_Noise4DNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_Noise4DNode"
    bl_label = "Noise 4D"

    useWList: VectorizedSocket.newProperty()
    noiseType: EnumProperty(name = "Noise Type", items = noiseTypeTypeItems, update = AnimationNode.refresh)
    periodic: BoolProperty(update = AnimationNode.refresh)

    def create(self):
        self.newInput("Vector List", "Vectors", "vectors")
        self.newInput(VectorizedSocket("Float", "useWList",
            ("W", "w"), ("Ws", "w")))
        self.newInput("Float", "Amplitude", "amplitude", value = 1)
        self.newInput("Float", "Frequency", "frequency", value = 0.1)
        self.newInput("Vector", "Offset", "offset")
        self.newInput("Integer", "Octaves", "octaves", value = 1, minValue = 1, maxValue = 8)
        if self.noiseType == "PERLIN":
            if self.periodic:
                self.newInput("Integer", "PX", "px", value = 1, minValue = 1)
                self.newInput("Integer", "PY", "py", value = 1, minValue = 1)
                self.newInput("Integer", "PZ", "pz", value = 1, minValue = 1)
                self.newInput("Integer", "PW", "pw", value = 1, minValue = 1)
        self.newOutput("Float List", "Values", "values")

    def draw(self, layout):
        layout.prop(self, "noiseType", text = "")
        if self.noiseType == "PERLIN":
            layout.prop(self, "periodic", text = "Periodic")

    def getExecutionCode(self, required):
        yield "noise = an_bluefox_extension.libs.noise"
        yield "vectors = noise.setFrequencyAndOffset(vectors, frequency, offset.x, offset.y, offset.z)"
        yield "_vectors = VirtualVector3DList.create(vectors, (0,0,0))"
        yield "_w = VirtualDoubleList.create(w, 0)"
        yield "amount = VirtualVector3DList.getMaxRealLength(_vectors, _w)"
        if self.noiseType == "PERLIN":
            if self.periodic:
                yield "values = DoubleList.fromValues(noise.pyPeriodicPerlin4D(_vectors, _w, px, py, pz, pw, amount, octaves, amplitude))"
            else:
                yield "values = DoubleList.fromValues(noise.pyPerlin4D(_vectors, _w, amount, octaves, amplitude))"
        if self.noiseType == "SIMPLEX":
            yield "values = DoubleList.fromValues(noise.pySimplex4D(_vectors, _w, amount, octaves, amplitude))"

    def getUsedModules(self):
        return ['an_bluefox_extension']
