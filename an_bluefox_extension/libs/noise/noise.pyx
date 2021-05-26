from . perlin1234 cimport (
    perlin1D, perlin2D,
    perlin3D, perlin4D,
    periodicPerlin1D,
    periodicPerlin2D,
    periodicPerlin3D,
    periodicPerlin4D
)
from . simplex1234 cimport simplex1D, simplex2D, simplex3D, simplex4D
from animation_nodes . math cimport Vector3
from animation_nodes . data_structures cimport Vector3DList, FloatList, VirtualVector3DList, VirtualDoubleList

cdef float fPerlin4D(float x, float y, float z, float w, int octaves):

    cdef float nScale = 1.0
    cdef float tScale = 0.0
    cdef float value = 0.0
    cdef Py_ssize_t i

    for i in range(octaves):
        value += perlin4D(x, y, z, w) * nScale
        tScale += nScale
        nScale *= 0.5
        x *= 2
        y *= 2
        z *= 2
        w *= 2
    return value / tScale

cdef float fPeriodicPerlin4D(float x, float y, float z, float w,
                int px, int py, int pz, int pw, int octaves):

    cdef float nScale = 1.0
    cdef float tScale = 0.0
    cdef float value = 0.0
    cdef Py_ssize_t i

    for i in range(octaves):
        value += periodicPerlin4D(x, y, z, w, px, py, pz, pw) * nScale
        tScale += nScale
        nScale *= 0.5
        x *= 2
        y *= 2
        z *= 2
        w *= 2
    return value / tScale

cdef float fSimplex4D(float x, float y, float z, float w, int octaves):

    cdef float nScale = 1.0
    cdef float tScale = 0.0
    cdef float value = 0.0
    cdef Py_ssize_t i

    for i in range(octaves):
        value += simplex4D(x, y, z, w) * nScale
        tScale += nScale
        nScale *= 0.5
        x *= 2
        y *= 2
        z *= 2
        w *= 2
    return value / tScale

####################################### Python Functions #######################################

def pyPerlin4D(VirtualVector3DList vectors,
               VirtualDoubleList w,
               Py_ssize_t amount,
               Py_ssize_t octaves,
               float amplitude):
    cdef Py_ssize_t i
    cdef FloatList output = FloatList(length = amount)
    for i in range(amount):
        output.data[i] = fPerlin4D(vectors.get(i).x,
                                  vectors.get(i).y,
                                  vectors.get(i).z,
                                  w.get(i),
                                  octaves) * amplitude
    return output

def pyPeriodicPerlin4D(VirtualVector3DList vectors,
                       VirtualDoubleList w,
                       int pX,
                       int pY,
                       int pZ,
                       int pW,
                       Py_ssize_t amount,
                       Py_ssize_t octaves,
                       float amplitude):
    cdef Py_ssize_t i
    cdef FloatList output = FloatList(length = amount)
    pX = max(abs(pX), 1)
    pY = max(abs(pY), 1)
    pZ = max(abs(pZ), 1)
    pW = max(abs(pW), 1)
    for i in range(amount):
        output.data[i] = fPeriodicPerlin4D(vectors.get(i).x,
                                           vectors.get(i).y,
                                           vectors.get(i).z,
                                           w.get(i),
                                           pX, pY, pZ, pW,
                                           octaves) * amplitude
    return output

def pySimplex4D(VirtualVector3DList vectors,
               VirtualDoubleList w,
               Py_ssize_t amount,
               Py_ssize_t octaves,
               float amplitude):
    cdef Py_ssize_t i
    cdef FloatList output = FloatList(length = amount)
    for i in range(amount):
        output.data[i] = fSimplex4D(vectors.get(i).x,
                                  vectors.get(i).y,
                                  vectors.get(i).z,
                                  w.get(i),
                                  octaves) * amplitude
    return output

def setFrequencyAndOffset(Vector3DList vectors, float frequency,
                       float xOff, float yOff, float zOff):
    cdef Py_ssize_t i
    cdef Py_ssize_t amount = vectors.length
    cdef Vector3DList output = Vector3DList(length = amount)
    for i in range(amount):
        output.data[i].x = vectors.data[i].x * frequency + xOff
        output.data[i].y = vectors.data[i].y * frequency + yOff
        output.data[i].z = vectors.data[i].z * frequency + zOff
    return output
