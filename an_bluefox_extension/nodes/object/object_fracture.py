import bpy
import bmesh
import math
import mathutils
from bpy.props import *
from mathutils import Vector, Matrix
from animation_nodes . base_types import AnimationNode
from animation_nodes . utils.data_blocks import removeNotUsedDataBlock
from animation_nodes . nodes . mesh . bmesh_create import getBMeshFromMesh
from animation_nodes . nodes.container_provider import getMainObjectContainer
from animation_nodes . utils.depsgraph import getActiveDepsgraph, getEvaluatedID

class BF_ObjectFracturNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_ObjectFractureNode"
    bl_label = "Object Fracture"
    bl_width_default = 180
    errorHandlingType = "EXCEPTION"
    options = {"NOT_IN_SUBPROGRAM"}

    fillInner: BoolProperty(update = AnimationNode.refresh)
    shadeSmooth: BoolProperty(update = AnimationNode.refresh)
    smoothAngle: FloatProperty(default = 45, update = AnimationNode.refresh)
    offset: FloatProperty(update = AnimationNode.refresh)
    nCloseFinds: IntProperty(default = 25, update = AnimationNode.refresh)
    sourceObject: PointerProperty(type = bpy.types.Object, description = "Source Object",
                             update = AnimationNode.refresh)
    datas = {}

    def create(self):
        self.newInput("Vector List", "Source Points", "points")
        self.newInput("Scene", "Scene", "scene", hide = True)
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
        row.prop(self, "sourceObject", text = "")
        row1 = col.row(align = True)
        row1.prop(self, "fillInner", text = "Inside Fill", toggle = True)
        row1.prop(self, "shadeSmooth", text = "Shade Smooth", toggle = True)
        if self.shadeSmooth:
            row2 = col.row(align = True)
            row2.prop(self, "smoothAngle", text = "Smooth Angle")
        row3 = col.row(align = True)
        row3.prop(self, "offset", text = "Offset")
        row4 = col.row(align = True)
        row4.prop(self, "nCloseFinds", text = "Close Finds No.")

    def execute(self, points, scene):
        self.datas["points"] = points
        self.datas["scene"] = scene
        if None in [scene, self.sourceObject]:
            return []
        collection = getCollection(scene, self.getSubCollectionName())
        return list(getattr(collection, "objects", []))

    def invokeFractureFunction(self):
        object = self.sourceObject
        if object is not None:
            points = self.datas.get("points")
            scene = self.datas.get("scene")
            parameters = (points, self.fillInner, self.offset, self.nCloseFinds)
            fractureObjects(object, scene, self.getSubCollectionName(), parameters,
                            self.shadeSmooth, self.smoothAngle)
            self.refresh()
            return True

    def getSubCollectionName(self):
        return "Fracture_Collection" + self.identifier

    def delete(self):
        subCollection = getCollection(self.datas.get("scene"), self.getSubCollectionName())
        if subCollection:
            removeObjectsFromCollection(subCollection)
            bpy.data.collections.remove(subCollection)

def fractureObjects(object, scene, name, parameters, smooth, angle):
    try:
        bm = getBMesh(object, scene)
        bmList = cellFracture(bm, parameters)
        subCollection = getCollection(scene, name)
        removeObjectsFromCollection(subCollection)
        fractureName = object.name + "_chunk."
        objects = bmeshListToObjects(bmList, fractureName, subCollection)
        if smooth:
            shadeObjectsSmooth(objects, angle)
        setIDKeys(objects)
    except Exception as e:
        print("Object fracture failed:")
        print(str(e))

def getCollection(scene, name):
    mainCollection = getMainObjectContainer(scene)
    subCollection = bpy.data.collections.get(name)
    if subCollection is None:
        subCollection = bpy.data.collections.new(name)
        mainCollection.children.link(subCollection)
    return subCollection

def setIDKeys(objects):
    for object in objects:
        object.id_keys.set("Transforms", "Initial Transforms",
                           (object.location, object.rotation_euler, object.scale))

def removeObjectsFromCollection(collection):
    for obj in collection.objects:
        data = obj.data
        type = obj.type
        bpy.data.objects.remove(obj)
        if data is None: return
        if data.users == 0:
            removeNotUsedDataBlock(data, type)

def getBMesh(object, scene):
    bm = bmesh.new()
    if getattr(object, "type", "") != "MESH" or scene is None:
        return bm
    bm.from_object(object, getActiveDepsgraph(), deform=False)
    evaluatedObject = getEvaluatedID(object)
    bm.transform(evaluatedObject.matrix_world)
    return bm

def shadeObjectsSmooth(objects, angle):
    smooth = True
    angle = math.radians(angle)
    for object in objects:
        mesh = object.data
        if len(mesh.polygons) > 0:
            smoothList = [smooth] * len(mesh.polygons)
            mesh.polygons.foreach_set("use_smooth", smoothList)
            mesh.polygons[0].use_smooth = smooth
            mesh.use_auto_smooth = True
            mesh.auto_smooth_angle = angle

def bmeshListToObjects(bmList, fractureName, subCollection):
    objectList = []
    for i, bm in enumerate(bmList):
        name = fractureName+str(i).zfill(3)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        ob = bpy.data.objects.new(name, me)
        subCollection.objects.link(ob)
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
def cellFracture(bm, parameters):
    points = [Vector([0, 0, 0])]
    fillInner = False
    offset = 0
    nCloseFinds = 14
    if parameters is not None:
        points, fillInner, offset, nCloseFinds = parameters
    locators = findLocators(points, nCloseFinds, offset)
    bmList = []
    for item in locators:
        bMesh = bm.copy()
        for point, normal in item:
            geomIn = bMesh.verts[:] + bMesh.edges[:] + bMesh.faces[:]
            res = bmesh.ops.bisect_plane(
                bMesh, geom=geomIn, dist=0.00001,
                plane_co=point, plane_no=normal, use_snap_center=False,
                clear_outer=True, clear_inner=False
            )
            if fillInner:
                surround = [e for e in res['geom_cut']
                            if isinstance(e, bmesh.types.BMEdge)]
                fres = bmesh.ops.edgenet_prepare(bMesh, edges=surround)
                bmesh.ops.edgeloop_fill(bMesh, edges=fres['edges'])
        if len(bMesh.faces) > 0:
            bmList.append(bMesh)
    return bmList

def findLocators(points, nCloseFinds, offset):
    size = len(points)
    kd = mathutils.kdtree.KDTree(size)
    for i, xyz in enumerate(points):
        kd.insert(xyz, i)
    kd.balance()
    locators = [[]] * size
    for idx, vtx in enumerate(points):
        nList = kd.find_n(vtx, nCloseFinds)
        pointNormals = []
        for co, index, dist in nList:
            if index == idx:
                continue
            point = (co - vtx) * 0.5 * (1 - offset) + vtx
            normal = co - vtx
            pointNormals.append((point, normal))
        locators[idx] = pointNormals
    return locators
