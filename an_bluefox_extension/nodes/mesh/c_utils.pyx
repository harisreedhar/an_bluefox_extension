from animation_nodes.data_structures cimport (
    PolygonIndicesList,
    UIntegerList
)

def polygonIndicesList_From_triArray(triArray):
    cdef int i
    cdef int triAmount = triArray.shape[0]
    cdef UIntegerList triIndices = UIntegerList.fromNumpyArray(triArray.ravel().astype('uint32'))
    cdef int indiceAmount = triIndices.length
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

        newIndices[index] = triIndices.data[index]
        newIndices[index+1] = triIndices.data[index+1]
        newIndices[index+2] = triIndices.data[index+2]

        index += 3
    return newPolygons
