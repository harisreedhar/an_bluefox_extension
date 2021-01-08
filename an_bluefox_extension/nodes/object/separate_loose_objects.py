import bpy
from bpy.props import *
from mathutils import Vector, Matrix
from animation_nodes . base_types import AnimationNode
from animation_nodes . utils.objects import enterObjectMode
from animation_nodes . nodes.container_provider import getMainObjectContainer
from animation_nodes . utils.blender_ui import executeInAreaType, iterActiveSpacesByType

object_in = None

class SeparateLooseObjectsNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_SeparateLooseObjectsNode"
    bl_label = "Separate Loose Objects"
    bl_width_default = 150
    options = {"NOT_IN_SUBPROGRAM"}

    def create(self):
        self.newInput("Object", "Object", "object", defaultDrawType = "PROPERTY_ONLY")
        self.newOutput("Object List", "Objects", "objects")

    def draw(self, layout):
        self.invokeFunction(layout, "invokeSeparateFunction",
            text = "Update",
            description = "separate loose parts from the source object",
            icon = "FILE_REFRESH")

    def execute(self, object):
        global object_in
        object_in = object

        if self.inputs[0].isUnlinked:
            self.delete()

        if object_in is None:
            return []

        collection = getCollection(self.getSubCollectionName())
        return list(getattr(collection, "objects", []))

    def invokeSeparateFunction(self):
        if object_in is not None:
            separateObjectByLooseParts(object_in, self.getSubCollectionName())
            self.refresh()

    def getSubCollectionName(self):
        return "Loose_Objects" + self.identifier

    def delete(self):
        subCollection = getCollection(self.getSubCollectionName())
        if subCollection:
            for object in subCollection.objects:
                bpy.data.objects.remove(object)
            bpy.data.collections.remove(subCollection)

@executeInAreaType("VIEW_3D")
def separateObjectByLooseParts(object, name):
    enterObjectMode()

    data = object.data.copy()
    objName = object.name + "_part.000"
    ob = bpy.data.objects.get(objName)
    if ob:
        bpy.data.objects.remove(ob)

    ob = bpy.data.objects.new(objName, data)
    subCollection = getCollection(name)

    for o in subCollection.objects:
        bpy.data.objects.remove(o)

    subCollection.objects.link(ob)
    bpy.ops.object.select_all(action = "DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.mesh.separate(type = 'LOOSE')
    setOrigin(subCollection.objects)
    setIDKeys(subCollection.objects)
    bpy.ops.object.select_all(action = "DESELECT")

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
        origin = sum((v.co for v in mesh.vertices), Vector()) / len(mesh.vertices)
        T = Matrix.Translation(-origin)
        mesh.transform(T)
        matrixWorld.translation = matrixWorld @ origin

def setIDKeys(objects):
    for object in objects:
        object.id_keys.set("Transforms", "Initial Transforms",
                (object.location, object.rotation_euler, object.scale))
