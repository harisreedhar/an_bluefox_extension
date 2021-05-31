import bpy
from bpy.props import *
from animation_nodes . base_types import AnimationNode, VectorizedSocket
from animation_nodes . events import propertyChanged, executionCodeChanged

trackAxisItems = [(axis, axis, "") for axis in ("X", "Y", "Z", "-X", "-Y", "-Z")]
guideAxisItems  = [(axis, axis, "") for axis in ("X", "Y", "Z")]
directionAxisItems = [(axis, axis, "", "", i)
                      for i, axis in enumerate(("X", "Y", "Z", "-X", "-Y", "-Z"))]

class BF_TargetEffexNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_TargetEffexNode"
    bl_label = "Target Effex"
    bl_width_default = 200

    trackAxis: EnumProperty(items = trackAxisItems, update = propertyChanged, default = "Z")
    guideAxis: EnumProperty(items = guideAxisItems, update = propertyChanged, default = "X")
    directionAxis: EnumProperty(name = "Direction Axis", default = "Z",
        items = directionAxisItems, update = propertyChanged)

    useTargetList: VectorizedSocket.newProperty()

    def checkedPropertiesChanged(self, context):
        self.updateSocketVisibility()
        executionCodeChanged()

    useOffset: BoolProperty(update = checkedPropertiesChanged)
    useDirection: BoolProperty(update = checkedPropertiesChanged)

    def create(self):
        self.newInput("Matrix List", "Matrices", "matrices")
        self.newInput(VectorizedSocket("Matrix", "useTargetList",
            ("Target", "targets"), ("Targets", "targets")))
        self.newInput("Float", "Distance", "distanceIn")
        self.newInput("Float", "Width", "width", value = 3.0)
        self.newInput("Float", "Strength", "offsetStrength", value = 1.0)
        self.newInput("Vector", "Guide", "guideIn", value = (0,0,1), hide = True)
        self.newInput("Falloff", "Falloff", "falloff")
        self.newOutput("Matrix List", "Matrices", "matricesOut")
        self.newOutput("Float List", "Values", "values", hide = True)

        self.updateSocketVisibility()

    def draw(self, layout):
        col = layout.column(align = True)
        row = col.row(align = True)
        row.prop(self, "useDirection", text = "Direction", toggle = True, icon = "ORIENTATION_GLOBAL")
        row.prop(self, "useOffset", text = "Offset", toggle = True, icon = "MOD_OFFSET")
        if self.useDirection:
            layout.prop(self, "trackAxis", expand = True)
            layout.prop(self, "guideAxis", expand = True)
            if self.trackAxis[-1:] == self.guideAxis[-1:]:
                layout.label(text = "Must be different", icon = "ERROR")

    def drawAdvanced(self, layout):
        layout.prop(self, "directionAxis", expand = True)

    def updateSocketVisibility(self):
        condition = self.useOffset
        self.inputs[2].hide = not condition
        self.inputs[3].hide = not condition
        self.inputs[4].hide = not self.useOffset

    def getExecutionCode(self, required):
        if not self.useTargetList:
            yield "targets = Matrix4x4List.fromValues([targets])"
        if self.useDirection or self.useOffset:
            yield "count = len(matrices)"
            yield "vectors = AN.nodes.matrix.c_utils.extractMatrixTranslations(matrices)"
            yield "scales = AN.nodes.matrix.c_utils.extractMatrixScales(matrices)"
            yield "rotations = AN.nodes.matrix.c_utils.extractMatrixRotations(matrices)"
            yield "falloffEvaluator = self.getFalloffEvaluator(falloff)"
            yield "influences = falloffEvaluator.evaluateList(vectors)"
            yield "func = an_bluefox_extension.nodes.matrix.effex.c_utils.targetEffexFunction"
            yield "vectors, d, s = func(targets, vectors, distanceIn, width, offsetStrength, influences, self.useOffset, self.useDirection)"
            yield "newRotations = AN.algorithms.rotations.directionsToMatrices(d, guideIn, self.trackAxis, self.guideAxis).toEulers()"
            yield "newRotations = an_bluefox_extension.utils.mix.eulerListLerp(rotations, newRotations, influences)"
            yield "_v = VirtualVector3DList.create(vectors, (0, 0, 0))"
            yield "_r = VirtualEulerList.create(newRotations, (0, 0, 0))"
            yield "_s = VirtualVector3DList.create(scales, (1, 1, 1))"
            yield "matricesOut = AN.nodes.matrix.c_utils.composeMatrices(count, _v, _r, _s)"
            yield "values = DoubleList.fromValues(s)"
        else:
            yield "matricesOut = matrices"
            yield "values = DoubleList()"

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")

    def getUsedModules(self):
        return ['an_bluefox_extension']
