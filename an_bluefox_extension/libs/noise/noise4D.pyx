from . common cimport fastFloor, lerp
from libc . math cimport abs, fabs, sqrt
from animation_nodes . math cimport Vector3, Vector4
from . common cimport fastFloor, lerp, addV4, mulV4_single, subV4, floorV4, hash44
from animation_nodes . data_structures cimport FloatList, DoubleList, Vector3DList, VirtualDoubleList, VirtualVector3DList


# https://github.com/stegu/perlin-noise/blob/master/src/noise1234.c

cdef unsigned char perm[512]

perm[:] = [151,160,137,91,90,15,
  131,13,201,95,96,53,194,233,7,225,140,36,103,30,69,142,8,99,37,240,21,10,23,
  190, 6,148,247,120,234,75,0,26,197,62,94,252,219,203,117,35,11,32,57,177,33,
  88,237,149,56,87,174,20,125,136,171,168, 68,175,74,165,71,134,139,48,27,166,
  77,146,158,231,83,111,229,122,60,211,133,230,220,105,92,41,55,46,245,40,244,
  102,143,54, 65,25,63,161, 1,216,80,73,209,76,132,187,208, 89,18,169,200,196,
  135,130,116,188,159,86,164,100,109,198,173,186, 3,64,52,217,226,250,124,123,
  5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,16,58,17,182,189,28,42,
  223,183,170,213,119,248,152, 2,44,154,163, 70,221,153,101,155,167, 43,172,9,
  129,22,39,253, 19,98,108,110,79,113,224,232,178,185, 112,104,218,246,97,228,
  251,34,242,193,238,210,144,12,191,179,162,241, 81,51,145,235,249,14,239,107,
  49,192,214, 31,181,199,106,157,184, 84,204,176,115,121,50,45,127, 4,150,254,
  138,236,205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180,
  151,160,137,91,90,15,
  131,13,201,95,96,53,194,233,7,225,140,36,103,30,69,142,8,99,37,240,21,10,23,
  190, 6,148,247,120,234,75,0,26,197,62,94,252,219,203,117,35,11,32,57,177,33,
  88,237,149,56,87,174,20,125,136,171,168, 68,175,74,165,71,134,139,48,27,166,
  77,146,158,231,83,111,229,122,60,211,133,230,220,105,92,41,55,46,245,40,244,
  102,143,54, 65,25,63,161, 1,216,80,73,209,76,132,187,208, 89,18,169,200,196,
  135,130,116,188,159,86,164,100,109,198,173,186, 3,64,52,217,226,250,124,123,
  5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,16,58,17,182,189,28,42,
  223,183,170,213,119,248,152, 2,44,154,163, 70,221,153,101,155,167, 43,172,9,
  129,22,39,253, 19,98,108,110,79,113,224,232,178,185, 112,104,218,246,97,228,
  251,34,242,193,238,210,144,12,191,179,162,241, 81,51,145,235,249,14,239,107,
  49,192,214, 31,181,199,106,157,184, 84,204,176,115,121,50,45,127, 4,150,254,
  138,236,205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180
]

cdef float fade(float t):
    return t * t * t * (t * (t * 6 - 15) + 10)

cdef float grad4(int hash, float x, float y, float z, float t):
    cdef int h = hash & 31
    cdef float u = x if h < 24 else y
    cdef float v = y if h < 16 else z
    cdef float w = z if h < 8 else t
    return (-u if (h & 1) else u) + (-v if (h & 2) else v) + (-w if (h & 4) else w)

#################################### 4D perlin noise ####################################

cdef float noise4(Vector3* vec, float w):
    cdef:
        int ix0, iy0, iz0, iw0, ix1, iy1, iz1, iw1
        float fx0, fy0, fz0, fw0, fx1, fy1, fz1, fw1
        float s, t, r, q
        float nxyz0, nxyz1, nxy0, nxy1, nx0, nx1, n0, n1

    ix0 = fastFloor(vec.x)
    iy0 = fastFloor(vec.y)
    iz0 = fastFloor(vec.z)
    iw0 = fastFloor(w)
    fx0 = vec.x - ix0
    fy0 = vec.y - iy0
    fz0 = vec.z - iz0
    fw0 = w - iw0
    fx1 = fx0 - 1.0
    fy1 = fy0 - 1.0
    fz1 = fz0 - 1.0
    fw1 = fw0 - 1.0
    ix1 = (ix0 + 1) & 0xff
    iy1 = (iy0 + 1) & 0xff
    iz1 = (iz0 + 1) & 0xff
    iw1 = (iw0 + 1) & 0xff
    ix0 = ix0 & 0xff
    iy0 = iy0 & 0xff
    iz0 = iz0 & 0xff
    iw0 = iw0 & 0xff

    q = fade(fw0)
    r = fade(fz0)
    t = fade(fy0)
    s = fade(fx0)

    nxyz0 = grad4(perm[ix0 + perm[iy0 + perm[iz0 + perm[iw0]]]], fx0, fy0, fz0, fw0)
    nxyz1 = grad4(perm[ix0 + perm[iy0 + perm[iz0 + perm[iw1]]]], fx0, fy0, fz0, fw1)
    nxy0 = lerp(q, nxyz0, nxyz1)

    nxyz0 = grad4(perm[ix0 + perm[iy0 + perm[iz1 + perm[iw0]]]], fx0, fy0, fz1, fw0)
    nxyz1 = grad4(perm[ix0 + perm[iy0 + perm[iz1 + perm[iw1]]]], fx0, fy0, fz1, fw1)
    nxy1 = lerp(q, nxyz0, nxyz1)

    nx0 = lerp(r, nxy0, nxy1)

    nxyz0 = grad4(perm[ix0 + perm[iy1 + perm[iz0 + perm[iw0]]]], fx0, fy1, fz0, fw0)
    nxyz1 = grad4(perm[ix0 + perm[iy1 + perm[iz0 + perm[iw1]]]], fx0, fy1, fz0, fw1)
    nxy0 = lerp(q, nxyz0, nxyz1)

    nxyz0 = grad4(perm[ix0 + perm[iy1 + perm[iz1 + perm[iw0]]]], fx0, fy1, fz1, fw0)
    nxyz1 = grad4(perm[ix0 + perm[iy1 + perm[iz1 + perm[iw1]]]], fx0, fy1, fz1, fw1)
    nxy1 = lerp(q, nxyz0, nxyz1)

    nx1 = lerp(r, nxy0, nxy1)

    n0 = lerp(t, nx0, nx1)

    nxyz0 = grad4(perm[ix1 + perm[iy0 + perm[iz0 + perm[iw0]]]], fx1, fy0, fz0, fw0)
    nxyz1 = grad4(perm[ix1 + perm[iy0 + perm[iz0 + perm[iw1]]]], fx1, fy0, fz0, fw1)
    nxy0 = lerp(q, nxyz0, nxyz1)

    nxyz0 = grad4(perm[ix1 + perm[iy0 + perm[iz1 + perm[iw0]]]], fx1, fy0, fz1, fw0)
    nxyz1 = grad4(perm[ix1 + perm[iy0 + perm[iz1 + perm[iw1]]]], fx1, fy0, fz1, fw1)
    nxy1 = lerp(q, nxyz0, nxyz1)

    nx0 = lerp(r, nxy0, nxy1)

    nxyz0 = grad4(perm[ix1 + perm[iy1 + perm[iz0 + perm[iw0]]]], fx1, fy1, fz0, fw0)
    nxyz1 = grad4(perm[ix1 + perm[iy1 + perm[iz0 + perm[iw1]]]], fx1, fy1, fz0, fw1)
    nxy0 = lerp(q, nxyz0, nxyz1)

    nxyz0 = grad4(perm[ix1 + perm[iy1 + perm[iz1 + perm[iw0]]]], fx1, fy1, fz1, fw0)
    nxyz1 = grad4(perm[ix1 + perm[iy1 + perm[iz1 + perm[iw1]]]], fx1, fy1, fz1, fw1)
    nxy1 = lerp(q, nxyz0, nxyz1)

    nx1 = lerp(r, nxy0, nxy1)

    n1 = lerp(t, nx0, nx1)

    return 0.87 * lerp(s, n0, n1)

################################# 4D periodic perlin noise #################################

cdef float pnoise4(Vector3* vec, float w, int px, int py, int pz, int pw):
    cdef:
        int ix0, iy0, iz0, iw0, ix1, iy1, iz1, iw1
        float fx0, fy0, fz0, fw0, fx1, fy1, fz1, fw1
        float s, t, r, q
        float nxyz0, nxyz1, nxy0, nxy1, nx0, nx1, n0, n1

    ix0 = fastFloor(vec.x)
    iy0 = fastFloor(vec.y)
    iz0 = fastFloor(vec.z)
    iw0 = fastFloor(w)
    fx0 = vec.x - ix0
    fy0 = vec.y - iy0
    fz0 = vec.z - iz0
    fw0 = w - iw0
    fx1 = fx0 - 1.0
    fy1 = fy0 - 1.0
    fz1 = fz0 - 1.0
    fw1 = fw0 - 1.0
    ix1 = ((ix0 + 1) % px) & 0xff
    iy1 = ((iy0 + 1) % py) & 0xff
    iz1 = ((iz0 + 1) % pz) & 0xff
    iw1 = ((iw0 + 1) % pw) & 0xff
    ix0 = (ix0 % px) & 0xff
    iy0 = (iy0 % py) & 0xff
    iz0 = (iz0 % pz) & 0xff
    iw0 = (iw0 % pw) & 0xff

    q = fade(fw0)
    r = fade(fz0)
    t = fade(fy0)
    s = fade(fx0)

    nxyz0 = grad4(perm[ix0 + perm[iy0 + perm[iz0 + perm[iw0]]]], fx0, fy0, fz0, fw0)
    nxyz1 = grad4(perm[ix0 + perm[iy0 + perm[iz0 + perm[iw1]]]], fx0, fy0, fz0, fw1)
    nxy0 = lerp(q, nxyz0, nxyz1)

    nxyz0 = grad4(perm[ix0 + perm[iy0 + perm[iz1 + perm[iw0]]]], fx0, fy0, fz1, fw0)
    nxyz1 = grad4(perm[ix0 + perm[iy0 + perm[iz1 + perm[iw1]]]], fx0, fy0, fz1, fw1)
    nxy1 = lerp(q, nxyz0, nxyz1)

    nx0 = lerp(r, nxy0, nxy1)

    nxyz0 = grad4(perm[ix0 + perm[iy1 + perm[iz0 + perm[iw0]]]], fx0, fy1, fz0, fw0)
    nxyz1 = grad4(perm[ix0 + perm[iy1 + perm[iz0 + perm[iw1]]]], fx0, fy1, fz0, fw1)
    nxy0 = lerp(q, nxyz0, nxyz1)

    nxyz0 = grad4(perm[ix0 + perm[iy1 + perm[iz1 + perm[iw0]]]], fx0, fy1, fz1, fw0)
    nxyz1 = grad4(perm[ix0 + perm[iy1 + perm[iz1 + perm[iw1]]]], fx0, fy1, fz1, fw1)
    nxy1 = lerp(q, nxyz0, nxyz1)

    nx1 = lerp(r, nxy0, nxy1)

    n0 = lerp(t, nx0, nx1)

    nxyz0 = grad4(perm[ix1 + perm[iy0 + perm[iz0 + perm[iw0]]]], fx1, fy0, fz0, fw0)
    nxyz1 = grad4(perm[ix1 + perm[iy0 + perm[iz0 + perm[iw1]]]], fx1, fy0, fz0, fw1)
    nxy0 = lerp(q, nxyz0, nxyz1)

    nxyz0 = grad4(perm[ix1 + perm[iy0 + perm[iz1 + perm[iw0]]]], fx1, fy0, fz1, fw0)
    nxyz1 = grad4(perm[ix1 + perm[iy0 + perm[iz1 + perm[iw1]]]], fx1, fy0, fz1, fw1)
    nxy1 = lerp(q, nxyz0, nxyz1)

    nx0 = lerp(r, nxy0, nxy1)

    nxyz0 = grad4(perm[ix1 + perm[iy1 + perm[iz0 + perm[iw0]]]], fx1, fy1, fz0, fw0)
    nxyz1 = grad4(perm[ix1 + perm[iy1 + perm[iz0 + perm[iw1]]]], fx1, fy1, fz0, fw1)
    nxy0 = lerp(q, nxyz0, nxyz1)

    nxyz0 = grad4(perm[ix1 + perm[iy1 + perm[iz1 + perm[iw0]]]], fx1, fy1, fz1, fw0)
    nxyz1 = grad4(perm[ix1 + perm[iy1 + perm[iz1 + perm[iw1]]]], fx1, fy1, fz1, fw1)
    nxy1 = lerp(q, nxyz0, nxyz1)

    nx1 = lerp(r, nxy0, nxy1)

    n1 = lerp(t, nx0, nx1)

    return 0.87 * lerp(s, n0, n1)

####################################### 4D fractal perlin noise #######################################

cdef float perlin4D_Single(Vector3* v, float w, float amplitude, float frequency, int octaves):
    cdef float value = 0
    cdef int i
    cdef Vector3 temp
    cdef float tempW
    temp.x = v.x * frequency
    temp.y = v.y * frequency
    temp.z = v.z * frequency
    tempW = w * frequency
    for i in range(octaves):
        value += amplitude * noise4(&temp, tempW)
        temp.x *= 2
        temp.y *= 2
        temp.z *= 2
        tempW *= 2
        amplitude *= 0.5
    return value

cdef float periodicPerlin4D_Single(Vector3* v,
                                   float w,
                                   int px,
                                   int py,
                                   int pz,
                                   int pw,
                                   float amplitude,
                                   float frequency,
                                   int octaves):
    cdef float value = 0
    cdef int i
    cdef Vector3 temp
    cdef float tempW
    temp.x = v.x * frequency
    temp.y = v.y * frequency
    temp.z = v.z * frequency
    tempW = w * frequency
    for i in range(octaves):
        value += amplitude * pnoise4(&temp, tempW, px, py, pz, pw)
        temp.x *= 2
        temp.y *= 2
        temp.z *= 2
        tempW *= 2
        amplitude *= 0.5
    return value

def perlin4D_List(VirtualVector3DList vectors,
                  VirtualDoubleList w,
                  Py_ssize_t amount,
                  float amplitude,
                  float frequency,
                  int octaves):

    cdef Py_ssize_t i
    cdef FloatList output = FloatList(length = amount)
    for i in range(amount):
        output.data[i] = perlin4D_Single(vectors.get(i), w.get(i), amplitude, frequency, octaves)
    return output

def periodicPerlin4D_List(VirtualVector3DList vectors,
                          VirtualDoubleList w,
                          Py_ssize_t amount,
                          float amplitude,
                          float frequency,
                          int octaves,
                          int pX,
                          int pY,
                          int pZ,
                          int pW):

    cdef Py_ssize_t i
    cdef FloatList output = FloatList(length = amount)

    pX = max(abs(pX), 1)
    pY = max(abs(pY), 1)
    pZ = max(abs(pZ), 1)
    pW = max(abs(pW), 1)

    for i in range(amount):
        output.data[i] = periodicPerlin4D_Single(vectors.get(i), w.get(i), pX, pY, pZ, pW, amplitude, frequency, octaves)
    return output

####################################### Voronoi 4D Noise #######################################

cdef float distanceV4(Vector4 a, Vector4 b, float exp, str method):
    cdef:
        float diff1 = (a.x - b.x)
        float diff2 = (a.y - b.y)
        float diff3 = (a.z - b.z)
        float diff4 = (a.w - b.w)

    if method == 'EUCLIDEAN':
        return sqrt(diff1*diff1 + diff2*diff2 + diff3*diff3 + diff4*diff4)
    elif method == 'MANHATTAN':
        return fabs(diff1) + fabs(diff2) + fabs(diff3) + fabs(diff4)
    elif method == 'CHEBYCHEV':
        return max(fabs(diff1), max(fabs(diff2), max(fabs(diff3), fabs(diff4))))
    elif method == 'MINKOWSKI':
        if exp == 0: return 0
        return (fabs(diff1)**exp + fabs(diff2)**exp + fabs(diff3)**exp + fabs(diff4)**exp) ** (1/exp)
    else:
        return 0

cdef float voronoi4D_F1(Vector4 coord, float randomness, float exponent, str method):
    cdef:
        Vector4 cellPosition = floorV4(coord)
        Vector4 localPosition = subV4(coord, cellPosition)

    cdef:
        Py_ssize_t u, k, j, i
        Vector4 cellOffset, pointPosition
        float distanceToPoint
        float minDistance = 8

    for u in range(-1, 2):
        for k in range(-1, 2):
            for j in range(-1, 2):
                for i in range(-1, 2):
                    cellOffset = Vector4(i, j, k, u)
                    pointPosition = addV4(cellOffset, mulV4_single(hash44(addV4(cellPosition, cellOffset)), randomness))
                    distanceToPoint = distanceV4(pointPosition, localPosition, exponent, method)
                    if distanceToPoint < minDistance:
                        minDistance = distanceToPoint
    return minDistance

cdef float voronoi4D_Single(Vector3* vector,
                            float w,
                            float amplitude,
                            float frequency,
                            float randomness,
                            float exponent,
                            str distanceMethod):

    cdef Vector4 point
    point.x = vector.x * frequency
    point.y = vector.y * frequency
    point.z = vector.z * frequency
    point.w = w * frequency
    return voronoi4D_F1(point, randomness, exponent, distanceMethod) * amplitude


def voronoi4D_List(VirtualVector3DList vectors,
                   VirtualDoubleList w,
                   Py_ssize_t amount,
                   float amplitude,
                   float frequency,
                   float randomness,
                   float exponent,
                   str distanceMethod):

    cdef Py_ssize_t i
    cdef FloatList output = FloatList(length = amount)
    for i in range(amount):
        output.data[i] = voronoi4D_Single(vectors.get(i), w.get(i), amplitude, frequency, randomness, exponent, distanceMethod)
    return output
