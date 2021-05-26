import bpy
import numpy as np
from bpy.props import *
from ... libs import skimage
from ... utils.formula import evaluateFormula
from . c_utils import polygonIndices_From_triArray
from animation_nodes . data_structures import Vector3DList, Mesh
from animation_nodes . base_types import AnimationNode, VectorizedSocket
from animation_nodes . data_structures.meshes.validate import createValidEdgesList

fieldTypeItems = [
    ("FALLOFF", "Falloff", "Use falloff field", "", 0),
    ("FORMULA", "Formula", "Use formula field", "", 1),
    ("FUNCTION", "Function", "Use function(x,y,z) as field", "", 2),
    ("ARRAY", "Array", "Use numpy array field", "", 3),
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
            defaultFormula = "cos(x*6)+cos(y*6)+cos(z*6)"
            self.newInput("Text", "Field", "field", value = defaultFormula,
                                        defaultDrawType = "PROPERTY_ONLY")
        else:
            self.newInput("Generic", "Field", "field")
        self.newInput("Integer", "X Divisions","xDivisions", minValue = 2, value = 10)
        self.newInput("Integer", "Y Divisions","yDivisions", minValue = 2, value = 10)
        self.newInput("Integer", "Z Divisions","zDivisions", minValue = 2, value = 10)
        self.newInput("Float", "Scale Grid","scaleGrid", value = 1)
        self.newInput("Matrix", "Transform Grid","transform")
        self.newInput(VectorizedSocket("Float", "useThresholdList",
            ("Threshold", "threshold"),("Thresholds", "threshold")), value = 0.3, hide = True)

        self.newOutput(VectorizedSocket("Mesh", "useThresholdList",
            ("Mesh", "mesh"), ("Mesh List", "mesh")))
        self.newOutput("Vector List", "Normals", "normals", hide = True)
        self.newOutput("Vector List", "Grid Points", "gridPoints", hide = True)
        self.newOutput("Float List", "Values", "values", hide = True)

        socket = self.inputs[-1]
        socket.useIsUsedProperty = True
        socket.isUsed = False

    def draw(self, layout):
        layout.prop(self, "fieldType", text = "")

    def getExecutionCode(self, required):
        yield "mesh = Mesh()"
        yield "gridPoints = Vector3DList()"
        yield "normals = Vector3DList()"
        yield "values = DoubleList()"
        if "mesh" in required:
            yield "try:"
            yield "    boundingBox = Vector3DList.fromNumpyArray(self.unityCube.ravel() * scaleGrid)"
            yield "    boundingBox.transform(transform)"
            yield "    mesh, grid, norm, val = self.generateMeshFromField(boundingBox, xDivisions, yDivisions, zDivisions, field, threshold)"
            if "gridPoints" in required:
                yield "    gridPoints = Vector3DList.fromNumpyArray(grid.ravel().astype('f'))"
            if "normals" in required:
                yield "    normals = Vector3DList.fromNumpyArray(norm.ravel().astype('f'))"
            if "values" in required:
                yield "    values = DoubleList.fromNumpyArray(val.astype('float64'))"
            yield "except Exception as e:"
            yield "    print('Marching Cubes error:', str(e))"
            yield "    self.raiseErrorMessage('Mesh generation failed')"

    def generateMeshFromField(self, boundingBox, xDivisions, yDivisions, zDivisions, field, threshold):
        grid, minBound, maxBound = self.createGrid(boundingBox, xDivisions, yDivisions, zDivisions)
        volume = self.getField(field, grid).reshape((xDivisions, yDivisions, zDivisions))
        if not self.inputs[-1].isUsed:
            threshold = None
        vertArr, facesArr, normalArr, valueArr = skimage.marching_cubes(volume, level = threshold)
        vertArr = ((vertArr / np.array([xDivisions, yDivisions, zDivisions])) * (maxBound - minBound) + minBound)
        vertices = Vector3DList.fromNumpyArray(vertArr.ravel().astype('f'))
        faces = polygonIndices_From_triArray(facesArr)
        result = self.createMesh(vertices, faces), grid, normalArr, valueArr
        return result

    def createGrid(self, boundingBox, xDivisions, yDivisions, zDivisions):
        vs = boundingBox.asNumpyArray().reshape(-1,3)
        minBound = vs.min(axis=0)
        maxBound = vs.max(axis=0)
        xRange = np.linspace(minBound[0], maxBound[0], num=xDivisions)
        yRange = np.linspace(minBound[1], maxBound[1], num=yDivisions)
        zRange = np.linspace(minBound[2], maxBound[2], num=zDivisions)
        grid = np.vstack([np.meshgrid(xRange, yRange, zRange, indexing='ij')]).reshape(3,-1).T
        return grid, minBound, maxBound

    def createMesh(self, vertices, faces):
        edges = createValidEdgesList(polygons = faces)
        return Mesh(vertices, edges, faces, skipValidation = True)

    def getField(self, field, grid):
        gx, gy, gz = grid[:,0], grid[:,1], grid[:,2]
        if self.fieldType == "FALLOFF":
            falloffEvaluator = self.getFalloffEvaluator(field)
            vectors = Vector3DList.fromNumpyArray(grid.astype('float32').ravel())
            falloffStrengths = falloffEvaluator.evaluateList(vectors)
            return falloffStrengths.asNumpyArray().astype('float32')
        elif self.fieldType == "FORMULA":
            return evaluateFormula(field, x=gx, y=gy, z=gz)
        elif self.fieldType == "FUNCTION":
            return field(gx, gy, gz)
        else:
            return field

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")

    unityCube = np.array([(-1.0000, -1.0000, -1.0000),(-1.0000, -1.0000, 1.0000),
                    (-1.0000, 1.0000, -1.0000),(-1.0000, 1.0000, 1.0000),
                    (1.0000, -1.0000, -1.0000),(1.0000, -1.0000, 1.0000),
                    (1.0000, 1.0000, -1.0000),(1.0000, 1.0000, 1.0000)], dtype = 'float32')
