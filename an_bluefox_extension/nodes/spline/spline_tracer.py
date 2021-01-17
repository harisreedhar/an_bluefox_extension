import bpy
from bpy.props import *
from animation_nodes . events import propertyChanged
from animation_nodes . base_types import AnimationNode, VectorizedSocket
from animation_nodes . data_structures import Vector3DList, PolySpline, VirtualDoubleList

class BF_SplineTracerNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_SplineTracerNode"
    bl_label = "Spline Tracer"
    bl_width_default = 150
    errorHandlingType = "EXCEPTION"

    codeEffects = [VectorizedSocket.CodeEffect]
    for attr in ["Vector","StartFrame","EndFrame","Radius","Tilt","MinDistance","Smoothness"]:
        exec("use{}List: VectorizedSocket.newProperty()".format(attr), globals(), locals())

    executionIndex = 0
    executionCache = {}

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

        self.newInput("Scene", "Scene", "scene", hide = True)

        listCollection = ["useVectorList", "useStartFrameList", "useEndFrameList",
                          "useRadiusList", "useTiltList", "useMinDistanceList"]

        self.newOutput(VectorizedSocket("Spline", listCollection,
            ("Spline", "spline"), ("Splines", "spline")))

    def execute(self, point, startFrame, endFrame, radius, tilt, minDistance, scene):
        self.executionIndex += 1
        if scene is None:
            return PolySpline()

        sceneStart = scene.frame_start
        currentFrame = scene.frame_current
        identifier = self.identifier + str(self.executionIndex)
        spline = self.executionCache.get(identifier)

        if currentFrame in [startFrame, sceneStart] or spline is None:
            self.executionCache[identifier] = PolySpline()
            return PolySpline()

        if currentFrame > startFrame and currentFrame <= endFrame:
            if self.validateMinDistance(point, spline, minDistance):
                spline.appendPoint(point, radius, tilt)

        return spline

    def validateMinDistance(self, point, spline, minDistance):
        if len(spline.points):
            pointDistance = (spline.points[-1] - point).length
            return pointDistance >= minDistance
        return True
