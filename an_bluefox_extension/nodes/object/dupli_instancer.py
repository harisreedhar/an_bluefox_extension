import bpy
import bmesh
from bpy.props import *
from animation_nodes . utils . layout import writeText
from animation_nodes . base_types import AnimationNode
from animation_nodes . nodes . mesh . c_utils import replicateMesh
from animation_nodes . events import propertyChanged, executionCodeChanged
from animation_nodes . nodes . mesh . generation . unity_triangle import mesh as unitytriangle
from animation_nodes . data_structures import (Mesh, Vector3DList, EdgeIndicesList, PolygonIndicesList)

dupliModeItems = [
    ("VERTS", "Vertices", "Instance on vertices", "", 0),
    ("FACES", "Faces", "Instance on Faces", "", 1),
    ("COLLECTION", "Collection", "Instance a collection", "", 2)
]

lastChild = {}

class BF_DupliInstancerNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_DupliInstancer"
    bl_label = "Dupli Instancer"
    errorHandlingType = "EXCEPTION"
    bl_width_default = 160

    useDisplay : BoolProperty(name = "Display Instancer", default = True, update = propertyChanged)
    useRender : BoolProperty(name = "Render Instancer", default = True, update = propertyChanged)

    mode : EnumProperty(name = "Mode", default = "VERTS",
        items = dupliModeItems, update = AnimationNode.refresh)

    def create(self):
        if self.mode != "COLLECTION":
            socket = self.newInput("Object", "Parent", "parent")
            socket.defaultDrawType = "PROPERTY_ONLY"
            socket.objectCreationType = "MESH"
            self.newInput("Object", "Child", "child")
            self.newInput("Matrix List", "Matrices", "matrices")
            self.newInput("Vector", "Location", "location", hide = True)
            self.newInput("Euler", "Rotation", "rotation", hide = True)
            self.newInput("Vector", "Scale", "scale", value = (1,1,1), hide = True)
        if self.mode == "COLLECTION":
            self.newInput("Object", "parent", "parent")
            self.newInput("Collection", "Collection", "collection", defaultDrawType = "PROPERTY_ONLY")
        elif self.mode == "VERTS":
            self.newInput("Boolean", "Align to Normal", "align")
        elif self.mode == "FACES":
            self.newInput("Boolean", "Scale by Face", "scaleByFace")
            self.newInput("Float", "Factor", "factor", value = 1.0)

        self.newOutput("Object", "Parent", "object")

    def draw(self, layout):
        row = layout.row(align = True)
        subrow = row.row(align = True)
        subrow.prop(self, "mode", text = "")
        subrow.prop(self, "useDisplay", index = 1, text = "", icon = "RESTRICT_VIEW_OFF")
        subrow.prop(self, "useRender", index = 2, text = "", icon = "RESTRICT_RENDER_OFF")

    def getExecutionFunctionName(self):
        if self.mode == "VERTS":
            return "execute_Verts"
        elif self.mode == "FACES":
            return "execute_Faces"
        elif self.mode == "COLLECTION":
            return "execute_Collection"

    def execute_Verts(self, parent, child, matrices, location, rotation, scale, align):
        if self.isValidObject(parent):
            mesh = parent.data
            replicatedMesh = self.getReplicatedMesh(matrices)
            self.setMesh(mesh, replicatedMesh)
        parentOut = parent

        if parent == None or child == None or parent == child:
            if parent != None and parent.instance_type:
                parent.instance_type = "NONE"
        else:
            self.set_Child_Parent_and_Transform(child, parent, location, rotation, scale)
            parent.instance_type = "VERTS"
            parent.use_instance_vertices_rotation = align
            self.set_instancer_visibility(parent)

        return parentOut

    def execute_Faces(self, parent, child, matrices, location, rotation, scale, scaleByFace, factor):
        if self.isValidObject(parent):
            mesh = parent.data
            replicatedMesh = self.getReplicatedMesh(matrices)
            self.setMesh(mesh, replicatedMesh)
        parentOut = parent

        if parent == None or child == None or parent == child:
            if parent != None and parent.instance_type:
                parent.instance_type = "NONE"
        else:
            self.set_Child_Parent_and_Transform(child, parent, location, rotation, scale)
            parent.instance_type = "FACES"
            parent.use_instance_faces_scale = scaleByFace
            parent.instance_faces_scale = factor
            self.set_instancer_visibility(parent)

        return parentOut

    def execute_Collection(self, parent, collection):
        parentOut = parent

        if parent == None or collection == None:
            if parent != None and parent.instance_type:
                parent.instance_type = "NONE"
        else:
            try:
                parent.instance_type = "COLLECTION"
                parent.instance_collection = collection
                self.set_instancer_visibility(parent)
            except TypeError:
                self.raiseErrorMessage("Parent should be an Empty")

        return parentOut

    def set_Child_Parent_and_Transform(self, child, parent, location, rotation, scale):
        child.location = location
        child.rotation_euler = rotation
        child.scale = scale
        child.parent = parent

    def set_instancer_visibility(self, parent):
        parent.show_instancer_for_viewport = self.useDisplay
        parent.show_instancer_for_render = self.useRender

    def getReplicatedMesh(self, matrices):
        if self.mode == "VERTS":
            vertexLocations = Vector3DList.fromValues([(0, 0, 0)])
            edgeIndices = EdgeIndicesList.fromValues([])
            polygonIndices = PolygonIndicesList.fromValues([])
            pointMesh = Mesh(vertexLocations, edgeIndices, polygonIndices)
            return replicateMesh(pointMesh, matrices)
        elif self.mode == "FACES":
            return replicateMesh(unitytriangle, matrices)

    def isValidObject(self, object):
        if object is None: return False
        if object.type != "MESH":
            self.setErrorMessage("Object is not a mesh object.")
            return False
        if object.mode != "OBJECT":
            self.setErrorMessage("Object is not in object mode.")
            return False
        return True

    def setMesh(self, outMesh, mesh):
        # clear existing mesh
        bmesh.new().to_mesh(outMesh)

        # allocate memory
        outMesh.vertices.add(len(mesh.vertices))
        outMesh.edges.add(len(mesh.edges))
        outMesh.loops.add(len(mesh.polygons.indices))
        outMesh.polygons.add(len(mesh.polygons))

        # Vertices
        outMesh.vertices.foreach_set("co", mesh.vertices.asMemoryView())
        outMesh.vertices.foreach_set("normal", mesh.getVertexNormals().asMemoryView())

        # Edges
        outMesh.edges.foreach_set("vertices", mesh.edges.asMemoryView())

        # Polygons
        outMesh.polygons.foreach_set("loop_total", mesh.polygons.polyLengths.asMemoryView())
        outMesh.polygons.foreach_set("loop_start", mesh.polygons.polyStarts.asMemoryView())
        outMesh.loops.foreach_set("vertex_index", mesh.polygons.indices.asMemoryView())
        outMesh.loops.foreach_set("edge_index", mesh.getLoopEdges().asMemoryView())
