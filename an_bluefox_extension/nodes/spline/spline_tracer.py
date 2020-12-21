import bpy
from bpy.props import *
from animation_nodes . events import propertyChanged
from animation_nodes . base_types import AnimationNode, VectorizedSocket
from animation_nodes . nodes . spline . spline_evaluation_base import SplineEvaluationBase
from animation_nodes . data_structures import Vector3DList, PolySpline, BezierSpline, VirtualDoubleList

splineTypeItems = [
    ("POLY", "Poly Spline", "Trace points as Poly Spline", "NONE", 0),
    ("BEZIER", "Bezier Spline", "Trace points as Bezier Spline", "NONE", 1)]

splineCache = {}

class BF_SplineTracerNode(bpy.types.Node, AnimationNode, SplineEvaluationBase):
    bl_idname = "an_bf_SplineTracerNode"
    bl_label = "Spline Tracer"
    bl_width_default = 150
    errorHandlingType = "EXCEPTION"

    useVectorList: VectorizedSocket.newProperty()
    splineType: EnumProperty(name = "Spline Type", default = "POLY",
        items = splineTypeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput(VectorizedSocket("Vector", "useVectorList",
            ("Point", "point"), ("Points", "point")))
        self.newInput("Boolean", "Trace Condition", "traceCondition", hide = True)
        self.newInput("Integer", "Reset Frame", "resetframe", value = 1)
        self.newInput("Integer", "Start Frame", "start", value = 1)
        self.newInput("Integer", "End Frame", "end", value = 250)
        self.newInput("Float", "Radius", "radius", value = 0.1, minValue = 0, hide = True)
        self.newInput("Float", "Tilt", "tilt", hide = True)
        self.newInput("Float", "Min Distance", "minDistance", value = 0.01, minValue = 0)
        if self.splineType == "BEZIER":
            self.newInput("Float", "Smoothness", "smoothness", value = 0.33, hide = True)
        self.newInput("Scene", "Scene", "scene", hide = True)

        self.newOutput(VectorizedSocket("Spline", "useVectorList",
            ("Spline", "spline"), ("Splines", "spline")))

    def draw(self, layout):
        layout.prop(self, "splineType", text = "")

    def execute(self, point, *args):
        if self.useVectorList:
            return self.tracePointsToSplines(point, args)
        return self.tracePointsToSplines([point], args)[0]

    loopingIndex = 0
    def tracePointsToSplines(self, *args):
        points = args[0]
        identifier = self.identifier
        if self.network.isSubnetwork:
            identifier = self.network.identifier + str(self.loopingIndex)
        tracePointToSpline = self.tracePointToSpline
        splines = [tracePointToSpline(identifier + str(i),
                    point, args[1]) for i, point in enumerate(points)]
        self.loopingIndex += 1
        return splines

    def tracePointToSpline(self, identifier, point, args):
        traceCondition, resetFrame, startFrame, endFrame, radius, tilt, minDistance = args[:7]
        frame, scene = 0, args[-1]
        if scene is not None:
            frame = scene.frame_current_final
        self.resetCache(identifier, frame, resetFrame)
        spline = self.getSpline(identifier)
        if traceCondition:
            if frame >= startFrame and frame <= endFrame:
                if self.minimumTraceDistance(minDistance, spline, point):
                    if self.splineType == "POLY":
                        spline.appendPoint(point, radius, tilt)
                    if self.splineType == "BEZIER":
                        spline.appendPoint(point, (0,0,0), (0,0,0), radius, tilt)
                        spline.smoothAllHandles(args[-2])
        return spline

    def resetCache(self, identifier, frame, resetFrame):
        if frame == resetFrame:
            cache = self.getCache()
            cache.clear()
        return

    def minimumTraceDistance(self, minDistance, spline, point):
        if len(spline.points):
            pointDistance = (spline.points[-1] - point).length
            return pointDistance >= minDistance
        return True

    def defaultSpline(self):
        if self.splineType == "POLY":
            return PolySpline()
        if self.splineType == "BEZIER":
            return BezierSpline()

    def getSpline(self, identifier):
        spline = self.getCachedSpline(identifier)
        if spline is not None:
            if spline.type != self.splineType:
                spline = None
        if spline is None:
            self.setCache(identifier, self.defaultSpline())
            spline = self.getCachedSpline(identifier)
        return spline

    def getCache(self):
        data = splineCache.get(self.identifier, None)
        if data is None:
            data = {}
            splineCache[self.identifier] = data
        return data

    def setCache(self, identifier, value):
        data = self.getCache()
        data[identifier] = value
        return

    def getCachedSpline(self, identifier):
        return self.getCache().get(identifier, None)
