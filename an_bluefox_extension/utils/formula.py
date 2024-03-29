import bpy
import numpy as np
from ast import parse

def checkIter(object):
    try:
        iterator = iter(object)
        return True
    except:
        return False

def isValidVariableName(name):
    try:
        parse('{} = None'.format(name))
        return True
    except (SyntaxError, ValueError, TypeError):
        return False

def evaluateFormula(formula, count=None, vars=dict()):
    for key,value in vars.items():
        exec(key + '=value')

    if count is not None:
        id = np.linspace(0, count-1, num = count, dtype = "int")
    frame = bpy.context.scene.frame_current

    # constants
    pi = np.pi
    e = np.e
    tau = 2 * pi

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
    def sinh(x):return np.sinh(x)
    def cosh(x):return np.cosh(x)
    def tanh(x):return np.tanh(x)
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
    def rnd(*args):
        argLen = len(args)
        if argLen > 0:
            np.random.seed(int(args[-1]))
        if argLen == 2:
            return np.random.uniform(0, args[0], count)
        elif argLen == 3:
            return np.random.uniform(args[0], args[1], count)
        else:
            return np.random.rand(count)

    evaluatedValue = eval(formula)

    if not isinstance(evaluatedValue, (np.ndarray, np.generic)):
        if not checkIter(evaluatedValue):
            evaluatedValue = np.array([evaluatedValue] * count)
        else:
            evaluatedValue = np.array(evaluatedValue)

    return evaluatedValue
