from libc.math cimport sqrt, ceil, floor, abs as absNumber

from animation_nodes . nodes . falloff . point_distance_falloff import PointDistanceFalloff

from animation_nodes . math cimport Vector3, setMatrixTranslation, setScaleMatrix, mixVec3, mixQuat, Matrix4, Quaternion

from animation_nodes . nodes . matrix . c_utils import*

from .... utils.mix cimport (
    vectorLerpInPlace,
    eulerToQuaternion,
    quaternionToMatrix4,
    quaternionNlerpInPlace
)

from .... utils.mix import (
    quaternionsToEulers, quaternionListLerp,
    quaternionListNlerp, vectorListLerp,
    matrixListLerp, quaternionsToMatrices
)

from animation_nodes . data_structures cimport (
    Vector3DList, DoubleList, FloatList, EulerList, Matrix4x4List,
    QuaternionList, VirtualQuaternionList,
    VirtualVector3DList, VirtualEulerList, VirtualMatrix4x4List,
    VirtualDoubleList, VirtualFloatList, Falloff, FalloffEvaluator
)

################################################### Inheritance effex code ###################################################

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

def matrixTranslationLerp(Matrix4x4List matrices, VirtualVector3DList translations, FloatList influences):
    cdef Vector3 target
    cdef Py_ssize_t i
    cdef Py_ssize_t amount = matrices.length
    cdef Vector3DList fromLocation = extractMatrixTranslations(matrices)
    for i in range(amount):
        vectorLerpInPlace(&target, fromLocation.data + i, translations.get(i), influences.data[i])
        setMatrixTranslation(matrices.data + i, &target)
    return matrices

def matrixRotationLerp(Matrix4x4List matrices, VirtualEulerList rotations, FloatList influences):
    cdef QuaternionList fromQuaternions = Matrix4x4List.toQuaternions(matrices)
    cdef Quaternion q, temp
    cdef Py_ssize_t i
    cdef Py_ssize_t amount = matrices.length
    cdef Matrix4x4List result = Matrix4x4List(length = amount)
    for i in range(amount):
        eulerToQuaternion(&q, rotations.get(i))
        quaternionNlerpInPlace(&temp, fromQuaternions.data + i, &q, influences.data[i])
        quaternionToMatrix4(result.data + i, &temp)
    return result

def matrixScaleLerp(Matrix4x4List matrices, VirtualVector3DList scales, FloatList influences):
    cdef Vector3 target
    cdef Py_ssize_t i
    cdef Py_ssize_t amount = matrices.length
    cdef Vector3DList fromScale = extractMatrixScales(matrices)
    cdef Matrix4x4List result = Matrix4x4List(length = amount)
    for i in range(amount):
        vectorLerpInPlace(&target, fromScale.data + i, scales.get(i), influences.data[i])
        setScaleMatrix(result.data + i, &target)
    return result

################################################# Inheritance effex code end #################################################

cdef getDirection(Vector3DList vectors, Vector3 *target, Py_ssize_t negFlag = 1):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = vectors.length
    cdef float vectorLength, x, y, z
    cdef Vector3DList outVectors = Vector3DList(length = count)

    for i in range(count):
        x = vectors.data[i].x - target.x
        y = vectors.data[i].y - target.y
        z = vectors.data[i].z - target.z

        vectorLength = sqrt(x*x + y*y + z*z)
        if vectorLength == 0:
            vectorLength = 0.00001

        outVectors.data[i].x = x / (vectorLength * vectorLength) * negFlag
        outVectors.data[i].y = y / (vectorLength * vectorLength) * negFlag
        outVectors.data[i].z = z / (vectorLength * vectorLength) * negFlag

    return outVectors

def getDirections(Vector3DList points, Vector3DList targets):
    cdef Py_ssize_t i, j
    cdef Py_ssize_t count = points.length
    cdef Py_ssize_t targetCount = targets.length
    cdef Vector3DList directions = Vector3DList(length = count)
    cdef Vector3DList temp = Vector3DList()

    for i in range(targetCount):
        temp = getDirection(points, targets.data + i)
        for j in range(count):
            directions.data[j].x += temp.data[j].x
            directions.data[j].y += temp.data[j].y
            directions.data[j].z += temp.data[j].z

    return directions

####################################    Target Effector Functions start   ##############################################
# code is shit, need complete rewrite

cdef Vector3DList findTargetDirection(Vector3DList vectors, Vector3 target, Py_ssize_t negFlag):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(vectors)
    cdef float x, y, z, divisor, vectorLength
    cdef Vector3DList outVectors = Vector3DList(length = count)

    for i in range(count):
        x = vectors.data[i].x - target.x
        y = vectors.data[i].y - target.y
        z = vectors.data[i].z - target.z

        outVectors.data[i].x = x
        outVectors.data[i].y = y
        outVectors.data[i].z = z

        vectorLength = sqrt(x * x + y * y + z * z)

        if vectorLength != 0:
            divisor = 1 / (vectorLength * vectorLength) * negFlag
            outVectors.data[i].x *= divisor
            outVectors.data[i].y *= divisor
            outVectors.data[i].z *= divisor

    return outVectors

def findSphericalDistance(Vector3DList vectors,
                          Vector3 target,
                          float size,
                          float width,
                          Py_ssize_t negFlag,
                          float offsetStrength,
                          FloatList influences,
                          useOffset):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = vectors.length
    cdef Vector3DList outVectors = Vector3DList(length = count)
    cdef Falloff pointfalloff = PointDistanceFalloff((target.x, target.y, target.z), size-1, width)

    cdef FalloffEvaluator falloffEvaluator = pointfalloff.getEvaluator("LOCATION")
    cdef FloatList distances = falloffEvaluator.evaluateList(vectors)
    distances.clamp(0,1)

    for i in range(count):
        outVectors.data[i].x = (vectors.data[i].x - target.x) * negFlag
        outVectors.data[i].y = (vectors.data[i].y - target.y) * negFlag
        outVectors.data[i].z = (vectors.data[i].z - target.z) * negFlag

        if useOffset:
            outVectors.data[i].x *= distances.data[i] * influences.data[i] * offsetStrength
            outVectors.data[i].y *= distances.data[i] * influences.data[i] * offsetStrength
            outVectors.data[i].z *= distances.data[i] * influences.data[i] * offsetStrength

    return outVectors, distances

def targetEffexFunction(Matrix4x4List targets,
                        Vector3DList targetOffsets,
                        float distanceIn,
                        float width,
                        float offsetStrength,
                        FloatList influences,
                        bint useOffset,
                        bint useDirection):

    cdef Py_ssize_t i, j, negFlag
    cdef Py_ssize_t count = targetOffsets.length
    cdef Py_ssize_t targetsCount = targets.length
    cdef float size, scale
    cdef Vector3DList newPositions, newDiretions
    cdef Vector3DList targetDirections = Vector3DList(length = count)
    targetDirections.fill(0)
    cdef Vector3DList centers = extractMatrixTranslations(targets)
    cdef FloatList distances = FloatList(length = count)
    distances.fill(0)
    cdef FloatList strengths = FloatList(length = count)
    strengths.fill(0)

    for i in range(targetsCount):
        negFlag = 1
        scale = targets.data[i].a11
        if scale < 0:
            negFlag = -1
        size = absNumber(scale) + distanceIn
        if useOffset:
            newPositions, distances = findSphericalDistance(targetOffsets,
                                                            centers.data[i],
                                                            size,
                                                            width,
                                                            negFlag,
                                                            offsetStrength,
                                                            influences,
                                                            useOffset)

            for j in range(count):
                targetOffsets.data[j].x += newPositions.data[j].x
                targetOffsets.data[j].y += newPositions.data[j].y
                targetOffsets.data[j].z += newPositions.data[j].z
                strengths.data[j] = max(strengths.data[j], distances.data[j]) * influences.data[j]

        if useDirection:
            newDiretions = findTargetDirection(targetOffsets, centers.data[i], negFlag)
            for j in range(targetDirections.length):
                targetDirections.data[j].x += newDiretions.data[j].x
                targetDirections.data[j].y += newDiretions.data[j].y
                targetDirections.data[j].z += newDiretions.data[j].z

    if useDirection:
        targetDirections.normalize()

    return targetOffsets, targetDirections, strengths

####################################    Target Effector Functions end   ##############################################
