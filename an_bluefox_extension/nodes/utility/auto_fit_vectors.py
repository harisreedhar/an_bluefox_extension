import bpy
import numpy as np
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures import Vector3DList

class BF_AutoFitVectorsNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_AutoFitVectorsNode"
    bl_label = "Auto Fit Vectors"

    def create(self):
        self.newInput("Vector List", "vectors", "vectors", dataIsModified = True)
        self.newInput("Float", "Scale", "scale", value = 1)
        self.newInput("Boolean", "Align Center", "alignCenter", value = True)
        self.newOutput("Vector List", "Result", "result")

    def execute(self, vectors, scale, alignCenter):
        if len(vectors) == 0:
            return vectors
        array = vectors.asNumpyArray().reshape(-1,3)
        mins = np.min(array, axis=0)
        maxs = np.max(array, axis=0)
        diff = maxs - mins
        nume = array - mins
        array = np.divide(nume, diff, out=np.zeros_like(nume), where=diff!=0)
        if alignCenter:
            array -= 0.5
        array *= scale
        return Vector3DList.fromNumpyArray(array.ravel().astype('f'))
