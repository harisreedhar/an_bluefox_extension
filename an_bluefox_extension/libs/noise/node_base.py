import bpy
from bpy.props import *
from animation_nodes . base_types import AnimationNode

noiseTypeItems = [
    ("PERLIN", "Perlin", "", "", 0),
    ("PERIODIC_PERLIN", "Periodic Perlin", "", "", 1),
    ("VORONOI", "Voronoi", "", "", 2),
]

distanceTypeItems = [
    ("EUCLIDEAN", "Euclidean", "", "", 0),
    ("MANHATTAN", "Manhattan", "", "", 1),
    ("CHEBYCHEV", "Chebychev", "", "", 2)
]

class Noise4DNodeBase:
    noiseType: EnumProperty(name = "Noise Type", items = noiseTypeItems, update = AnimationNode.refresh)
    distanceMethod: EnumProperty(name = "Distance Method", items = distanceTypeItems, update = AnimationNode.refresh)

    def createInputs(self):
        self.newInput("Float", "W", "w")
        self.newInput("Float", "Amplitude", "amplitude", value = 1)
        self.newInput("Float", "Frequency", "frequency", value = 0.1)
        self.newInput("Vector", "Offset", "offset")

        if self.noiseType != 'VORONOI':
            self.newInput("Integer", "Octaves", "octaves", value = 1, minValue = 1, maxValue = 16)
            self.newInput("Float", "Lacunarity", "lacunarity", value = 2)
            self.newInput("Float", "Persistance", "persistance", value = 0.5)

        if self.noiseType == 'PERIODIC_PERLIN':
            self.newInput("Integer", "PX", "px", value = 1, minValue = 1)
            self.newInput("Integer", "PY", "py", value = 1, minValue = 1)
            self.newInput("Integer", "PZ", "pz", value = 1, minValue = 1)
            self.newInput("Integer", "PW", "pw", value = 1, minValue = 1)

        if self.noiseType == 'VORONOI':
            self.newInput("Float", "Randomness", "randomness", value = 1, minValue = 0, maxValue = 1)

    def drawNoiseSettings(self, layout):
        layout.prop(self, "noiseType", text = "")
        if self.noiseType == 'VORONOI':
            layout.prop(self, "distanceMethod", text = "")
