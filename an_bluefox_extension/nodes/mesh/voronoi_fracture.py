import bpy
import bmesh
import mathutils
from bpy.props import *
from animation_nodes . base_types import AnimationNode
from ... utils.cache_node import cacheHelper, prepareCache
from animation_nodes . nodes . mesh . bmesh_create import getBMeshFromMesh
from animation_nodes . data_structures import (
    Vector3DList, EdgeIndicesList,
    PolygonIndicesList, LongList,
    Mesh, Matrix4x4List
)

class BF_VoronoiFractureNode(bpy.types.Node, AnimationNode, cacheHelper):
    bl_idname = "an_bf_VoronoiFractureNode"
    bl_label = "Voronoi Fracture"
    bl_width_default = 150

    searchAmount: IntProperty(description = "Amount of nearest points for KD-Tree evaluation.",
                         default = 50, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Mesh", "Mesh", "source")
        self.newInput("Vector List", "Points", "points")
        self.newInput("Boolean", "Shell Only", "shellOnly", value = False)
        self.newInput("Float", "Offset", "offset")
        self.newOutput("Mesh List", "Meshes", "meshes")
        self.newOutput("Matrix List", "Matrices", "matrices")

    def draw(self, layout):
        self.drawInvokeUpdate(layout, "resetCache")
        layout.prop(self, "searchAmount", text = "Search Amount")

    def drawAdvanced(self, layout):
        self.drawUpdateType(layout)

    @prepareCache
    def execute(self, source, points, shellOnly, offset):
        cachedValue = self.getCacheValue()
        if self.updateType == "REALTIME" or cachedValue is None:
            meshes, matrices = meshVoronoiFracture(source, points, shellOnly, offset, self.searchAmount)
            self.setCacheValue((meshes, matrices))
            return meshes, matrices

        return cachedValue[0], cachedValue[1].copy()

    def resetCache(self):
        self.setCacheToNone(self.identifier)

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

    return (meshList, matrixList)

def getMeshFromBMesh(bMesh):
    try:
        vertices = Vector3DList.fromValues(v.co for v in bMesh.verts)
        edges = EdgeIndicesList.fromValues(tuple(v.index for v in edge.verts) for edge in bMesh.edges)
        polygons = PolygonIndicesList.fromValues(tuple(v.index for v in face.verts) for face in bMesh.faces)
        materialIndices = LongList.fromValues(face.material_index for face in bMesh.faces)
        return Mesh(vertices, edges, polygons, materialIndices)
    except:
        return Mesh()
