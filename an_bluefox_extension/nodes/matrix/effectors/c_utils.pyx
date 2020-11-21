from libc.math cimport sqrt, ceil, floor, abs as absNumber

from animation_nodes . nodes . matrix . c_utils import*

from .... utils.mix import (
    quaternionsToEulers, quaternionListLerp,
    quaternionListNlerp, vectorListLerp,
    matrixListLerp
)

from animation_nodes . data_structures cimport (
    Vector3DList, DoubleList, FloatList, EulerList, Matrix4x4List,
    QuaternionList, VirtualQuaternionList,
    VirtualVector3DList, VirtualEulerList, VirtualMatrix4x4List,
    VirtualDoubleList, VirtualFloatList
)

################################################### Inheritance effector code ###################################################

def inheritPointsOverSpline(Vector3DList vA, Vector3DList vB, Vector3DList splinePoints, FloatList influences):

    cdef Py_ssize_t i, j, bIndex, aIndex, count, splinePointCount, innerLength
    cdef float f, influence, oneMinusinfluence

    count = vA.length
    splinePointCount = splinePoints.length
    innerLength = splinePointCount + 2

    cdef Vector3DList outVectorList = Vector3DList(length = count)
    cdef Vector3DList innerVectorList = Vector3DList(length = innerLength)

    for i in range(count):
        innerVectorList.data[0] = vA.data[i]

        for j in range(splinePointCount):
            innerVectorList.data[j+1].x = splinePoints.data[j].x
            innerVectorList.data[j+1].y = splinePoints.data[j].y
            innerVectorList.data[j+1].z = splinePoints.data[j].z

        innerVectorList.data[innerLength - 1] = vB.data[i]
        f = influences.data[i] * (innerLength - 1)
        influence = f % 1
        bIndex = int(max(min(floor(f), innerLength - 1), 0))
        aIndex = int(max(min(ceil(f), innerLength - 1), 0))
        oneMinusinfluence = 1-influence

        outVectorList.data[i].x = (innerVectorList.data[bIndex].x * oneMinusinfluence
                                  + innerVectorList.data[aIndex].x * influence)
        outVectorList.data[i].y = (innerVectorList.data[bIndex].y * oneMinusinfluence
                                  + innerVectorList.data[aIndex].y * influence)
        outVectorList.data[i].z = (innerVectorList.data[bIndex].z * oneMinusinfluence
                                  + innerVectorList.data[aIndex].z * influence)

    return outVectorList

def alignOnSpline(QuaternionList qA, QuaternionList qB,
                  QuaternionList splineRotations, FloatList influences):

    cdef Py_ssize_t i, j, bIndex, aIndex, count, splineEulerCount, innerLength

    count = qA.getLength()
    splineEulerCount = splineRotations.getLength()
    innerLength = splineEulerCount + 2

    cdef float f, influence, t1, w, x, y, z, ls, invNorm
    cdef QuaternionList outEulerlist = QuaternionList(length = count)
    cdef QuaternionList inList = QuaternionList(length = innerLength)

    for i in range(count):
        inList.data[0] = qA.data[i]

        for j in range(splineEulerCount):
            inList.data[j+1].w = splineRotations.data[j].w
            inList.data[j+1].x = splineRotations.data[j].x
            inList.data[j+1].y = splineRotations.data[j].y
            inList.data[j+1].z = splineRotations.data[j].z

        inList.data[innerLength - 1] = qB.data[i]
        f = influences.data[i] * (innerLength - 1)
        influence = f % 1
        bIndex = int(max(min(floor(f), innerLength - 1), 0))
        aIndex = int(max(min(ceil(f), innerLength - 1), 0))
        t1 = 1 - influence
        dot = (inList.data[bIndex].x * inList.data[aIndex].x
             + inList.data[bIndex].y * inList.data[aIndex].y
             + inList.data[bIndex].z * inList.data[aIndex].z
             + inList.data[bIndex].w * inList.data[aIndex].w)

        if dot >= 0:
            w = t1 * inList.data[bIndex].w + influence * inList.data[aIndex].w
            x = t1 * inList.data[bIndex].x + influence * inList.data[aIndex].x
            y = t1 * inList.data[bIndex].y + influence * inList.data[aIndex].y
            z = t1 * inList.data[bIndex].z + influence * inList.data[aIndex].z
        else:
            w = t1 * inList.data[bIndex].w - influence * inList.data[aIndex].w
            x = t1 * inList.data[bIndex].x - influence * inList.data[aIndex].x
            y = t1 * inList.data[bIndex].y - influence * inList.data[aIndex].y
            z = t1 * inList.data[bIndex].z - influence * inList.data[aIndex].z

        ls = w * w + x * x + y * y + z * z

        invNorm = 1/sqrt(ls)
        w *= invNorm
        x *= invNorm
        y *= invNorm
        z *= invNorm

        outEulerlist.data[i].w = w
        outEulerlist.data[i].x = x
        outEulerlist.data[i].y = y
        outEulerlist.data[i].z = z

    return quaternionsToEulers(outEulerlist)

def inheritMatrixOverSpline(Matrix4x4List mA,
                            Matrix4x4List mB,
                            Vector3DList splinePoints,
                            Matrix4x4List splineRotations, FloatList influences, bint align):

    cdef Vector3DList translation = inheritPointsOverSpline(extractMatrixTranslations(mA),
                                                extractMatrixTranslations(mB),
                                                splinePoints,
                                                influences)

    cdef EulerList rotation = quaternionsToEulers(quaternionListLerp(
                                            Matrix4x4List.toQuaternions(mA),
                                            Matrix4x4List.toQuaternions(mB),
                                            influences))
    if align:
        rotation = alignOnSpline(Matrix4x4List.toQuaternions(mA),
                                  Matrix4x4List.toQuaternions(mB),
                                  Matrix4x4List.toQuaternions(splineRotations),
                                  influences)

    cdef Vector3DList scale = vectorListLerp(extractMatrixScales(mA),
                                         extractMatrixScales(mB),
                                         influences)

    cdef VirtualVector3DList _translation = VirtualVector3DList.create(translation, (0, 0, 0))
    cdef VirtualEulerList _rotation = VirtualEulerList.create(rotation, (0, 0, 0))
    cdef VirtualVector3DList _scale = VirtualVector3DList.create(scale, (1, 1, 1))

    return composeMatrices(len(mA), _translation, _rotation, _scale)

def inhertMatrixLinear(Matrix4x4List mA, Matrix4x4List mB, FloatList influences):
    return matrixListLerp(mA, mB, influences)

################################################# Inheritance effector code end #################################################
