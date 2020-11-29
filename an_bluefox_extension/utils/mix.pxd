from animation_nodes . math cimport Vector3, Euler3, Quaternion, Matrix4

cdef quaternionToMatrix4(Matrix4 *m, Quaternion *q)
cdef eulerToQuaternion(Quaternion *q, Euler3 *e)
cdef vectorLerpInPlace(Vector3 *target, Vector3 *a, Vector3 *b, float factor)
cdef quaternionToEulerInPlace(Euler3 *e, Quaternion *q)
cdef quaternionNlerpInPlace(Quaternion *target, Quaternion *a, Quaternion *b, float factor)
