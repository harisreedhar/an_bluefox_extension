import bpy
import bmesh
import mathutils
from bpy.props import *
from animation_nodes . base_types import AnimationNode
from animation_nodes . nodes . mesh . bmesh_create import getBMeshFromMesh
from animation_nodes . data_structures import (
    Vector3DList, EdgeIndicesList,
    PolygonIndicesList, LongList,
    Mesh, Matrix4x4List
)

updateTypeItems = [("REALTIME", "Real Time", "", "NONE", 0),
                   ("CACHED", "Cached", "", "NONE", 1)]

class BF_VoronoiFractureNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_VoronoiFractureNode"
    bl_label = "Voronoi Fracture"
    bl_width_default = 160

    searchAmount: IntProperty(description = "Amount of nearest points for KD-Tree evaluation",
                         default = 50, update = AnimationNode.refresh)
    updateType: EnumProperty(items = updateTypeItems, update = AnimationNode.refresh, default = "REALTIME")

    executionIndex = 0
    executionCache = {}

    def create(self):
        self.newInput("Mesh", "Mesh", "source")
        self.newInput("Vector List", "Points", "points")
        self.newInput("Boolean", "Shell Only", "shellOnly", value = False)
        self.newInput("Float", "Offset", "offset")
        self.newOutput("Mesh List", "Meshes", "meshes")
        self.newOutput("Matrix List", "Matrices", "matrices")

    def draw(self, layout):
        col = layout.column()
        col.scale_y = 1.5
        if self.updateType == "CACHED":
            self.invokeFunction(col, "resetVoronoiCache",
                                text="Update",
                                description="Update cache",
                                icon="FILE_REFRESH")
        col = layout.column(align = True)
        row = col.row(align = True)
        row.prop(self, "updateType", expand = True)
        row1 = col.row(align = True)
        row1.prop(self, "searchAmount", text = "Search Amount")

    def execute(self, source, points, shellOnly, offset):
        self.executionIndex += 1
        identifier = self.identifier + str(self.executionIndex)
        cachedValue = self.executionCache.get(identifier)

        if self.updateType == "REALTIME" or cachedValue is None:
            result = meshVoronoiFracture(source, points, shellOnly, offset, self.searchAmount)
            self.executionCache[identifier] = result
            return result[0], result[1]

        return cachedValue[0], cachedValue[1].copy()

    def resetVoronoiCache(self):
        for key in self.executionCache.keys():
            if key.startswith(self.identifier):
                self.executionCache[key] = None
        self.refresh()

# Reference: https://github.com/nortikin/sverchok/blob/master/node_scripts/SNLite_templates/demo/voronoi_3d.py
def meshVoronoiFracture(mesh, points, shellOnly, offset, amount):
    bm = getBMeshFromMesh(mesh)
    size = len(points)
    kd = mathutils.kdtree.KDTree(size)
    for i, vector in enumerate(points):
        kd.insert(vector, i)
    kd.balance()
    identityMatrix = mathutils.Matrix.Identity(4)
    meshList = []
    matrixList = Matrix4x4List()

    for i, vertex in enumerate(points):
        bMesh = bm.copy()
        neighbours = kd.find_n(vertex, amount)
        for coord, index, distance in neighbours:
            if index == i:
                continue
            normal = coord - vertex
            point = normal * 0.5 * (1 - offset) + vertex

            geomIn = bMesh.verts[:] + bMesh.edges[:] + bMesh.faces[:]
            res = bmesh.ops.bisect_plane(
                bMesh, geom=geomIn, dist=0.00001,
                plane_co=point, plane_no=normal, use_snap_center=False,
                clear_outer=True, clear_inner=False
            )
            if not shellOnly:
                _edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
                _res = bmesh.ops.edgenet_prepare(bMesh, edges=_edges)
                bmesh.ops.edgeloop_fill(bMesh, edges=_res['edges'])

        if len(bMesh.faces) > 0:
            mesh = getMeshFromBMesh(bMesh)
            meanCenter = mesh.vertices.getAverageOfElements()
            mesh.move(-meanCenter)
            meshList.append(mesh)
            matrixList.append(identityMatrix.Translation(meanCenter))
            bMesh.free()

    return [meshList, matrixList]

def getMeshFromBMesh(bMesh):
    try:
        vertices = Vector3DList.fromValues(v.co for v in bMesh.verts)
        edges = EdgeIndicesList.fromValues(tuple(v.index for v in edge.verts) for edge in bMesh.edges)
        polygons = PolygonIndicesList.fromValues(tuple(v.index for v in face.verts) for face in bMesh.faces)
        materialIndices = LongList.fromValues(face.material_index for face in bMesh.faces)
        return Mesh(vertices, edges, polygons, materialIndices)
    except:
        return Mesh()
