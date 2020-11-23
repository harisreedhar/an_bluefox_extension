import cython
from libc.math cimport sqrt, floor, fabs
from animation_nodes . data_structures cimport (
    Color, ColorList,
    FloatList, VirtualColorList,
    VirtualDoubleList
)

@cython.cdivision(True)
cdef c_colorMix(Color *result, Color *a, Color *b, float f, str mode, bint clamp):
    cdef float temp
    cdef double h1, h2, s1, s2, v1, v2, a1, a2
    if clamp:
        f = min(max(f, 0), 1)

    result.a = 1
    if mode == 'MULTIPLY':
        result.r = a.r * b.r
        result.g = a.g * b.g
        result.b = a.b * b.b

    elif mode == 'COLORBURN':
        result.r = 1 - (1 - b.r) / a.r
        result.g = 1 - (1 - b.g) / a.g
        result.b = 1 - (1 - b.b) / a.b

    elif mode == 'LINEARBURN':
        result.r = a.r + b.r - 1
        result.g = a.g + b.g - 1
        result.b = a.b + b.b - 1

    elif mode == 'SCREEN':
        result.r = a.r + b.r - a.r * b.r
        result.g = a.g + b.g - a.g * b.g
        result.b = a.b + b.b - a.b * b.b

    elif mode == 'COLORDODGE':
        result.r = a.r / (1 - b.r)
        result.g = a.g / (1 - b.g)
        result.b = a.b / (1 - b.b)

    elif mode == 'ADD':
        result.r = a.r + b.r
        result.g = a.g + b.g
        result.b = a.b + b.b

    elif mode == 'SUBTRACT':
        result.r = a.r - b.r
        result.g = a.g - b.g
        result.b = a.b - b.b

    elif mode == 'DIVIDE':
        temp = 1 - f
        result.r = temp * a.r + f * a.r / b.r
        result.g = temp * a.g + f * a.g / b.g
        result.b = temp * a.b + f * a.b / b.b

    elif mode == 'OVERLAY':
        if a.r < 0.5:
            result.r = 2 * a.r * b.r
        else:
            result.r = 1 - 2 * (1 - a.r) * (1 - b.r)
        if a.g < 0.5:
            result.g = 2 * a.g * b.g
        else:
            result.r = 1 - 2 * (1 - a.g) * (1 - b.g)
        if a.b < 0.5:
            result.b = 2 * a.b * b.b
        else:
            result.b = 1 - 2 * (1 - a.b) * (1 - b.b)

    elif mode == 'SOFTLIGHT':
        if b.r <= 0.5:
            result.r = a.r - (1 - 2 * a.r) * a.r * (1 - a.r)
        else:
            if a.r <= 0.25:
                temp = ((16 * a.r - 12) * a.r + 4) * a.r
            else:
                temp = sqrt(a.r)
            result.r = a.r + (2 * b.r - 1) * (temp - a.r)

        if b.g <= 0.5:
            result.g = a.g - (1 - 2 * a.g) * a.g * (1 - a.g)
        else:
            if a.g <= 0.25:
                temp = ((16 * a.g - 12) * a.g + 4) * a.g
            else:
                temp = sqrt(a.g)
            result.g = a.g + (2 * b.g - 1) * (temp - a.g)

        if b.b <= 0.5:
            result.b = a.b - (1 - 2 * a.b) * a.b * (1 - a.b)
        else:
            if a.b <= 0.25:
                temp = ((16 * a.b - 12) * a.b + 4) * a.b
            else:
                temp = sqrt(a.b)
            result.b = a.b + (2 * b.b - 1) * (temp - a.b)

    elif mode == 'DARKEN':
        result.r = min(a.r, b.r)
        result.g = min(a.g, b.g)
        result.b = min(a.b, b.b)

    elif mode == 'LIGHTEN':
        result.r = max(a.r, b.r)
        result.g = max(a.g, b.g)
        result.b = max(a.b, b.b)

    elif mode == 'HARDLIGHT':
        if a.r < 0.5:
            result.r = 2 * a.r * b.r
        else:
            result.r = 1.0 - 2.0 * (1.0 - a.r) * (1.0 - b.r)
        if a.g < 0.5:
            result.g = 2 * a.g * b.g
        else:
            result.g = 1.0 - 2.0 * (1.0 - a.g) * (1.0 - b.g)
        if a.b < 0.5:
            result.b = 2 * a.b * b.b
        else:
            result.b = 1.0 - 2.0 * (1.0 - a.b) * (1.0 - b.b)

    elif mode == 'LINEARLIGHT':
        result.r = 2 * a.r + b.r - 1
        result.g = 2 * a.g + b.g - 1
        result.b = 2 * a.b + b.b - 1

    elif mode == 'HARDMIX':
        result.r = floor(a.r + b.r)
        result.g = floor(a.g + b.g)
        result.b = floor(a.b + b.b)

    elif mode == 'DIFFERENCE':
        result.r = fabs(b.r - a.r)
        result.g = fabs(b.g - a.g)
        result.b = fabs(b.b - a.b)

    else:
        result.r = b.r
        result.g = b.g
        result.b = b.b

    result.r = ((1 - f) * a.r + f * result.r)
    result.g = ((1 - f) * a.g + f * result.g)
    result.b = ((1 - f) * a.b + f * result.b)

    if clamp:
        result.r = min(max(result.r, 0), 1)
        result.g = min(max(result.g, 0), 1)
        result.b = min(max(result.b, 0), 1)

def colorMixList(VirtualColorList a, VirtualColorList b, VirtualDoubleList f, str mode, bint clamp = False):
    cdef colorsLength = VirtualColorList.getMaxRealLength(a, b)
    cdef factorLength = VirtualDoubleList.getMaxRealLength(f)
    cdef int amount = max(colorsLength, factorLength)
    cdef Py_ssize_t i
    cdef ColorList result = ColorList(length = amount)
    result.fill(0)

    for i in range(amount):
        c_colorMix(result.data + i, a.get(i), b.get(i), <float>f.get(i), mode, clamp)

    return result
