import cython

from animation_nodes.data_structures cimport PolygonIndicesList

from libc.math cimport sin, cos, fabs

from animation_nodes . math cimport (
     Quaternion, Euler3, Vector3, Matrix4,
     setTranslationRotationScaleMatrix, quaternionNormalize_InPlace,
     lengthVec3
)

from animation_nodes . data_structures cimport (
    Vector3DList, DoubleList, FloatList, EulerList, Matrix4x4List,
    QuaternionList, VirtualQuaternionList,
    VirtualVector3DList, VirtualEulerList, VirtualMatrix4x4List,
    VirtualDoubleList, VirtualFloatList, Mesh,
    Interpolation, EdgeIndicesList
)

from animation_nodes . nodes . number . c_utils import mapRange_DoubleList

cdef c_polygonIndices_From_triArray(unsigned int [:, :] triArray):
    cdef int i
    cdef int triAmount = triArray.shape[0]
    cdef int indiceAmount = triArray.size
    cdef PolygonIndicesList newPolygons = PolygonIndicesList(
                                          indicesAmount = indiceAmount,
                                          polygonAmount = triAmount)
    cdef unsigned int *newIndices = newPolygons.indices.data
    cdef unsigned int *newPolyStarts = newPolygons.polyStarts.data
    cdef unsigned int *newPolyLengths = newPolygons.polyLengths.data

    cdef unsigned int index = 0
    for i in range(triAmount):
        newPolyStarts[i] = index
        newPolyLengths[i] = 3

        newIndices[index] = triArray[i, 0]
        newIndices[index+1] = triArray[i, 1]
        newIndices[index+2] = triArray[i, 2]

        index += 3
    return newPolygons

def polygonIndices_From_triArray(triArray):
    return c_polygonIndices_From_triArray(triArray.astype('uint32'))

cdef c_stretchDeform(Vector3 *point, float factor, str axis):
    cdef float x = point.x
    cdef float y = point.y
    cdef float z = point.z
    cdef float scale = 0

    if axis == 'X':
        scale = (x * x * factor - factor + 1.0)
        point.x = x * (1.0 + factor)
        point.y = y * scale
        point.z = z * scale

    if axis == 'Y':
        scale = (y * y * factor - factor + 1.0)
        point.x = x * scale
        point.y = y * (1.0 + factor)
        point.z = z * scale

    if axis == 'Z':
        scale = (z * z * factor - factor + 1.0)
        point.x = x * scale
        point.y = y * scale
        point.z = z * (1.0 + factor)

cdef c_taperDeform(Vector3 *point, float factor, str axis):
    cdef float x = point.x
    cdef float y = point.y
    cdef float z = point.z
    cdef float scale = 0

    if axis == 'X':
        scale = x * factor
        point.x = x
        point.y = y + y * scale
        point.z = z + z * scale

    if axis == 'Y':
        scale = y * factor
        point.x = x + x * scale
        point.y = y
        point.z = z + z * scale

    if axis == 'Z':
        scale = z * factor
        point.x = x + x * scale
        point.y = y + y * scale
        point.z = z

cdef c_twistDeform(Vector3 *point, float factor, str axis):
    cdef float x = point.x
    cdef float y = point.y
    cdef float z = point.z
    cdef float theta, sint, cost

    if axis == 'X':
        theta = x * factor
        sint = sin(theta)
        cost = cos(theta)
        point.x = x
        point.y = y * cost - z * sint
        point.z = y * sint + z * cost

    if axis == 'Y':
        theta = y * factor
        sint = sin(theta)
        cost = cos(theta)
        point.x = x * cost - z * sint
        point.y = y
        point.z = x * sint + z * cost

    if axis == 'Z':
        theta = z * factor
        sint = sin(theta)
        cost = cos(theta)
        point.x = x * cost - y * sint
        point.y = x * sint + y * cost
        point.z = z

cdef c_bendDeform(Vector3 *point, float factor, str axis):
    cdef float x = point.x
    cdef float y = point.y
    cdef float z = point.z
    cdef float theta, sint, cost

    if factor == 0:
        factor = 0.00001

    if axis == 'X':
        theta = z * factor
        sint = sin(theta)
        cost = cos(theta)
        point.x = x
        point.y = (y - 1/factor) * cost + 1.0 / factor
        point.z = -(y - 1/factor) * sint

    if axis == 'Y':
        theta = z * factor
        sint = sin(theta)
        cost = cos(theta)
        point.x = (x - 1.0 / factor) * cost + 1.0 / factor
        point.y = y
        point.z = -(x - 1.0 / factor) * sint

    if axis == 'Z':
        theta = x * factor
        sint = sin(theta)
        cost = cos(theta)
        point.x = -(y - 1.0 / factor) * sint
        point.y = (y - 1.0 / factor) * cost + 1.0 / factor
        point.z = z

def stretchDeform(Vector3DList points, FloatList strengths, float factor, str axis = 'Z'):
    cdef Py_ssize_t i
    cdef int amount = points.length
    for i in range(amount):
        c_stretchDeform(&points.data[i], strengths.data[i]*factor, axis)
    return points

def taperDeform(Vector3DList points, FloatList strengths, float factor, str axis = 'Z'):
    cdef Py_ssize_t i
    cdef int amount = points.length
    for i in range(amount):
        c_taperDeform(&points.data[i], strengths.data[i]*factor, axis)
    return points

def twistDeform(Vector3DList points, FloatList strengths, float factor, str axis = 'Z'):
    cdef Py_ssize_t i
    cdef int amount = points.length
    for i in range(amount):
        c_twistDeform(&points.data[i], strengths.data[i]*factor, axis)
    return points

def bendDeform(Vector3DList points, FloatList strengths, float factor, str axis = 'Z'):
    cdef Py_ssize_t i
    cdef int amount = points.length
    for i in range(amount):
        c_bendDeform(&points.data[i], strengths.data[i]*factor, axis)
    return points

@cython.cdivision(True)
def findMeshTension(Mesh mesh1, Mesh mesh2, float intensity, float influence):
    cdef EdgeIndicesList mesh1Edges = mesh1.edges
    cdef Vector3DList mesh1Vertices = mesh1.vertices
    cdef Vector3DList mesh2Vertices = mesh2.vertices

    cdef Py_ssize_t edgeAmount = mesh1Edges.length
    cdef Py_ssize_t i, index1, index2

    cdef Vector3 v1
    cdef Vector3 v2
    cdef float factor

    cdef DoubleList weights = DoubleList(length = mesh1Vertices.length)
    weights.fill(0)

    for i in range(edgeAmount):
        index1 = <Py_ssize_t>mesh1Edges.data[i].v1
        index2 = <Py_ssize_t>mesh1Edges.data[i].v2

        v1.x = mesh1Vertices.data[index1].x - mesh1Vertices.data[index2].x
        v1.y = mesh1Vertices.data[index1].y - mesh1Vertices.data[index2].y
        v1.z = mesh1Vertices.data[index1].z - mesh1Vertices.data[index2].z

        v2.x = mesh2Vertices.data[index1].x - mesh2Vertices.data[index2].x
        v2.y = mesh2Vertices.data[index1].y - mesh2Vertices.data[index2].y
        v2.z = mesh2Vertices.data[index1].z - mesh2Vertices.data[index2].z

        factor = (lengthVec3(&v1) / lengthVec3(&v2)) / 2

        influence = fabs(influence)
        weights.data[index1] -= factor
        weights.data[index2] -= factor
        weights.data[index1] += influence
        weights.data[index2] += influence

    return mapRange_DoubleList(weights, True, 0, 1, -intensity, intensity)
