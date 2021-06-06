from animation_nodes . math cimport Vector3

cdef float noise4(Vector3* vec, float w)
cdef float pnoise4(Vector3* vec, float w, int px, int py, int pz, int pw)
cdef float fractalNoise(Vector3* v, float w, float amplitude, float frequency, int octaves)
cdef float fractalPNoise(Vector3* v, float w, int px, int py, int pz, int pw, float amplitude, float frequency, int octaves)
