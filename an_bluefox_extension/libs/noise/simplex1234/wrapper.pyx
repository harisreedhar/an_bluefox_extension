from . simplex1234 cimport snoise1, snoise2, snoise3, snoise4

cdef float simplex1D(float x):
    return snoise1(x)
cdef float simplex2D(float x, float y):
    return snoise2(x, y)
cdef float simplex3D(float x, float y, float z):
    return snoise3(x, y, z)
cdef float simplex4D(float x, float y, float z, float w):
    return snoise4(x, y, z, w)
