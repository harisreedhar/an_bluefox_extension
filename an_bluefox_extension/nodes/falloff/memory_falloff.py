import bpy
import numpy as np
from bpy.props import *
from animation_nodes . base_types import AnimationNode
from animation_nodes . nodes . falloff . mix_falloffs import MixFalloffs
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
    enableFade: BoolProperty(name = "Enable Fade", default = False, update = AnimationNode.refresh)
    executionIndex = 0

    def create(self):
        self.newInput("Falloff", "Falloff", "falloff", dataIsModified = True)
        self.newInput("Integer", "Reset Frame", "resetFrame", value = 1)
        self.newInput("Integer", "Start Frame", "startFrame", value = 1, minValue = 0)
        self.newInput("Integer", "Length", "length", value = 250, minValue = 1)
        if self.enableFade:
            self.newInput("Integer", "Fade Length", "fadeLength", value = 25, minValue = 1)
            self.newInput("Float", "Fade Min", "fadeMin", value = 0, hide = True)
            self.newInput("Float", "Fade Max", "fadeMax", value = 1, hide = True)

        if self.outputFalloffList:
            self.newOutput("Falloff List", "Falloff", "falloffOut")
        else:
            self.newOutput("Falloff", "Falloff", "falloffOut")

    def draw(self, layout):
        if not self.outputFalloffList:
            layout.prop(self, "mixMode", text = "")
        layout.prop(self, "enableFade")

    def drawAdvanced(self, layout):
        layout.prop(self, "outputFalloffList")

    def getExecutionCode(self, required):
        if "falloffOut" in required:
            yield "currentFrame = bpy.context.scene.frame_current"
            if self.enableFade:
                yield "result = self.fadedMemoryFalloff(falloff, currentFrame, resetFrame, startFrame, length, fadeLength, fadeMin, fadeMax)"
            else:
                yield "result = self.memoryFalloff(falloff, currentFrame, resetFrame, startFrame, length)"
            if self.outputFalloffList:
                yield "falloffOut = result"
            else:
                yield "falloffOut = AN.nodes.falloff.mix_falloffs.MixFalloffs(result, self.mixMode)"

    def memoryFalloff(self, falloff, currentFrame, resetFrame, startFrame, length):
        try:
            identifier = self.identifier + str(self.executionIndex)
            startFrame = max(0, currentFrame - startFrame)
            length = abs(length)
            index = max(0, min(length - 1, startFrame))

            if falloffCache.get(identifier) is None:
                falloffCache[identifier] = [falloff] * length

            if currentFrame == resetFrame or len(falloffCache[identifier]) != length:
                falloffCache[identifier] = [self.getDefaultFalloff()] * length

            falloffList = falloffCache.get(identifier)
            falloffList[index] = falloff
            self.executionIndex += 1
            return falloffList
        except:
            return [falloff]

    def fadedMemoryFalloff(self, falloff, currentFrame, resetFrame, startFrame, length, fadeLength, fadeMin, fadeMax):
        try:
            falloffList = self.memoryFalloff(falloff, currentFrame, resetFrame, startFrame, length)
            index = currentFrame % length
            shiftedList = falloffList[index:] + falloffList[:index]
            fadeLength = abs(fadeLength)
            result = shiftedList[-fadeLength:]
            gradient = np.linspace(fadeMin, fadeMax, num=fadeLength, dtype='float32').tolist()
            result = [MixFalloffs([ConstantFalloff(g), r], 'MULTIPLY') for r,g in zip(result, gradient)]
            return result
        except:
            return [falloff]

    def getDefaultFalloff(self):
        if self.mixMode in ['MAX']:
            return ConstantFalloff(0)
        if self.mixMode in ['MIN']:
            return ConstantFalloff(1)

    def delete(self):
        keys = list(falloffCache.keys())
        for key in keys:
            if key.startswith(self.identifier):
                falloffCache.pop(key)
