import bpy
from bpy.props import *
from animation_nodes . base_types import AnimationNode, VectorizedSocket

noiseTypeItems = [
    ("PERLIN", "Perlin", "", "", 0),
    ("PERIODIC_PERLIN", "Periodic Perlin", "", "", 1),
    ("VORONOI", "Voronoi", "", "", 2),
]

voronoiDistanceTypeItems = [
    ("EUCLIDEAN", "Euclidean", "", "", 0),
    ("MANHATTAN", "Manhattan", "", "", 1),
    ("CHEBYCHEV", "Chebychev", "", "", 2),
    ("MINKOWSKI", "Minkowski", "", "", 3),
]

class BF_Noise4DNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_Noise4DNode"
    bl_label = "Noise 4D"

    useWList: VectorizedSocket.newProperty()
    noiseType: EnumProperty(name = "Noise Type", items = noiseTypeItems, update = AnimationNode.refresh)
    distanceMethod: EnumProperty(name = "Distance Method", items = voronoiDistanceTypeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Vector List", "Vectors", "vectors", dataIsModified = True)
        self.newInput(VectorizedSocket("Float", "useWList", ("W", "w"), ("Ws", "w")))
        self.newInput("Float", "Amplitude", "amplitude", value = 1)
        self.newInput("Float", "Frequency", "frequency", value = 0.1)
        self.newInput("Vector", "Offset", "offset")

        if self.noiseType != 'VORONOI':
            self.newInput("Integer", "Octaves", "octaves", value = 1, minValue = 1, maxValue = 16)
        if self.noiseType == 'PERIODIC_PERLIN':
            self.newInput("Integer", "PX", "px", value = 1, minValue = 1)
            self.newInput("Integer", "PY", "py", value = 1, minValue = 1)
            self.newInput("Integer", "PZ", "pz", value = 1, minValue = 1)
            self.newInput("Integer", "PW", "pw", value = 1, minValue = 1)
        if self.noiseType == 'VORONOI':
            self.newInput("Float", "Randomness", "randomness", value = 1, minValue = 0, maxValue = 1)
            self.newInput("Float", "Exponent", "exponent", value = 2)

        self.newOutput("Float List", "Values", "values")

    def draw(self, layout):
        layout.prop(self, "noiseType", text = "")
        if self.noiseType == 'VORONOI':
            layout.prop(self, "distanceMethod", text = "")

    def getExecutionCode(self, required):
        yield "vectors.transform(Matrix.Translation(offset))"
        yield "_vectors = VirtualVector3DList.create(vectors, (0,0,0))"
        yield "_w = VirtualDoubleList.create(w, 0)"
        yield "amount = VirtualVector3DList.getMaxRealLength(_vectors, _w)"
        yield "noise = an_bluefox_extension.libs.noise"
        if self.noiseType == 'PERLIN':
            yield "values = DoubleList.fromValues(noise.perlin4D_List(_vectors, _w, amount, amplitude, frequency, octaves))"
        elif self.noiseType == 'PERIODIC_PERLIN':
            yield "values = DoubleList.fromValues(noise.periodicPerlin4D_List(_vectors, _w, amount, amplitude, frequency, octaves, px, py, pz, pw))"
        elif self.noiseType == 'VORONOI':
            yield "values = DoubleList.fromValues(noise.voronoi4D_List(_vectors, _w, amount, amplitude, frequency, randomness, exponent, self.distanceMethod))"

    def getUsedModules(self):
        return ['an_bluefox_extension']
