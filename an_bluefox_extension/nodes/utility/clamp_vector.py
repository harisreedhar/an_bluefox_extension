import bpy
from animation_nodes . data_structures import Vector3DList
from animation_nodes . base_types import AnimationNode, VectorizedSocket

class BF_ClampVectorNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_ClampVectorNode"
    bl_label = "Clamp Vector"

    useVectorList: VectorizedSocket.newProperty()

    def create(self):
        self.newInput(VectorizedSocket("Vector", "useVectorList",
            ("Vector", "vector"), ("Vectors", "vector")))
        self.newInput("Vector", "Min", "min")
        self.newInput("Vector", "Max", "max", value = (1,1,1))
        self.newOutput(VectorizedSocket("Vector", "useVectorList",
            ("Vector", "vector"), ("Vectors", "vector")))

    def execute(self, vector, minimum, maximum):
        vector = vector if self.useVectorList else Vector3DList.fromValue(vector)
        array = vector.asNumpyArray().reshape(-1,3)

        array[:,0][array[:,0] > maximum[0]] = maximum[0]
        array[:,0][array[:,0] < minimum[0]] = minimum[0]
        array[:,1][array[:,1] > maximum[1]] = maximum[1]
        array[:,1][array[:,1] < minimum[1]] = minimum[1]
        array[:,2][array[:,2] > maximum[2]] = maximum[2]
        array[:,2][array[:,2] < minimum[2]] = minimum[2]
        output = Vector3DList.fromNumpyArray(array.ravel().astype('f'))

        if not self.useVectorList: return output[0]
        return output
