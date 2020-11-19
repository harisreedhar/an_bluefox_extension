from animation_nodes.data_structures cimport PolygonIndicesList

cdef c_polygonIndices_From_triArray(unsigned int [:, :] triArray):
    cdef int i
    cdef int triAmount = triArray.shape[0]
    cdef int indiceAmount = triArray.size
    cdef PolygonIndicesList newPolygons = PolygonIndicesList(
                                          indicesAmount = indiceAmount,
                                          polygonAmount = triAmount)
    cdef unsigned int *newIndices = newPolygons.indices.data
    cdef unsigned int *newPolyStarts = newPolygons.polyStarts.data
    cdef unsigned int *newPolyLengths = newPolygons.polyLengths.data

    cdef unsigned int index = 0
    for i in range(triAmount):
        newPolyStarts[i] = index
        newPolyLengths[i] = 3

        newIndices[index] = triArray[i, 0]
        newIndices[index+1] = triArray[i, 1]
        newIndices[index+2] = triArray[i, 2]

        index += 3
    return newPolygons

def polygonIndices_From_triArray(triArray):
    return c_polygonIndices_From_triArray(triArray.astype('uint32'))
