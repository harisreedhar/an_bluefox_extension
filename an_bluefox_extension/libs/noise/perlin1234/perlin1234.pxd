cdef extern from "noise1234.h":
    # 1D, 2D, 3D and 4D float Perlin noise
    float noise1(float x)
    float noise2(float x, float y)
    float noise3(float x, float y, float z)
    float noise4(float x, float y, float z, float w)

    # 1D, 2D, 3D and 4D float Perlin periodic noise
    float pnoise1(float x, int px )
    float pnoise2(float x, float y, int px, int py)
    float pnoise3(float x, float y, float z, int px, int py, int pz)
    float pnoise4(float x, float y, float z, float w,
                int px, int py, int pz, int pw)
