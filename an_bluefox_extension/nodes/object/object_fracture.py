import bpy
import bmesh
import math
import mathutils
from bpy.props import *
from mathutils import Vector, Matrix
from animation_nodes . base_types import AnimationNode
from animation_nodes . utils.data_blocks import removeNotUsedDataBlock
from animation_nodes . nodes.container_provider import getMainObjectContainer
from animation_nodes . utils.depsgraph import getActiveDepsgraph, getEvaluatedID

class BF_ObjectFracturNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_ObjectFractureNode"
    bl_label = "Object Fracture"
    errorHandlingType = "EXCEPTION"
    options = {"NOT_IN_SUBPROGRAM"}

    sourceObject: PointerProperty(type = bpy.types.Object, description = "Source Object",
                             update = AnimationNode.refresh)
    shrink: FloatProperty(update = AnimationNode.refresh)
    nCloseFinds: IntProperty(default = 100, update = AnimationNode.refresh)
    fillInner: BoolProperty(update = AnimationNode.refresh)
    innerMaterialIndex: IntProperty(default = 0, update = AnimationNode.refresh)
    shadeSmooth: BoolProperty(update = AnimationNode.refresh)
    smoothAngle: FloatProperty(default = 45, update = AnimationNode.refresh)
    collection: PointerProperty(type = bpy.types.Collection, description = "Output Collection",
                             update = AnimationNode.refresh)
    copyObjectData: BoolProperty(default = True, description = "Copies UV, Vertex Colors, Materials from source",
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
        row1.prop(self, "shrink", text = "Shrink")
        row2 = col.row(align = True)
        row2.prop(self, "nCloseFinds", text = "Quality")
        row3 = col.row(align = True)
        row3.prop(self, "fillInner", text = "Fill Inner", toggle = True)
        if self.fillInner:
            row33 = col.row(align = True)
            row33.prop(self, "innerMaterialIndex", text = "Material Index")
        row4 = col.row(align = True)
        row4.prop(self, "shadeSmooth", text = "Shade Smooth", toggle = True)
        if self.shadeSmooth:
            row44 = col.row(align = True)
            row44.prop(self, "smoothAngle", text = "Angle")
        row5 = col.row(align = True)
        row5.prop(self, "collection", text = "")
        if self.collection is None:
            self.invokeFunction(row5, "createCollection",
                                text="",
                                description="Create new output collection",
                                icon = "PLUS")

    def drawAdvanced(self, layout):
        layout.prop(self, "copyObjectData", text="Copy object data")

    def execute(self, points, scene):
        self.datas[self.identifier] = {'points':points, 'scene':scene}
        if None in [scene, self.sourceObject]:
            return []
        collection = self.collection
        return list(getattr(collection, "objects", []))

    def invokeFractureFunction(self):
        datas = self.datas.get(self.identifier)
        if datas is None:
            return
        points = datas.get("points")
        scene = datas.get("scene")
        object = self.sourceObject
        collection = self.collection
        if None not in [object, collection]:
            wm = bpy.context.window_manager
            wm.progress_begin(0, 100)
            wm.progress_update(1)
            parameters = (points, self.fillInner, self.shrink, self.nCloseFinds,
                        self.innerMaterialIndex)
            fractureObjects(object, scene, collection, parameters,
                            self.shadeSmooth, self.smoothAngle, self.copyObjectData, wm)
            self.refresh()
            wm.progress_end()
            return True

    def createCollection(self):
        mainCollection = getMainObjectContainer(self.datas.get("scene"))
        subCollection = bpy.data.collections.new('AN_Fracture_Collection')
        mainCollection.children.link(subCollection)
        self.collection = subCollection

    def delete(self):
        keys = list(self.datas.keys())
        for key in keys:
            if key.startswith(self.identifier):
                self.datas.pop(key)

    def duplicate(self, sourceNode):
        self.sourceObject = self.collection = None

def fractureObjects(object, scene, collection, parameters, smooth, angle, copyObjectData, wm):
    try:
        bm = getBMesh(object, scene)
        wm.progress_update(2)
        bmList = cellFracture(bm, parameters, wm)
        removeObjectsFromCollection(collection)
        fractureName = object.name + "_chunk."
        objects = bmeshListToObjects(bmList, fractureName, collection)
        if smooth:
            shadeObjectsSmooth(objects, angle)
        setIDKeys(objects)

        if copyObjectData:
            for ob in objects:
                destinationData = ob.data
                sourceData = object.data
                for mat in sourceData.materials:
                    destinationData.materials.append(mat)
                for layerAttribute in ("vertex_colors", "uv_layers"):
                    sourceLayer = getattr(sourceData, layerAttribute)
                    destinationLayer = getattr(destinationData, layerAttribute)
                    for key in sourceLayer.keys():
                        destinationLayer.new(name=key)

                for i in range(len(destinationData.materials)):
                    sourceSlot = object.material_slots[i]
                    destinationSlot = ob.material_slots[i]
                    destinationSlot.link = sourceSlot.link
                    destinationSlot.material = sourceSlot.material

        wm.progress_update(99)
    except Exception as e:
        print("Object fracture failed:")
        print(str(e))

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
    bm.from_object(object, getActiveDepsgraph())
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
def cellFracture(bm, parameters, wm):
    points = [Vector([0, 0, 0])]
    fillInner = False
    shrink = 0
    nCloseFinds = 14
    if parameters is not None:
        points, fillInner, shrink, nCloseFinds, materialIndex = parameters
    locators = findLocators(points, nCloseFinds, shrink, wm)
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
            if fillInner:
                surround = [e for e in res['geom_cut']
                            if isinstance(e, bmesh.types.BMEdge)]
                fres = bmesh.ops.edgenet_prepare(bMesh, edges=surround)
                bmesh.ops.edgeloop_fill(bMesh, edges=fres['edges'], mat_nr=materialIndex)

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
