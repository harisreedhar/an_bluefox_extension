from animation_nodes . math cimport Vector4, Vector3
from libc . math cimport fabs, floor, sqrt

cdef inline int fastFloor(float x):
    return <int>x if <int>x < x else <int>x-1

cdef inline float lerp(float t, float a, float b):
    return (a) + (t) * (b-a)

cdef inline float fract(float value):
    return value - fastFloor(value)

cdef inline float dotV4(Vector4 a, Vector4 b):
    return a.x*b.x + a.y*b.y + a.z*b.z + a.w*b.w

cdef inline Vector4 addV4(Vector4 a, Vector4 b):
    a.x += b.x
    a.y += b.y
    a.z += b.z
    a.w += b.w
    return a

cdef inline Vector4 mulV4_single(Vector4 a, float b):
    a.x *= b
    a.y *= b
    a.z *= b
    a.w *= b
    return a

cdef inline Vector4 subV4(Vector4 a, Vector4 b):
    a.x -= b.x
    a.y -= b.y
    a.z -= b.z
    a.w -= b.w
    return a

cdef inline Vector4 floorV4(Vector4 a):
    a.x = fastFloor(a.x)
    a.y = fastFloor(a.y)
    a.z = fastFloor(a.z)
    a.w = fastFloor(a.w)
    return a

cdef inline Vector4 fractV4(Vector4 a):
    a.x = fract(a.x)
    a.y = fract(a.y)
    a.z = fract(a.z)
    a.w = fract(a.w)
    return a

# https://www.shadertoy.com/view/4djSRW
cdef inline Vector4 hash44(Vector4 p4):
    p4 = Vector4(fract(p4.x * 0.1031),
                 fract(p4.y * 0.1030),
                 fract(p4.z * 0.0973),
                 fract(p4.w * 0.1099))

    cdef float dot = p4.x*p4.w + p4.y*p4.z + p4.z*p4.x + p4.w*p4.y + 133.32
    p4.x += dot
    p4.y += dot
    p4.z += dot
    p4.w += dot

    return Vector4(fract((p4.x + p4.y) * p4.z),
                   fract((p4.x + p4.z) * p4.y),
                   fract((p4.y + p4.z) * p4.w),
                   fract((p4.z + p4.w) * p4.x))

cdef inline void applyFrequencyOffset(Vector4* output, Vector3* point, float frequency, Vector4 offset):
    output.x = (point.x * frequency) + offset.x
    output.y = (point.y * frequency) + offset.y
    output.z = (point.z * frequency) + offset.z
    output.w = frequency + offset.w
