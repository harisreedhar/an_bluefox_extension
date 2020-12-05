import bpy
from bpy.props import *
from animation_nodes . base_types import AnimationNode
from animation_nodes . nodes . falloff . constant_falloff import ConstantFalloff
from animation_nodes . data_structures cimport CompoundFalloff, Falloff
from libc.math cimport (sin, cos, tan, asin, acos,
                        atan, atan2, fabs, floor,
                        ceil, sqrt, pow, log, round)

operationTypeItems = [
    ("ADD", "Add", "", "NONE", 0),
    ("SUBTRACT", "Subtract", "", "NONE", 1),
    ("MULTIPLY", "Multiply", "", "NONE", 2),
    ("DIVIDE", "Divide", "", "NONE", 3),
    ("MODULO", "Modulo", "", "NONE", 4),
    ("SQUAREROOT", "Square Root", "", "NONE", 5),
    ("POWER", "Power", "", "NONE", 6),
    ("LOG", "Logarithm", "", "NONE", 7),

    ("SIN", "Sin", "", "NONE", 8),
    ("COS", "Cos", "", "NONE", 9),
    ("TAN", "Tan", "", "NONE", 10),
    ("ARCSIN", "ArcSin", "", "NONE", 11),
    ("ARCCOS", "ArcCosine", "", "NONE", 12),
    ("ARCTAN", "ArcTangent", "", "NONE", 13),
    ("ARCTAN2", "ArcTangent B/A", "", "NONE", 14),

    ("MAX", "Maximum", "", "NONE", 15),
    ("MIN", "Minimum", "", "NONE", 16),
    ("LESSTHAN", "Less Than", "", "NONE", 17),
    ("GREATERTHAN", "Greater Than", "", "NONE", 18),
    ("ABSOLUTE", "Absolute", "", "NONE", 19),
    ("FLOOR", "Floor", "", "NONE", 20),
    ("CEIL", "Ceil", "", "NONE", 21),
    ("SNAP", "Snap", "", "NONE", 22),
    ("AVERAGE", "Average", "", "NONE", 23),
]

class BF_MathFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_MathFalloffNode"
    bl_label = "Math Falloff"
    errorHandlingType = "EXCEPTION"

    __annotations__ = {}

    __annotations__["operationType"] = EnumProperty(name = "Operation Type", items = operationTypeItems,
        default = "ADD", update = AnimationNode.refresh)

    def create(self):
        self.newInput("Falloff", "A", "a")
        if self.checkTwoInputOperation():
            self.newInput("Falloff", "B", "b")

        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        row = layout.row(align = True)
        row.prop(self, "operationType", text = "")

    def execute(self, *args):
        a = args[0]
        b = ConstantFalloff(1)
        if self.checkTwoInputOperation():
            b = args[1]

        return MathFalloffs([a, b], self.operationType, default = 1)

    def checkTwoInputOperation(self):
        twoOperationList = ['ADD', 'MULTIPLY', 'MAX', 'MIN',
                            'SUBTRACT', 'DIVIDE', 'POWER',
                            'MODULO', 'SNAP', 'ARCTAN2',
                            'LESSTHAN', 'GREATERTHAN', 'AVERAGE']
        return self.operationType in twoOperationList

class MathFalloffs:
    def __new__(cls, list falloffs not None, str method not None, double default = 1):
        if len(falloffs) == 0:
            return ConstantFalloff(default)
        if len(falloffs) == 1:
            pass
        if len(falloffs) == 2:
            if method == "SIN": return SinFalloff(*falloffs)
            elif method == "COS": return CosFalloff(*falloffs)
            elif method == "TAN": return TanFalloff(*falloffs)
            elif method == "ARCSIN": return ArcSinFalloff(*falloffs)
            elif method == "ARCCOS": return ArcCosFalloff(*falloffs)
            elif method == "ARCTAN": return ArcTanFalloff(*falloffs)
            elif method == "LOG": return LogarithmFalloff(*falloffs)
            elif method == "ABSOLUTE": return AbsoluteFalloff(*falloffs)
            elif method == "FLOOR": return FloorFalloff(*falloffs)
            elif method == "CEIL": return CeilFalloff(*falloffs)
            elif method == "SQUAREROOT": return SquareRootFalloff(*falloffs)

            elif method == "ADD": return AddTwoFalloffs(*falloffs)
            elif method == "MULTIPLY": return MultiplyTwoFalloffs(*falloffs)
            elif method == "MAX": return MaxTwoFalloffs(*falloffs)
            elif method == "MIN": return MinTwoFalloffs(*falloffs)
            elif method == "LESSTHAN": return LessThanTwoFalloffs(*falloffs)
            elif method == "GREATERTHAN": return GreaterThanTwoFalloffs(*falloffs)
            elif method == "SUBTRACT": return SubtractTwoFalloffs(*falloffs)
            elif method == "DIVIDE": return DivideFalloff(*falloffs)
            elif method == "POWER": return PowerFalloff(*falloffs)
            elif method == "MODULO": return ModuloFalloff(*falloffs)
            elif method == "SNAP": return SnapFalloff(*falloffs)
            elif method == "ARCTAN2": return ArcTan2Falloff(*falloffs)
            elif method == "AVERAGE": return AverageFalloff(*falloffs)

            raise Exception("invalid method")

# Operations with two falloffs
##############################
cdef class OperationTwoFalloffBase(CompoundFalloff):
    cdef:
        Falloff a, b

    def __cinit__(self, Falloff a, Falloff b):
        self.a = a
        self.b = b

    cdef list getDependencies(self):
        return [self.a, self.b]

cdef class AddTwoFalloffs(OperationTwoFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return dependencyResults[0] + dependencyResults[1]

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = a[i] + b[i]

cdef class MultiplyTwoFalloffs(OperationTwoFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return dependencyResults[0] * dependencyResults[1]

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = a[i] * b[i]

cdef class MinTwoFalloffs(OperationTwoFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return min(dependencyResults[0], dependencyResults[1])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = min(a[i], b[i])

cdef class MaxTwoFalloffs(OperationTwoFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return max(dependencyResults[0], dependencyResults[1])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = max(a[i], b[i])

cdef class LessThanTwoFalloffs(OperationTwoFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return <float>(dependencyResults[0] < dependencyResults[1])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = <float>(a[i] < b[i])

cdef class GreaterThanTwoFalloffs(OperationTwoFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return <float>(dependencyResults[0] > dependencyResults[1])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = <float>(a[i] > b[i])

cdef class SubtractTwoFalloffs(OperationTwoFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return dependencyResults[0] - dependencyResults[1]

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = a[i] - b[i]

cdef class DivideFalloff(OperationTwoFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        if dependencyResults[1] != 0:
            return dependencyResults[0] / dependencyResults[1]

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            if b[i] != 0:
                target[i] = a[i] / b[i]

cdef class PowerFalloff(OperationTwoFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        if dependencyResults[0] >= 0 or dependencyResults[1] % 1 == 0:
            return pow(dependencyResults[0], dependencyResults[1])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            if a[i] >= 0 or b[i] % 1 == 0:
                target[i] = pow(a[i], b[i])

cdef class ModuloFalloff(OperationTwoFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        if dependencyResults[1] != 0:
            return dependencyResults[0] % dependencyResults[1]

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            if b[i] != 0:
                target[i] = a[i] % b[i]

cdef class SnapFalloff(OperationTwoFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        if dependencyResults[1] != 0:
            return round(dependencyResults[0] / dependencyResults[1]) * dependencyResults[1]
        return dependencyResults[0]

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            if b[i] != 0:
                target[i] = round(a[i] / b[i]) * b[i]
            else:
                target[i] = a[i]

cdef class ArcTan2Falloff(OperationTwoFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return atan2(dependencyResults[1], dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = atan2(b[i], a[i])

cdef class AverageFalloff(OperationTwoFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return (dependencyResults[1] + dependencyResults[0]) * 0.5

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = (b[i] + a[i]) * 0.5

# Operations with single falloff
################################
cdef class OperationSingleFalloffBase(CompoundFalloff):
    cdef:
        Falloff a

    def __cinit__(self, Falloff a, Falloff b):
        self.a = a

    cdef list getDependencies(self):
        return [self.a]

cdef class SinFalloff(OperationSingleFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return sin(dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        for i in range(amount):
            target[i] = sin(a[i])

cdef class CosFalloff(OperationSingleFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return cos(dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        for i in range(amount):
            target[i] = cos(a[i])

cdef class TanFalloff(OperationSingleFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return tan(dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        for i in range(amount):
            target[i] = tan(a[i])

cdef class ArcSinFalloff(OperationSingleFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return asin(min(max(dependencyResults[0], -1), 1))

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        for i in range(amount):
            target[i] = asin(min(max(a[i], -1), 1))

cdef class ArcCosFalloff(OperationSingleFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return acos(min(max(dependencyResults[0], -1), 1))

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        for i in range(amount):
            target[i] = acos(min(max(a[i], -1), 1))

cdef class ArcTanFalloff(OperationSingleFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return atan(dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        for i in range(amount):
            target[i] = atan(a[i])

cdef class LogarithmFalloff(OperationSingleFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return log(dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        for i in range(amount):
            target[i] = log(a[i])

cdef class AbsoluteFalloff(OperationSingleFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return fabs(dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        for i in range(amount):
            target[i] = fabs(a[i])

cdef class FloorFalloff(OperationSingleFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return floor(dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        for i in range(amount):
            target[i] = floor(a[i])

cdef class CeilFalloff(OperationSingleFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return ceil(dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        for i in range(amount):
            target[i] = ceil(a[i])

cdef class SquareRootFalloff(OperationSingleFalloffBase):
    cdef float evaluate(self, float *dependencyResults):
        return sqrt(dependencyResults[0])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        for i in range(amount):
            target[i] = sqrt(a[i])
