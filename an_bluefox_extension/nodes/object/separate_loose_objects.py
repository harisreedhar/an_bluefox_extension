import bpy
from bpy.props import *
from mathutils import Vector, Matrix
from animation_nodes . base_types import AnimationNode, VectorizedSocket
from . object_utils import removeObjectsFromCollection, setOrigin, setIDKeys
from animation_nodes . utils.depsgraph import getActiveDepsgraph, getEvaluatedID

dataByIdentifier = {}

class BF_SeparateLooseObjectsNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_SeparateLooseObjectsNode"
    bl_label = "Separate Loose Objects"
    errorHandlingType = "EXCEPTION"
    options = {"NOT_IN_SUBPROGRAM"}

    useObjectList  : VectorizedSocket.newProperty()

    collection     : PointerProperty(type = bpy.types.Collection, description = "Output Collection", update = AnimationNode.refresh)
    setObjectOrgin : BoolProperty(default = True, description = "", update = AnimationNode.refresh)
    setObjectIDKey : BoolProperty(default = True, description = "", update = AnimationNode.refresh)
    forceUpdateTree: BoolProperty(default = True, description = "", update = AnimationNode.refresh)

    def create(self):
        self.newInput(VectorizedSocket("Object", "useObjectList",
            ("Object", "object", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Objects", "object")))
        self.newOutput("Object List", "Objects", "objects")

    def draw(self, layout):
        col = layout.column()
        col.scale_y = 1.5
        self.invokeFunction(col, "invokeSeparateFunction",
                            text="Update",
                            description="Separate object by loose parts",
                            icon="FILE_REFRESH")

        col = layout.column(align = True)
        row = col.row(align = True)
        row.prop(self, "collection", text = "")
        if self.collection is None:
            self.invokeFunction(row, "createCollection",
                                text="",
                                description="Create new output collection",
                                icon = "PLUS")

    def drawAdvanced(self, layout):
        layout.prop(self, "setObjectOrgin", text="Set origin to geometry center")
        layout.prop(self, "setObjectIDKey", text="Set object ID keys")
        layout.separator()
        layout.prop(self, "forceUpdateTree", text="Force execute node tree")

    def execute(self, object):
        objects = object if self.useObjectList else [object]
        dataByIdentifier[self.identifier] = objects
        collection = self.collection
        return list(getattr(collection, "objects", []))

    def invokeSeparateFunction(self):
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        wm.progress_update(1)

        if self.forceUpdateTree:
            tree = bpy.data.node_groups.get(self.id_data.name)
            tree.execute()

        objects = dataByIdentifier.get(self.identifier)
        collection = self.collection
        if None in objects or collection is None:
            return

        removeObjectsFromCollection(collection)

        try:
            totalObjects = len(objects)
            for i, object in enumerate(objects):
                separateObjectByLooseParts(object, collection, self.setObjectOrgin, self.setObjectIDKey)
                wm.progress_update(int((i/totalObjects)*100))
        except Exception as e:
            print("Object separation failed:")
            print(str(e))

        self.refresh()
        wm.progress_end()
        return

    def createCollection(self):
        collection = bpy.data.collections.new('AN_Separated_Objects')
        bpy.context.scene.collection.children.link(collection)
        self.collection = collection

    def duplicate(self):
        self.collection = None

    def delete(self):
        keys = list(dataByIdentifier.keys())
        for key in keys:
            if key.startswith(self.identifier):
                dataByIdentifier.pop(key)

def separateObjectByLooseParts(object, collection, setObjectOrgin, setObjectIDKey):
    if object.type != "MESH":
        return
    if object.mode != "OBJECT":
        return

    data = object.data.copy()
    matrixWorld = object.matrix_world
    data.transform(matrixWorld)
    objName = object.name + "_part.000"

    ob = bpy.data.objects.get(objName)
    if ob:
        bpy.data.objects.remove(ob)

    ob = bpy.data.objects.new(objName, data)
    collection.objects.link(ob)

    bpy.ops.object.select_all(action = "DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.mesh.separate(type = 'LOOSE')
    objects = bpy.context.selected_objects
    if setObjectOrgin:
        setOrigin(objects)
    if setObjectIDKey:
        setIDKeys(objects)
    bpy.ops.object.select_all(action = "DESELECT")
