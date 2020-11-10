import bpy
import numpy as np
from bpy.props import *
from animation_nodes . events import propertyChanged
from animation_nodes . base_types import AnimationNode, VectorizedSocket
from . utils.marchingCubes import iterate_and_store_3d, unpack_unique_verts
from animation_nodes . data_structures.meshes.validate import createValidEdgesList
from animation_nodes . data_structures import LongList, Vector3DList, PolygonIndicesList, EdgeIndicesList, Mesh

fieldTypeItems = [
    ("FALLOFF", "Falloff", "Use falloff field", "", 0),
    ("FORMULA", "Formula", "Use formula field", "", 1),
    ("CUSTOM", "Custom", "Use custom function field", "", 2)
]

class BF_MarchingCubesNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_MarchingCubesNode"
    bl_label = "Marching Cubes"
    errorHandlingType = "EXCEPTION"

    codeEffects = [VectorizedSocket.CodeEffect]
    useThresholdList: VectorizedSocket.newProperty()

    fieldType: EnumProperty(name = "Field Type", default = "FALLOFF",
        items = fieldTypeItems, update = AnimationNode.refresh)

    def create(self):
        if self.fieldType == "FALLOFF":
            self.newInput("Falloff", "Field", "field")
        elif self.fieldType == "FORMULA":
            defaultFormula = "cos(x*3)+cos(y*3)+cos(z*3)"
            self.newInput("Text", "Field", "field", value = defaultFormula, 
                                        defaultDrawType = "PROPERTY_ONLY")   
        else:
            self.newInput("Generic", "Field", "field")
        self.newInput("Matrix", "Transform","transform")
        self.newInput("Integer", "Samples","samples", minValue = 0, value = 10)
        self.newInput(VectorizedSocket("Float", "useThresholdList",
            ("Threshold", "threshold"),("Thresholds", "threshold")), value = 0.3)

        self.newOutput(VectorizedSocket("Mesh", "useThresholdList",
            ("Mesh", "mesh"), ("Mesh List", "mesh")))

    def draw(self, layout):
        layout.prop(self, "fieldType", text = "")
      
    def execute(self, field, transform, samples, threshold):
        try:
            boundingBox = Vector3DList.fromValues(unityCube)
            boundingBox.transform(transform)
            return self.generateMeshFromField(boundingBox, samples, field, threshold)
        except:
            self.raiseErrorMessage("Mesh generation failed")
            return Mesh()

    def generateMeshFromField(self, boundingBox, samples, field, threshold):
        grid, minBound, maxBound = self.createGrid(boundingBox, samples)
        volume = self.getField(field, grid).reshape((samples, samples, samples))

        vertices, faces = self.isoSurface(volume, threshold)
        vertices = vertices.asNumpyArray().reshape(-1,3)
        vertices = ((vertices / samples) * (maxBound - minBound) + minBound)
        vertices = Vector3DList.fromNumpyArray(vertices.ravel().astype('f'))

        return self.createMesh(vertices, faces)

    # Need work on face ordering (Causes weird artifacts when smoothshading)
    def isoSurface(self, volume, level, spacing=(1,1,1)):
        if volume.ndim != 3:
            raise ValueError("Input volume must have 3 dimensions.")
        if level is None:
            level = 0.5 * (volume.min() + volume.max())
        else:
            level = float(level)
            if level < volume.min() or level > volume.max():
                raise ValueError("Surface level must be within volume data range.")
        if len(spacing) != 3:
            raise ValueError("`spacing` must consist of three floats.")

        volume = np.array(volume, dtype=np.float64, order="C")
        raw_faces = iterate_and_store_3d(volume, level)
        vertices, faces = unpack_unique_verts(raw_faces)
        return vertices, faces

    def createGrid(self, boundingBox, samples):
        vs = np.array(boundingBox)
        minBound = vs.min(axis=0)
        maxBound = vs.max(axis=0)
        xRange = np.linspace(minBound[0], maxBound[0], num=samples)
        yRange = np.linspace(minBound[1], maxBound[1], num=samples)
        zRange = np.linspace(minBound[2], maxBound[2], num=samples)
        grid = np.vstack([np.meshgrid(xRange, yRange, zRange, indexing='ij')]).reshape(3,-1).T
        return grid, minBound, maxBound

    def createMesh(self, vertices, faces):
        edges = createValidEdgesList(polygons = faces)
        materialIndices = LongList(length = len(faces))
        materialIndices.fill(0)
        return Mesh(vertices, edges, faces, materialIndices, skipValidation = False)

    def getField(self, field, grid):
        x, y, z = grid[:,0], grid[:,1], grid[:,2]
        if self.fieldType == "FALLOFF":
            falloffEvaluator = self.getFalloffEvaluator(field)
            vectors = Vector3DList.fromNumpyArray(grid.astype('float32').ravel())
            falloffStrengths = falloffEvaluator.evaluateList(vectors)
            return falloffStrengths.asNumpyArray().astype('float32')
        elif self.fieldType == "FORMULA":
            return self.evaluateFormula(field, grid, x, y, z)
        else:
            return field(x, y, z)
    
    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")

    def evaluateFormula(self, formula, grid, x, y, z):
        count = len(x)
        default_result = np.zeros(count)

        # constants
        pi = np.pi
        e = np.e

        # functions
        def abs(x):return np.absolute(x)
        def sqrt(x):return np.sqrt(x)
        def cbrt(x):return np.cbrt(x)
        def round(x):return np.around(x)
        def floor(x):return np.floor(x)
        def ceil(x):return np.ceil(x)
        def trunc(x):return np.trunc(x)
        def clamp(x):return np.clip(x,0,1)
        def exp(x):return np.exp(x)
        def log(x):return np.log(x)
        def radians(x):return np.radians(x)
        def degrees(x):return np.degrees(x)
        def sin(x):return np.sin(x)
        def cos(x):return np.cos(x)
        def tan(x):return np.tan(x)
        def asin(x):return np.arcsin(x)
        def acos(x):return np.arccos(x)
        def atan(x):return np.arctan(x)
        def atan2(x,y):return np.arctan2(x,y)
        def mod(x,y):return np.mod(x,y)
        def pow(x,y):return np.power(x,y)
        def rem(x,y):return np.remainder(x,y)
        def max(x,y):return np.maximum(x,y)
        def min(x,y):return np.minimum(x,y)
        def copysign(x,y):return np.copysign(x,y)
        def dist(x,y):return np.linalg.norm(x-y)

        return eval(formula)

unityCube = [(-1.0000, -1.0000, -1.0000),(-1.0000, -1.0000, 1.0000),
                (-1.0000, 1.0000, -1.0000),(-1.0000, 1.0000, 1.0000),
                (1.0000, -1.0000, -1.0000),(1.0000, -1.0000, 1.0000),
                (1.0000, 1.0000, -1.0000),(1.0000, 1.0000, 1.0000)]
