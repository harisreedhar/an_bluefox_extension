import os
import bpy
from bpy.props import *
from ... utils import save_to_disk as sd
from . disk_cache_writer import classTypeItems
from animation_nodes . base_types import AnimationNode

class BF_DiskCacheReaderNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_DiskCacheReaderNode"
    bl_label = "Disk Cache Reader"
    bl_width_default = 180
    errorHandlingType = "EXCEPTION"

    filePath    : StringProperty(name="File Path", subtype='FILE_PATH', default="/tmp/an_cache.npy", update=AnimationNode.refresh)
    fileInfo    : BoolProperty(name="File Info", default=False, update=AnimationNode.refresh)
    classType   : EnumProperty(name="Output List Type", default="VECTOR", items=classTypeItems, update=AnimationNode.refresh)
    fileType    : StringProperty(default="Unknown")
    startFrame  : IntProperty(default=0)
    endFrame    : IntProperty(default=0)
    length      : IntProperty(default=0)

    def create(self):
        self.newInput("Float", "Frame", "frame")
        self.newInput("Boolean", "Loop", "loop", value=False)
        socketType = self.classType.title() + " List"
        self.newOutput(socketType, "Data", "out")

    def draw(self, layout):
        layout.prop(self, "classType", text="")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "filePath", text="")
        row.prop(self, "fileInfo", text="", icon="INFO")
        if self.fileInfo:
            col.label(text = f"Type: {self.fileType.title()}")
            col.label(text = f"Start Frame: {self.startFrame}")
            col.label(text = f"End Frame: {self.endFrame}")

    def execute(self, frame, loop):
        try:
            if not os.path.isfile(self.filePath):
                self.raiseErrorMessage("File not exist")
            reader = sd.Reader(self.filePath)
            self.fileType = reader.classType
            if self.fileType != self.classType:
                self.raiseErrorMessage(f"{self.fileType} -> {self.classType}")
            self.startFrame = reader.startFrame
            self.endFrame = reader.endFrame
            self.length = reader.n
            index = self.getIndex(frame, loop=loop)
            return reader[index]
        except Exception as e:
            self.raiseErrorMessage("ERROR: " + str(e))
            return self.outputs[0].getDefaultValue()

    def getIndex(self, frame, loop=False):
        index = int((frame - self.startFrame) % self.length)
        if not loop:
            if frame < self.startFrame:
                index = 0
            if frame > self.endFrame:
                index = -1
        return index
