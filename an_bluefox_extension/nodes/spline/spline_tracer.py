import bpy
from bpy.props import *
from animation_nodes . data_structures import PolySpline
from animation_nodes . base_types import AnimationNode, VectorizedSocket

class BF_SplineTracerNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_SplineTracerNode"
    bl_label = "Spline Tracer"
    bl_width_default = 150
    errorHandlingType = "EXCEPTION"

    codeEffects = [VectorizedSocket.CodeEffect]
    for attr in ["Vector","StartFrame","EndFrame","Radius","Tilt","MinDistance"]:
        exec("use{}List: VectorizedSocket.newProperty()".format(attr), globals(), locals())

    nodeIndex = 0
    nodeCache = {}

    def create(self):
        self.newInput(VectorizedSocket("Vector", "useVectorList",
            ("Point", "point"), ("Points", "point")))

        self.newInput(VectorizedSocket("Integer", "useStartFrameList",
            ("Start Frame", "startFrame", dict(value = bpy.context.scene.frame_start)),
            ("Start Frames", "startFrame")))

        self.newInput(VectorizedSocket("Integer", "useEndFrameList",
            ("End Frame", "endFrame", dict(value = bpy.context.scene.frame_end)),
            ("End Frames", "endFrame")))

        self.newInput(VectorizedSocket("Float", "useRadiusList",
            ("Radius", "radius", dict(value = 0.1)),
            ("Radii", "radius")), hide = True)

        self.newInput(VectorizedSocket("Float", "useTiltList",
            ("Tilt", "tilt"),
            ("Tilts", "tilt")), hide = True)

        self.newInput(VectorizedSocket("Float", "useMinDistanceList",
            ("Min Distance", "minDistance", dict(value = 0.1)),
            ("Min Distances", "minDistance")))

        self.newInput("Boolean", "Reset", "reset", value = False, hide = True)
        self.newInput("Scene", "Scene", "scene", hide = True)

        listCollection = ["useVectorList", "useStartFrameList", "useEndFrameList",
                          "useRadiusList", "useTiltList", "useMinDistanceList"]

        self.newOutput(VectorizedSocket("Spline", listCollection,
            ("Spline", "spline"), ("Splines", "spline")))

    def execute(self, point, startFrame, endFrame, radius, tilt, minDistance, reset, scene):
        self.nodeIndex += 1

        spline = PolySpline()
        if scene is None:
            return spline

        currentFrame = scene.frame_current
        if currentFrame < startFrame:
            return spline

        identifier = self.identifier + str(self.nodeIndex)
        spline = self.nodeCache.get(identifier)

        if (currentFrame == startFrame) or reset or spline is None:
            spline = PolySpline()
            self.nodeCache[identifier] = spline
            return spline

        if currentFrame > startFrame and currentFrame <= endFrame:
            if self.checkAppendDistance(point, spline, minDistance):
                spline.appendPoint(point, radius, tilt)

        return spline.copy()

    def checkAppendDistance(self, point, spline, minDistance):
        if len(spline.points):
            pointDistance = (spline.points[-1] - point).length
            return pointDistance >= minDistance
        return True

    def clearCache(self):
        keys = list(self.nodeCache.keys())
        for key in keys:
            if key.startswith(self.identifier):
                self.nodeCache.pop(key, None)

    def delete(self):
        self.clearCache()
