from . perlin1234 cimport (
    noise1, noise2, noise3, noise4,
    pnoise1, pnoise2, pnoise3, pnoise4,
)

cdef float perlin1D(float x):
    return noise1(x)
cdef float perlin2D(float x, float y):
    return noise2(x, y)
cdef float perlin3D(float x, float y, float z):
    return noise3(x, y, z)
cdef float perlin4D(float x, float y, float z, float w):
    return noise4(x, y, z, w)

cdef float periodicPerlin1D(float x, int px):
    return pnoise1(x, px)
cdef float periodicPerlin2D(float x, float y, int px, int py):
    return pnoise2(x, y, px, py)
cdef float periodicPerlin3D(float x, float y, float z, int px, int py, int pz):
    return pnoise3(x, y, z, px, py, pz)
cdef float periodicPerlin4D(float x, float y, float z, float w, int px, int py, int pz, int pw):
    return pnoise4(x, y, z, w, px, py, pz, pw)
