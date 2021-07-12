import bpy
import bmesh
from mathutils import Vector, Matrix
from animation_nodes . utils.data_blocks import removeNotUsedDataBlock
from animation_nodes . utils.depsgraph import getActiveDepsgraph, getEvaluatedID

def getBMeshFromObject(object):
    bm = bmesh.new()
    if getattr(object, "type", "") != "MESH":
        return bm
    bm.from_object(object, getActiveDepsgraph())
    evaluatedObject = getEvaluatedID(object)
    bm.transform(evaluatedObject.matrix_world)
    return bm

def bmeshListToObjects(bmList, objectName, collection):
    objectList = []
    for i, bm in enumerate(bmList):
        name = objectName + str(i).zfill(3)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        ob = bpy.data.objects.new(name, me)
        collection.objects.link(ob)
        objectList.append(ob)
    return objectList

def removeObjectsFromCollection(collection):
    for obj in collection.objects:
        data = obj.data
        type = obj.type
        bpy.data.objects.remove(obj)
        if data is None: return
        if data.users == 0:
            removeNotUsedDataBlock(data, type)

def setOrigin(objects):
    for object in objects:
        mesh = object.data
        matrixWorld = object.matrix_world
        origin = sum((v.co for v in mesh.vertices), Vector()) / len(mesh.vertices)
        T = Matrix.Translation(-origin)
        mesh.transform(T)
        matrixWorld.translation = matrixWorld @ origin

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

def setIDKeys(objects):
    for object in objects:
        object.id_keys.set("Transforms", "Initial Transforms",
                           (object.location, object.rotation_euler, object.scale))
