import os
import bpy
from bpy.props import *
from ... utils import save_to_disk as sd
from . disk_cache_writer import classTypeItems
from animation_nodes . base_types import AnimationNode

class BF_DiskCacheReaderNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_DiskCacheReaderNode"
    bl_label = "Disk Cache Reader"
    bl_width_default = 150
    errorHandlingType = "EXCEPTION"

    classType: EnumProperty(name="Output List Type", default="VECTOR", items=classTypeItems, update=AnimationNode.refresh)

    def create(self):
        self.newInput("Text", "File Path", "filePath",
            value="/tmp/an_cache.npy",
            showFileChooser = True,
            defaultDrawType = "PROPERTY_ONLY")
        self.newInput("Integer", "Frame", "frame", value=1)
        self.newInput("Boolean", "Accumulate", "accumulate", value=False)
        socketType = self.classType.title() + " List"
        self.newOutput(socketType, "Data", "out")

    def draw(self, layout):
        layout.prop(self, "classType", text="")

    def execute(self, filePath, frame, accumulate):
        try:
            if not os.path.exists(filePath):
                self.raiseErrorMessage("File does not exist")

            reader = sd.Reader(filePath)
            classType = reader.classType
            if classType != self.classType:
                self.raiseErrorMessage(f"{classType} -> {self.classType}")

            startFrame = reader.startFrame
            endFrame = reader.endFrame
            length = reader.n

            index = int((frame - startFrame) % length)
            if frame < startFrame:
                index = 0
            if frame > endFrame:
                index = length - 1

            if accumulate and index > 0:
                result = reader[0]
                for i in range(min(index + 1, length)):
                    if i > 0:
                        result.extend(reader[i])
                return result

            return reader[index]

        except Exception as e:
            self.raiseErrorMessage("ERROR: " + str(e))
            return self.outputs[0].getDefaultValue()
