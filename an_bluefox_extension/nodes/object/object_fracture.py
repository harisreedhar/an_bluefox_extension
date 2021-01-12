import bpy
import bmesh
import mathutils
from bpy.props import *
from mathutils import Vector, Matrix
from animation_nodes . base_types import AnimationNode
from animation_nodes . utils.objects import enterObjectMode
from animation_nodes . nodes . mesh . bmesh_create import getBMeshFromMesh
from animation_nodes . nodes.container_provider import getMainObjectContainer
from animation_nodes . utils.depsgraph import getActiveDepsgraph, getEvaluatedID
from animation_nodes . data_structures.meshes.validate import createValidEdgesList
from animation_nodes . utils.blender_ui import executeInAreaType, iterActiveSpacesByType
from animation_nodes . data_structures import (
    LongList,
    Vector3DList,
    PolygonIndicesList,
    EdgeIndicesList,
    Mesh
)

class FractureInputs:
    objectIn = None
    parameters = None
    centerOrigin = False

class BF_ObjectFracturNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_ObjectFractureNode"
    bl_label = "Object Fracture"
    bl_width_default = 180
    errorHandlingType = "EXCEPTION"
    options = {"NOT_IN_SUBPROGRAM"}

    fillInner: BoolProperty(update = AnimationNode.refresh)
    centerOrigin: BoolProperty(update = AnimationNode.refresh)

    def create(self):
        self.newInput("Object", "Object", "object",
                      defaultDrawType="PROPERTY_ONLY")
        self.newInput("Vector List", "Points", "points")
        self.newInput("Float", "Offset", "offset")
        self.newInput("Integer", "Near Points", "nearPointsAmount", value=50, hide = True)
        self.newInput("Float", "Merge Distance", "mergeDistance", value=0.001, hide = True)

        self.newOutput("Object List", "Objects", "objects")

    def draw(self, layout):
        col = layout.column(align = True)
        row = col.row(align = True)
        self.invokeFunction(row, "invokeSeparateFunction",
                            text="Update",
                            description="separate loose parts from the source object",
                            icon="FILE_REFRESH")

        row = col.row(align = True)
        row.prop(self, "fillInner", text = "Inside Fill", toggle = True)
        row.prop(self, "centerOrigin", text = "Center Origin", toggle = True)

    def execute(self, object, points, offset, nearPointsAmount, mergeDistance):
        FractureInputs.objectIn = object
        FractureInputs.parameters = (points, self.fillInner, offset, nearPointsAmount, mergeDistance)
        FractureInputs.centerOrigin = self.centerOrigin

        if FractureInputs.objectIn is None:
            return []

        collection = getCollection(self.getSubCollectionName())
        return list(getattr(collection, "objects", []))

    def invokeSeparateFunction(self):
        if FractureInputs.objectIn is not None:
            fractureObjects(FractureInputs.objectIn, self.getSubCollectionName())
            self.refresh()

    def getSubCollectionName(self):
        return "Fractured_Objects" + self.identifier

    def delete(self):
        subCollection = getCollection(self.getSubCollectionName())
        if subCollection:
            for object in subCollection.objects:
                bpy.data.objects.remove(object)
            bpy.data.collections.remove(subCollection)

@executeInAreaType("VIEW_3D")
def fractureObjects(object, name):
    try:
        enterObjectMode()

        data = object.data.copy()
        bm = cellFracture(object)
        bm.to_mesh(data)
        bm.free()
        objName = object.name + "_piece.000"
        ob = bpy.data.objects.get(objName)
        if ob:
            bpy.data.objects.remove(ob)

        ob = bpy.data.objects.new(objName, data)
        subCollection = getCollection(name)

        for obj in subCollection.objects:
            bpy.data.objects.remove(obj)

        subCollection.objects.link(ob)
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.mesh.separate(type='LOOSE')
        if FractureInputs.centerOrigin:
            setOrigin(subCollection.objects)
        setIDKeys(subCollection.objects)
        bpy.ops.object.select_all(action="DESELECT")
    except Exception as e:
        print("Object fracture failed:")
        print(str(e))

def getCollection(name):
    mainCollection = getMainObjectContainer(bpy.context.scene)
    subCollection = bpy.data.collections.get(name)
    if subCollection is None:
        subCollection = bpy.data.collections.new(name)
        mainCollection.children.link(subCollection)
    return subCollection

def setOrigin(objects):
    for object in objects:
        mesh = object.data
        matrixWorld = object.matrix_world
        origin = sum((v.co for v in mesh.vertices),
                     Vector()) / len(mesh.vertices)
        T = Matrix.Translation(-origin)
        mesh.transform(T)
        matrixWorld.translation = matrixWorld @ origin

def setIDKeys(objects):
    for object in objects:
        object.id_keys.set("Transforms", "Initial Transforms",
                           (object.location, object.rotation_euler, object.scale))

def getBMesh(object):
    bm = bmesh.new()
    scene = bpy.context.scene
    if getattr(object, "type", "") != "MESH" or scene is None:
        return bm
    bm.from_object(object, getActiveDepsgraph(), deform=False)
    evaluatedObject = getEvaluatedID(object)
    bm.transform(evaluatedObject.matrix_world)
    return bm

def bMeshToMesh(bMesh):
    faces = PolygonIndicesList.fromValues(
        tuple(v.index for v in face.verts) for face in bMesh.faces)
    return Mesh(Vector3DList.fromValues(v.co for v in bMesh.verts),
                createValidEdgesList(polygons=faces),
                faces,
                LongList.fromValues(face.material_index for face in bMesh.faces))

# Reference: https://github.com/nortikin/sverchok/blob/master/node_scripts/SNLite_templates/demo/voronoi_3d.py
def cellFracture(object):
    points = [Vector([0, 0, 0])]
    fillInner = False
    offset = 0
    nearPointsAmount = 14
    mergeDistance = 0.05

    parameters = FractureInputs.parameters
    if parameters is not None:
        points, fillInner, offset, nearPointsAmount, mergeDistance = parameters

    locators = findLocators(points, nearPointsAmount, offset)

    meshList = []
    for item in locators:
        bMesh = getBMesh(object)
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
        bmesh.ops.remove_doubles(bMesh, verts=bMesh.verts, dist=mergeDistance)

        anMesh = bMeshToMesh(bMesh)
        bMesh.free()
        meshList.append(anMesh)

    result = getBMeshFromMesh(Mesh.join(*meshList))

    return result

def findLocators(points, nearPointsAmount, offset):
    size = len(points)
    kd = mathutils.kdtree.KDTree(size)
    for i, xyz in enumerate(points):
        kd.insert(xyz, i)
    kd.balance()

    locators = [[]] * size
    for idx, vtx in enumerate(points):
        nList = kd.find_n(vtx, nearPointsAmount)
        pointNormals = []
        for co, index, dist in nList:
            if index == idx:
                continue
            point = (co - vtx) * 0.5 * (1 - offset) + vtx
            normal = co - vtx
            pointNormals.append((point, normal))
        locators[idx] = pointNormals

    return locators
