import bpy
from ... libs . noise import Noise4DNodeBase
from animation_nodes . base_types import AnimationNode, VectorizedSocket

class BF_Noise4DNode(bpy.types.Node, AnimationNode, Noise4DNodeBase):
    bl_idname = "an_bf_Noise4DNode"
    bl_label = "Noise 4D"

    useWList: VectorizedSocket.newProperty()

    def create(self):
        self.newInput("Vector List", "Vectors", "vectors")
        self.newInput(VectorizedSocket("Float", "useWList", ("W", "w"), ("Ws", "w")))
        self.createInputs()
        self.newOutput("Float List", "Values", "values")

    def draw(self, layout):
        self.drawNoiseSettings(layout)

    def getExecutionCode(self, required):
        yield "_vectors = VirtualVector3DList.create(vectors, (0,0,0))"
        yield "_w = VirtualDoubleList.create(w, 0)"
        yield "amount = VirtualVector3DList.getMaxRealLength(_vectors, _w)"
        yield "noise = an_bluefox_extension.libs.noise"
        if self.noiseType == 'PERLIN':
            yield "values = DoubleList.fromValues(noise.perlin4D_List(_vectors, _w, amount, amplitude, frequency, offset, octaves, lacunarity, persistance))"
        elif self.noiseType == 'PERIODIC_PERLIN':
            yield "values = DoubleList.fromValues(noise.periodicPerlin4D_List(_vectors, _w, amount, amplitude, frequency, offset, octaves, lacunarity, persistance, px, py, pz, pw))"
        elif self.noiseType == 'VORONOI':
            yield "values = DoubleList.fromValues(noise.voronoi4D_List(_vectors, _w, amount, amplitude, frequency, offset, randomness, exponent, self.distanceMethod))"

    def getUsedModules(self):
        return ['an_bluefox_extension']
