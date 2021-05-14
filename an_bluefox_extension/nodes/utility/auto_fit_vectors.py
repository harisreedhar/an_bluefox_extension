import bpy
import numpy as np
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures import Vector3DList

class BF_AutoFitVectorsNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_AutoFitVectorsNode"
    bl_label = "Auto Fit Vectors"

    def create(self):
        self.newInput("Boolean", "Align Center", "alignCenter", value = True)
        self.newInput("Float", "Scale", "scale", value = 1)
        self.newInput("Vector List", "vectors", "vectors")
        self.newOutput("Vector List", "Result", "result")

    def execute(self, alignCenter, scale, vectors):
        if len(vectors) == 0:
            return vectors
        array = vectors.asNumpyArray()
        if alignCenter:
            _array = array.reshape(-1,3)
            _array -= np.mean(_array, axis = 0)
            array = _array.ravel()
        array /= np.max(np.abs(array))
        array *= scale
        return Vector3DList.fromNumpyArray(array.astype('f'))
