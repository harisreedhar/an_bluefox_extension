from animation_nodes . math cimport Vector3, Vector4

cdef float noise4(Vector3* vec, float w)
cdef float pnoise4(Vector3* vec, float w, int px, int py, int pz, int pw)
cdef float perlin4D_Single(Vector3* v, float w, float amplitude, float frequency, Vector3 offset, int octaves)
cdef float periodicPerlin4D_Single(Vector3* v,
                                   float w,
                                   int px,
                                   int py,
                                   int pz,
                                   int pw,
                                   float amplitude,
                                   float frequency,
                                   Vector3 offset,
                                   int octaves)

cdef float distanceV4(Vector4 a, Vector4 b, float exp, str method)
cdef float voronoi4D_F1(Vector4 coord, float randomness, float exponent, str method)
cdef float voronoi4D_Single(Vector3* vector,
                            float w,
                            float amplitude,
                            float frequency,
                            Vector3 offset,
                            float randomness,
                            float exponent,
                            str distanceMethod)
