import bpy
import numpy as np
from bpy.props import *
from . effex_base import EffexBase
from animation_nodes . base_types import AnimationNode
from animation_nodes . nodes.rotation.c_utils import eulersToVectors
from .... utils . formula import evaluateFormula, isValidVariableName
from animation_nodes . data_structures import FloatList, VirtualDoubleList, VirtualLongList

class BF_FormulaEffexNode(bpy.types.Node, AnimationNode, EffexBase):
    bl_idname = "an_bf_FormulaEffexNode"
    bl_label = "Formula Effex"
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
        self.newInput("Struct", "Variables", "variables")
        self.createBasicInputs()
        self.newOutput("Matrix List", "Matrices", "matrices")
        self.newOutput("Float List", "Values", "effexValues", hide = True)
        self.updateSocketVisibility()

    def draw(self, layout):
        col = layout.column(align=True)
        col.prop(self, "formula", text = "")
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
        if "matrices" in required or "effexValues" in required:
            yield "effexValues = AN.data_structures.DoubleList()"
            if any([self.useTranslation, self.useRotation, self.useScale]):
                yield "efStrengths = AN.data_structures.FloatList()"
                yield "try:"
                yield "    efStrengths = self.getFormulaStrengths(matrices, falloff, variables)"
                yield "    mixedFalloff = self.mixEffexAndFalloff(efStrengths, falloff, interpolation, outMin=minValue, outMax=maxValue)"
                yield "    influences = self.getInfluences(mixedFalloff, matrices)"
                yield "    matrices = self.offsetMatrixList(matrices, influences, translation, rotation, scale)"
                if "effexValues" in required:
                    yield "    effexValues = AN.data_structures.DoubleList.fromValues(influences)"
                yield "except Exception as e:"
                yield "    self.setErrorMessage(f'Formula error! {str(e)}')"

    def getFormulaStrengths(self, matrices, falloff, userInputs):
        formula = self.formula
        variables = dict()
        if formula != "":
            t,r,s = self.getMatriceComponents(matrices)
            if self.incPosAttr:
                arrT = t.asNumpyArray().reshape(-1,3)
                variables['px'] = arrT[:,0]
                variables['py'] = arrT[:,1]
                variables['pz'] = arrT[:,2]
            if self.incRotAttr:
                r = eulersToVectors(r, False)
                arrR = r.asNumpyArray().reshape(-1,3)
                variables['rx'] = arrR[:,0]
                variables['ry'] = arrR[:,1]
                variables['rz'] = arrR[:,2]
            if self.incScaleAttr:
                arrS = s.asNumpyArray().reshape(-1,3)
                variables['sx'] = arrS[:,0]
                variables['sy'] = arrS[:,1]
                variables['sz'] = arrS[:,2]
            if self.incFalloffAttr:
                influences = self.getInfluences(falloff, matrices).copy()
                variables["falloff"] = influences.asNumpyArray()

            totalCount = len(matrices)

            for key, value in zip(userInputs.keys(), userInputs.values()):
                varType = key[0]
                varName = key[1]
                if not isValidVariableName(varName):
                    self.raiseErrorMessage(f"Invalid variable name '{varName}' ")
                    return
                if varType == "Float List":
                    if len(value):
                        _value = VirtualDoubleList.create(value, 0).materialize(totalCount)
                        variables[varName] = _value.asNumpyArray().astype('f')
                elif varType == "Integer List":
                    if len(value):
                        _value = VirtualLongList.create(value, 0).materialize(totalCount)
                        variables[varName] = _value.asNumpyArray().astype('f')
                elif varType in ("Float", "Integer"):
                    variables[varName] = value
                else:
                    self.raiseErrorMessage("Variable must be Float or Integer type")

            array = evaluateFormula(formula, count = totalCount, vars = variables)

            strengths = FloatList.fromNumpyArray(array.astype('f'))
            return strengths
