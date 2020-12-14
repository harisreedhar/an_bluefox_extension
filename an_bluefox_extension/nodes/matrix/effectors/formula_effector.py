import bpy
import numpy as np
from bpy.props import *
from . effector_base import EffectorBase
from .... utils . formula import evaluateFormula
from animation_nodes . base_types import AnimationNode
from animation_nodes . nodes.rotation.c_utils import eulersToVectors
from animation_nodes . data_structures import Matrix4x4List, Vector3DList, FloatList

class BF_FormulaEffectorNode(bpy.types.Node, AnimationNode, EffectorBase):
    bl_idname = "an_bf_FormulaEffector"
    bl_label = "Formula Effector"
    bl_width_default = 200
    errorHandlingType = "EXCEPTION"

    formula: StringProperty(name = "Formula", default = "sin(id/count*2*pi + frame/10)",
                        update = AnimationNode.refresh)
    incPosAttr: BoolProperty(name = "Include position variables", default = True,
                        update = AnimationNode.refresh)
    incRotAttr: BoolProperty(name = "Include rotation variables", default = False,
                        update = AnimationNode.refresh)
    incScaleAttr: BoolProperty(name = "Include scale variables", default = False,
                        update = AnimationNode.refresh)
    incFalloffAttr: BoolProperty(name = "Include falloff variable", default = False,
                        update = AnimationNode.refresh)

    def create(self):
        self.newInput("Matrix List", "Matrices", "matrices", dataIsModified = True)
        self.createBasicInputs()
        self.newOutput("Matrix List", "Matrices", "matrices")
        self.newOutput("Float List", "Values", "effectorValues", hide = True)
        self.updateSocketVisibility()

    def draw(self, layout):
        layout.prop(self, "formula", text = "")
        self.draw_MatrixTransformationProperties(layout)

    def drawAdvanced(self, layout):
        self.drawFalloffMixType(layout)
        layout.prop(self, "incPosAttr")
        layout.label(text = "px,py,pz")
        layout.prop(self, "incRotAttr")
        layout.label(text = "rx,ry,rz")
        layout.prop(self, "incScaleAttr")
        layout.label(text = "sx,sy,sz")
        layout.prop(self, "incFalloffAttr")
        layout.label(text = "falloff")

    def getExecutionCode(self, required):
        if "matrices" in required or "effectorValues" in required:
            yield "effectorValues = AN.data_structures.DoubleList()"
            if any([self.useTranslation, self.useRotation, self.useScale]):
                yield "efStrengths = AN.data_structures.FloatList()"
                yield "try:"
                yield "    efStrengths = self.getFormulaStrengths(self.formula, matrices, falloff)"
                yield "    mixedFalloff = self.mixEffectorAndFalloff(efStrengths, falloff, interpolation, outMin=minValue, outMax=maxValue)"
                yield "    influences = self.getInfluences(mixedFalloff, matrices)"
                yield "    matrices = self.offsetMatrixList(matrices, influences, translation, rotation, scale)"
                if "effectorValues" in required:
                    yield "    effectorValues = AN.data_structures.DoubleList.fromValues(influences)"
                yield "except Exception as e:"
                yield "    print('Formula Effector Error:', str(e))"
                yield "    self.setErrorMessage('Formula error!')"

    def getFormulaStrengths(self, formula, matrices, falloff):
        formula = self.formula
        pX = pY = pZ = rX = rY = rZ = arrF = 0
        sX = sY = sZ = 1
        if formula != "":
            t,r,s = self.getMatriceComponents(matrices)
            if self.incPosAttr:
                arrT = t.asNumpyArray().reshape(-1,3)
                pX,pY,pZ = arrT[:,0], arrT[:,1], arrT[:,2]
            if self.incRotAttr:
                r = eulersToVectors(r, False)
                arrR = r.asNumpyArray().reshape(-1,3)
                rX,rY,rZ = arrR[:,0], arrR[:,1], arrR[:,2]
            if self.incScaleAttr:
                arrS = s.asNumpyArray().reshape(-1,3)
                sX,sY,sZ = arrS[:,0], arrS[:,1], arrS[:,2]
            if self.incFalloffAttr:
                influences = self.getInfluences(falloff, matrices).copy()
                arrF = influences.asNumpyArray()

            array = evaluateFormula(formula, count = len(matrices), falloff = arrF,
                    px = pX, py = pY, pz = pZ,
                        rx = rX, ry = rY, rz = rZ,
                            sx = sX, sy = sY, sz = sZ)

            strengths = FloatList.fromNumpyArray(array.astype('f'))
            return strengths
