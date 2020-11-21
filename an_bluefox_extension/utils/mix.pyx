from libc.math cimport sqrt, M_PI, copysign, asin, atan2, sin, cos, tan, ceil, floor, abs as absNumber

from animation_nodes . nodes . matrix . c_utils import*

from animation_nodes . math cimport (
     Quaternion, Euler3, Vector3, Matrix4,
     setTranslationRotationScaleMatrix, quaternionNormalize_InPlace
)

from animation_nodes . data_structures cimport (
    Vector3DList, DoubleList, FloatList, EulerList, Matrix4x4List,
    QuaternionList, VirtualQuaternionList,
    VirtualVector3DList, VirtualEulerList, VirtualMatrix4x4List,
    VirtualDoubleList, VirtualFloatList,
    Interpolation
)

def quaternionsToEulers(QuaternionList q):
    cdef Py_ssize_t i
    cdef Py_ssize_t amount = q.length
    cdef EulerList e = EulerList(length = amount)
    e.fill(0)

    for i in range(amount):
        quaternionToEulerInPlace(&e.data[i], &q.data[i])
    return e

cdef quaternionToEulerInPlace(Euler3 *e, Quaternion *q):
    #quaternionNormalize_InPlace(q)
    cdef float sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
    cdef float cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
    e.x = atan2(sinr_cosp, cosr_cosp)

    cdef float sinp = 2 * (q.w * q.y - q.z * q.x)
    if absNumber(sinp) >= 1.0:
        e.y = copysign(M_PI/2, sinp)
    else:
        e.y = asin(sinp)

    cdef float siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cdef float cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    e.z = atan2(siny_cosp, cosy_cosp)
    e.order = 0

def quaternionListLerp(QuaternionList qA, QuaternionList qB, FloatList influences):
    cdef Py_ssize_t count = len(qA)
    cdef QuaternionList out_Quat = QuaternionList(length = count)
    cdef double t, t1, dot, w1, w2, x1, x2, y1, y2, z1, z2, ls, invNorm

    for i in range(count):
        t = influences.data[i]
        t1 = 1 - t
        w1, w2 = qA.data[i].w, qB.data[i].w
        x1, x2 = qA.data[i].x, qB.data[i].x
        y1, y2 = qA.data[i].y, qB.data[i].y
        z1, z2 = qA.data[i].z, qB.data[i].z

        dot = x1 * x2 + y1 * y2 + z1 * z2 + w1 * w2

        if dot >= 0:
            out_Quat.data[i].w = t1 * w1 + t * w2
            out_Quat.data[i].x = t1 * x1 + t * x2
            out_Quat.data[i].y = t1 * y1 + t * y2
            out_Quat.data[i].z = t1 * z1 + t * z2
        else:
            out_Quat.data[i].w = t1 * w1 - t * w2
            out_Quat.data[i].x = t1 * x1 - t * x2
            out_Quat.data[i].y = t1 * y1 - t * y2
            out_Quat.data[i].z = t1 * z1 - t * z2

        ls = out_Quat.data[i].w * out_Quat.data[i].w
        ls += out_Quat.data[i].x * out_Quat.data[i].x
        ls += out_Quat.data[i].y * out_Quat.data[i].y
        ls += out_Quat.data[i].z * out_Quat.data[i].z
        invNorm = 1/sqrt(ls)
        out_Quat.data[i].w *= invNorm
        out_Quat.data[i].x *= invNorm
        out_Quat.data[i].y *= invNorm
        out_Quat.data[i].z *= invNorm

    return out_Quat

cdef quaternionNlerpInPlace(Quaternion *target, Quaternion *a, Quaternion *b, float factor):
    cdef float dot = a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w
    cdef float oneMinusFactor = 1.0 - factor
    if dot < 0:
        target.w = oneMinusFactor * a.w + factor * -b.w
        target.x = oneMinusFactor * a.x + factor * -b.x
        target.y = oneMinusFactor * a.y + factor * -b.y
        target.z = oneMinusFactor * a.z + factor * -b.z
    else:
        target.w = oneMinusFactor * a.w + factor * b.w
        target.x = oneMinusFactor * a.x + factor * b.x
        target.y = oneMinusFactor * a.y + factor * b.y
        target.z = oneMinusFactor * a.z + factor * b.z

    quaternionNormalize_InPlace(target)

def quaternionListNlerp(QuaternionList q1, QuaternionList q2, FloatList factors):
    cdef Py_ssize_t i
    cdef Py_ssize_t amount = max(max(q1.length, q2.length), factors.length)
    cdef QuaternionList result = QuaternionList(length = amount)
    cdef VirtualQuaternionList _q1 = VirtualQuaternionList.create(q1, (1,0,0,0))
    cdef VirtualQuaternionList _q2 = VirtualQuaternionList.create(q2, (1,0,0,0))
    cdef VirtualFloatList _factors = VirtualFloatList.create(factors, 0)

    for i in range(amount):
        quaternionNlerpInPlace(&result.data[i], _q1.get(i), _q2.get(i), _factors.get(i))

    return result

cdef vectorLerpInPlace(Vector3 *target, Vector3 *a, Vector3 *b, float factor):
    cdef double oneMinusFactor = 1 - factor

    target.x = oneMinusFactor * a.x + factor * b.x
    target.y = oneMinusFactor * a.y + factor * b.y
    target.z = oneMinusFactor * a.z + factor * b.z

def vectorListLerp(Vector3DList vA, Vector3DList vB, FloatList factors):
    cdef Py_ssize_t amount = max(max(vA.length, vB.length), factors.length)
    cdef Py_ssize_t i
    cdef VirtualFloatList _factors = VirtualFloatList.create(factors, 0)
    cdef VirtualVector3DList _vA = VirtualVector3DList.create(vA, (0,0,0))
    cdef VirtualVector3DList _vB = VirtualVector3DList.create(vB, (0,0,0))
    cdef Vector3DList result = Vector3DList(length = amount)

    for i in range(amount):
        vectorLerpInPlace(result.data + i, _vA.get(i), _vB.get(i), _factors.get(i))

    return result

def matrixListLerp(Matrix4x4List mA, Matrix4x4List mB, FloatList factors):
    cdef Py_ssize_t i
    cdef Py_ssize_t amount = max(max(mA.length, mB.length), factors.length)

    cdef Matrix4x4List result = Matrix4x4List(length = amount)
    cdef VirtualFloatList _factors = VirtualFloatList.create(factors, 0)

    cdef VirtualQuaternionList qA = VirtualQuaternionList.create(mA.toQuaternions(), (1,0,0,0))
    cdef VirtualQuaternionList qB = VirtualQuaternionList.create(mB.toQuaternions(), (1,0,0,0))

    cdef VirtualVector3DList tA = VirtualVector3DList.create(extractMatrixTranslations(mA), (0,0,0))
    cdef VirtualVector3DList tB = VirtualVector3DList.create(extractMatrixTranslations(mB), (0,0,0))

    cdef VirtualVector3DList sA = VirtualVector3DList.create(extractMatrixScales(mA), (0,0,0))
    cdef VirtualVector3DList sB = VirtualVector3DList.create(extractMatrixScales(mB), (0,0,0))

    cdef Vector3 t
    cdef Vector3 s
    cdef Quaternion q
    cdef Euler3 r

    for i in range(amount):
        vectorLerpInPlace(&t, tA.get(i), tB.get(i), _factors.get(i))
        vectorLerpInPlace(&s, sA.get(i), sB.get(i), _factors.get(i))
        quaternionNlerpInPlace(&q, qA.get(i), qB.get(i), _factors.get(i))
        quaternionToEulerInPlace(&r, &q)
        setTranslationRotationScaleMatrix(&result.data[i], &t, &r, &s)

    return result
