import bpy
from bpy.props import *
from animation_nodes . base_types import AnimationNode
from animation_nodes . nodes . falloff . constant_falloff import ConstantFalloff

falloffCache = {}

mixModeItems = [
    ("MAX", "Max", "", "", 0),
    ("MIN", "Min", "", "", 1)
]

class BF_MemoryFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_MemoryFalloffNode"
    bl_label = "Memory Falloff"
    bl_width_default = 150

    mixMode: EnumProperty(name = "Mix", default = "MAX",
        items = mixModeItems, update = AnimationNode.refresh)

    outputFalloffList: BoolProperty(name = "Output Falloff List", default = False,
        update = AnimationNode.refresh)

    def create(self):
        self.newInput("Falloff", "Falloff", "falloff", dataIsModified = True)
        self.newInput("Integer", "Reset Frame", "resetframe", value = 1)
        self.newInput("Integer", "Start Frame", "startframe", value = 1, minValue = 0)
        self.newInput("Integer", "Length", "length", value = 250, minValue = 1)

        if self.outputFalloffList:
            self.newOutput("Falloff List", "Falloff", "falloffOut")
        else:
            self.newOutput("Falloff", "Falloff", "falloffOut")

    def draw(self, layout):
        if not self.outputFalloffList:
            layout.prop(self, "mixMode", text = "")

    def drawAdvanced(self, layout):
        layout.prop(self, "outputFalloffList")

    def getExecutionCode(self, required):
        if "falloffOut" in required:
            yield "result = self.memoryFalloff(falloff, resetframe, startframe, length)"
            if self.outputFalloffList:
                yield "falloffOut = result"
            else:
                yield "falloffOut = AN.nodes.falloff.mix_falloffs.MixFalloffs(result, self.mixMode)"

    loopingIndex = 0
    def memoryFalloff(self, falloff, resetframe, startframe, length):
        try:
            identifier = self.identifier
            if self.network.isSubnetwork:
                identifier = self.network.identifier + str(self.loopingIndex)

            currentFrame = bpy.context.scene.frame_current
            startframe = max(0, currentFrame - startframe)
            length = abs(length)
            index = max(0, min(length - 1, startframe))

            if falloffCache.get(identifier) is None:
                falloffCache[identifier] = [falloff] * length

            if currentFrame == resetframe or len(falloffCache[identifier]) != length:
                falloffCache[identifier] = [self.getDefaultFalloff()] * length

            falloffList = falloffCache.get(identifier)
            falloffList[index] = falloff
            self.loopingIndex += 1
            return falloffList
        except:
            return [falloff]

    def getDefaultFalloff(self):
        if self.mixMode in ['MAX']:
            return ConstantFalloff(0)
        if self.mixMode in ['MIN']:
            return ConstantFalloff(1)
