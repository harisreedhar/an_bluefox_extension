import bpy
import sys
import bmesh
import math
import mathutils
from bpy.props import *
from mathutils import Vector, Matrix
from animation_nodes . utils.data_blocks import removeNotUsedDataBlock
from animation_nodes . base_types import AnimationNode, VectorizedSocket
from animation_nodes . utils.depsgraph import getActiveDepsgraph, getEvaluatedID

dataByIdentifier = {}

class FractureData:
    def __init__(self, *args):
        self.sourceObjects = args[0]
        self.sourcePoints  = args[1]
        self.collection    = args[2]
        self.shrink        = args[3]
        self.quality       = args[4]
        self.fillInner     = args[5]
        self.materialIndex = args[6]
        self.copyData      = args[7]

class BF_ObjectFracturNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_ObjectFractureNode"
    bl_label = "Object Fracture"
    errorHandlingType = "EXCEPTION"
    options = {"NOT_IN_SUBPROGRAM"}

    useObjectList : VectorizedSocket.newProperty()

    collection    : PointerProperty(type = bpy.types.Collection, description = "Output Collection", update = AnimationNode.refresh)
    shrink        : FloatProperty(update = AnimationNode.refresh)
    quality       : IntProperty(default = 100, update = AnimationNode.refresh)
    fillInner     : BoolProperty(update = AnimationNode.refresh)
    materialIndex : IntProperty(default = 0, update = AnimationNode.refresh)
    copyData      : BoolProperty(default = True, description = "Copies UV, Vertex Colors, Materials from source", update = AnimationNode.refresh)

    def create(self):
        self.newInput(VectorizedSocket("Object", "useObjectList",
            ("Object", "object", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Objects", "object")))
        self.newInput("Vector List", "Points", "points")
        self.newOutput("Object List", "Objects", "objects")

    def draw(self, layout):
        col = layout.column()
        col.scale_y = 1.5
        self.invokeFunction(col, "invokeFractureFunction",
                            text="Update",
                            description="fracture object into multiple objects",
                            icon="FILE_REFRESH")

        col = layout.column(align = True)
        row = col.row(align = True)
        row.prop(self, "collection", text = "")
        if self.collection is None:
            self.invokeFunction(row, "createCollection",
                                text="",
                                description="Create new output collection",
                                icon = "PLUS")

        row = col.row(align = True)
        row.prop(self, "shrink", text = "Shrink")
        row = col.row(align = True)
        row.prop(self, "quality", text = "Quality")
        row = col.row(align = True)
        fillInnerIcon = "DOWNARROW_HLT" if self.fillInner else "RIGHTARROW"
        row.prop(self, "fillInner", text = "Fill Inner", toggle = True, icon=fillInnerIcon)
        if self.fillInner:
            row = col.row(align = True)
            row.prop(self, "materialIndex", text = "Material Index")

    def drawAdvanced(self, layout):
        layout.prop(self, "copyData", text="Copy object data")

    def execute(self, object, points):
        objects = object if self.useObjectList else [object]
        collection = self.collection
        fractureData = FractureData(objects,
                                    points,
                                    collection,
                                    self.shrink,
                                    self.quality,
                                    self.fillInner,
                                    self.materialIndex,
                                    self.copyData)

        dataByIdentifier[self.identifier] = fractureData
        return list(getattr(collection, "objects", []))

    def invokeFractureFunction(self):
        fractureData = dataByIdentifier.get(self.identifier)
        if fractureData is None:
            return
        if None in fractureData.sourceObjects:
            return
        if any(i is None for i in [fractureData.sourcePoints, fractureData.collection]):
            return

        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        wm.progress_update(1)

        fractureObjects(fractureData, wm)
        self.refresh()

        wm.progress_end()
        return

    def createCollection(self):
        collection = bpy.data.collections.new('AN_Fracture_Collection')
        bpy.context.scene.collection.children.link(collection)
        self.collection = collection

    def delete(self):
        keys = list(dataByIdentifier.keys())
        for key in keys:
            if key.startswith(self.identifier):
                dataByIdentifier.pop(key)

    def duplicate(self, sourceNode):
        self.collection = None

def fractureObjects(fractureData, wm):
    try:
        sys.stdout.write("Fracturing Objects: ")
        sys.stdout.flush()

        objects = fractureData.sourceObjects
        collection = fractureData.collection
        removeObjectsFromCollection(collection)
        length = len(objects)
        for i, object in enumerate(objects):
            bm = getBMesh(object)
            wm.progress_update(2)
            bmList = cellFracture(bm, fractureData, wm)
            fractureName = object.name + "_chunk."
            fracturedObjects = bmeshListToObjects(bmList, fractureName, collection)
            setIDKeys(fracturedObjects)

            if fractureData.copyData:
                for fracturedObject in fracturedObjects:
                    copyObjectData(object, fracturedObject)

            msg = f"{i+1} of {length}"
            sys.stdout.write(msg + chr(8) * len(msg))
            sys.stdout.flush()
            wm.progress_update(99)

        sys.stdout.write("DONE" + " "*len(msg)+"\n")
        sys.stdout.flush()

    except Exception as e:
        print("Object fracture failed:")
        print(str(e))

def setIDKeys(objects):
    for object in objects:
        object.id_keys.set("Transforms", "Initial Transforms",
                           (object.location, object.rotation_euler, object.scale))

def copyObjectData(sourceObject, destinationObject):
    sourceData = sourceObject.data
    destinationData = destinationObject.data
    for mat in sourceData.materials:
        destinationData.materials.append(mat)
    for layerAttribute in ("vertex_colors", "uv_layers"):
        sourceLayer = getattr(sourceData, layerAttribute)
        destinationLayer = getattr(destinationData, layerAttribute)
        for key in sourceLayer.keys():
            destinationLayer.new(name=key)

    for i in range(len(destinationData.materials)):
        sourceSlot = sourceObject.material_slots[i]
        destinationSlot = destinationObject.material_slots[i]
        destinationSlot.link = sourceSlot.link
        destinationSlot.material = sourceSlot.material

    destinationData.update()

def removeObjectsFromCollection(collection):
    for obj in collection.objects:
        data = obj.data
        type = obj.type
        bpy.data.objects.remove(obj)
        if data is None: return
        if data.users == 0:
            removeNotUsedDataBlock(data, type)

def getBMesh(object):
    bm = bmesh.new()
    if getattr(object, "type", "") != "MESH":
        return bm
    bm.from_object(object, getActiveDepsgraph())
    evaluatedObject = getEvaluatedID(object)
    bm.transform(evaluatedObject.matrix_world)
    return bm

def bmeshListToObjects(bmList, fractureName, collection):
    objectList = []
    for i, bm in enumerate(bmList):
        name = fractureName + str(i).zfill(3)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        ob = bpy.data.objects.new(name, me)
        collection.objects.link(ob)
        objectList.append(ob)
        setOrigin(ob)
    return objectList

def setOrigin(object):
    mesh = object.data
    matrixWorld = object.matrix_world
    origin = sum((v.co for v in mesh.vertices), Vector()) / len(mesh.vertices)
    T = Matrix.Translation(-origin)
    mesh.transform(T)
    matrixWorld.translation = matrixWorld @ origin

# Reference: https://github.com/nortikin/sverchok/blob/master/node_scripts/SNLite_templates/demo/voronoi_3d.py
def cellFracture(bm, fractureData, wm):
    locators = findLocators(fractureData.sourcePoints, fractureData.quality, fractureData.shrink, wm)
    bmList = []
    progressTot = len(locators)
    for i, item in enumerate(locators):
        bMesh = bm.copy()
        for point, normal in item:
            geomIn = bMesh.verts[:] + bMesh.edges[:] + bMesh.faces[:]
            res = bmesh.ops.bisect_plane(
                bMesh, geom=geomIn, dist=0.00001,
                plane_co=point, plane_no=normal, use_snap_center=False,
                clear_outer=True, clear_inner=False
            )
            if fractureData.fillInner:
                surround = [e for e in res['geom_cut']
                            if isinstance(e, bmesh.types.BMEdge)]
                fres = bmesh.ops.edgenet_prepare(bMesh, edges=surround)
                bmesh.ops.edgeloop_fill(bMesh, edges = fres['edges'], mat_nr = fractureData.materialIndex)

        if len(bMesh.faces) > 0:
            bmList.append(bMesh)
        wm.progress_update(int((i/progressTot)*95)+5)
    return bmList

def findLocators(points, nCloseFinds, shrink, wm):
    size = len(points)
    kd = mathutils.kdtree.KDTree(size)
    wm.progress_update(3)
    for i, xyz in enumerate(points):
        kd.insert(xyz, i)
    kd.balance()
    locators = [[]] * size
    wm.progress_update(4)
    for idx, vtx in enumerate(points):
        nList = kd.find_n(vtx, nCloseFinds)
        pointNormals = []
        for co, index, dist in nList:
            if index == idx:
                continue
            point = (co - vtx) * 0.5 * (1 - shrink) + vtx
            normal = co - vtx
            pointNormals.append((point, normal))
        locators[idx] = pointNormals
    wm.progress_update(5)
    return locators
