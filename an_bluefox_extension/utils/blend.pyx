from libc . math cimport sqrt, floor, fabs

cdef float blendFloats(float a, float b, float factor):
    return a * (1-factor) + b * factor

cdef float add(float a, float b, float factor):
    return blendFloats(a, a + b, factor)

cdef float multiply(float a, float b, float factor):
    return blendFloats(a, a * b, factor)

cdef float screen(float a, float b, float factor):
    cdef float oneMinusFactor = 1 - factor
    return 1 - (oneMinusFactor + factor * (1 - b)) * (1 - a)

cdef float overlay(float a, float b, float factor):
    cdef float oneMinusFactor = 1 - factor
    cdef float output = a
    if output < 0.5:
        output *= oneMinusFactor + 2 * factor * b
    else:
        output = 1 - (oneMinusFactor + 2 * factor * (1 - b)) * (1 - output)
    return output

cdef float subtract(float a, float b, float factor):
    return blendFloats(a, a - b, factor)

cdef float divide(float a, float b, float factor):
    cdef float oneMinusFactor = 1 - factor
    cdef float output = a
    if b != 0:
        output = oneMinusFactor * output + factor * output / b
    return output

cdef float difference(float a, float b, float factor):
    return blendFloats(a, fabs(a - b), factor)

cdef float darken(float a, float b, float factor):
    return blendFloats(a, min(a, b), factor)

cdef float lighten(float a, float b, float factor):
    return blendFloats(a, max(a, b), factor)

cdef float softLight(float a, float b, float factor):
    cdef float oneMinusFactor = 1 - factor
    cdef float scr = 1 - (1 - b) * (1 - a)
    return oneMinusFactor * a + factor * ((1 - a) * b * a + a * scr)

cdef float hardMix(float a, float b, float factor):
    return blendFloats(a, floor(a + b), factor)
