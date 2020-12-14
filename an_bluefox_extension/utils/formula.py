import bpy
import numpy as np

def checkIter(object):
    try:
        iterator = iter(object)
        return True
    except:
        return False

def evaluateFormula(formula, count = 0, falloff = 0,
                          px = 0, py = 0, pz = 0,
                          rx = 0, ry = 0, rz = 0,
                          sx = 1, sy = 1, sz = 1,
                          a = 0, b = 0, c = 0,
                          d = 0, e = 0, f = 0,
                          x = 0, y = 0, z = 0):

    id = np.linspace(0, count, num = count, dtype = "int")
    frame = bpy.context.scene.frame_current

    # constants
    pi = np.pi
    e = np.e

    # functions
    def abs(x):return np.absolute(x)
    def sqrt(x):return np.sqrt(x)
    def cbrt(x):return np.cbrt(x)
    def round(x):return np.around(x)
    def floor(x):return np.floor(x)
    def ceil(x):return np.ceil(x)
    def trunc(x):return np.trunc(x)
    def clamp(x):return np.clip(x,0,1)
    def exp(x):return np.exp(x)
    def log(x):return np.log(x)
    def radians(x):return np.radians(x)
    def degrees(x):return np.degrees(x)
    def sin(x):return np.sin(x)
    def cos(x):return np.cos(x)
    def tan(x):return np.tan(x)
    def asin(x):return np.arcsin(x)
    def acos(x):return np.arccos(x)
    def atan(x):return np.arctan(x)
    def atan2(x,y):return np.arctan2(x,y)
    def mod(x,y):return np.mod(x,y)
    def pow(x,y):return np.power(x,y)
    def rem(x,y):return np.remainder(x,y)
    def max(x,y):return np.maximum(x,y)
    def min(x,y):return np.minimum(x,y)
    def copysign(x,y):return np.copysign(x,y)
    def dist(x,y):return np.linalg.norm(x-y)

    evaluatedValue = eval(formula)

    if not isinstance(evaluatedValue, (np.ndarray, np.generic)):
        if not checkIter(evaluatedValue):
            evaluatedValue = np.array([evaluatedValue] * count)
        else:
            evaluatedValue = np.array(evaluatedValue)

    return evaluatedValue
