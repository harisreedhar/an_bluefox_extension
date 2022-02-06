import bpy
from bpy.props import *
from dataclasses import dataclass
from ... utils import save_to_disk as sd
from animation_nodes . base_types import AnimationNode

classTypeItems = {
    ("BOOLEAN", "Boolean", "Boolean list", "", 0),
    ("INTEGER", "Integer", "Integer list", "", 1),
    ("FLOAT", "Float", "Float list", "", 2),
    ("VECTOR", "Vector", "3D Vector list", "", 3),
    ("COLOR", "Color", "Color list", "", 4),
    ("QUATERNION", "Quaternion", "Quaternion list", "", 5),
    ("MATRIX", "Matrix", "4x4 Matrix list", "", 6)
}

@dataclass
class DataContainer:
    data: list
    filePath: str
    classType: str
    startFrame: int
    endFrame: int
    maxLength: int

cache = {}

class BF_DiskCacheWriterNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_DiskCacheWriterNode"
    bl_label = "Disk Cache Writer"
    bl_width_default = 180
    errorHandlingType = "EXCEPTION"

    classType: EnumProperty(name="Input List Type", default="VECTOR", items=classTypeItems, update=AnimationNode.refresh)

    def create(self):
        self.newInput("Text", "File Path", "filePath",
            value="/tmp/an_cache.npy",
            showFileChooser = True,
            defaultDrawType = "PROPERTY_ONLY")
        socketType = self.classType.title() + " List"
        self.newInput(socketType, "Data", "data")
        self.newInput("Integer", "Start Frame", "startFrame", value = 1)
        self.newInput("Integer", "End Frame", "endFrame", value = 250)
        self.newInput("Integer", "Max List Length", "maxListLength", minValue=1, value = 1000)
        self.newOutput("Text", "File Path", "filePath")

    def draw(self, layout):
        col = layout.column(align=True)
        subcol = col.column(align=True)
        subcol.scale_y = 1.5
        subrow = subcol.row(align=True)
        self.invokeFunction(subrow, "writeToDisk", description="Write to disk", text="Write", icon="DISK_DRIVE")
        self.invokeFunction(subrow, "deleteDiskCache", description="Delete from disk", text="Delete", icon="TRASH")
        col = layout.column(align=True)
        subcol = col.column(align=True)
        row = subcol.row(align=True)
        row.prop(self, "classType", text='')

    def writeToDisk(self):
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        wm.progress_update(1)

        try:
            packedData = cache.get(self.identifier, None)
            if packedData is None: return

            filePath = packedData.filePath
            classType = packedData.classType
            startFrame = packedData.startFrame
            endFrame = packedData.endFrame
            maxLength = packedData.maxLength

            if maxLength < 1 : return
            n = endFrame - startFrame + 1

            info = {
                'n': n,
                'max_length': maxLength,
                'start_frame': startFrame,
                'end_frame': endFrame,
                'class_type': classType
            }
            restoreFrame = bpy.context.scene.frame_current
            with sd.Writer(filePath, info) as f:
                count = 0
                for i in range(startFrame, endFrame + 1):
                    bpy.context.scene.frame_set(i)
                    data = cache.get(self.identifier, None).data
                    if data is None:return
                    f.add(data)
                    wm.progress_update(int((count/n) * 100))
                    count += 1
            bpy.context.scene.frame_set(restoreFrame)

        except Exception as e:
            print("Disk writing Failed")
            print(str(e))

        self.delete()
        wm.progress_end()

    def execute(self, filePath, data, startFrame, endFrame, maxListLength):
        if startFrame >= endFrame:
            self.raiseErrorMessage("End Frame should be greater than Start Frame")

        listLength = len(data)
        if listLength > maxListLength:
            data = data[:maxListLength]

        cache[self.identifier] = DataContainer(
            data,
            filePath,
            self.classType,
            startFrame,
            endFrame,
            maxListLength)

        return filePath

    def deleteDiskCache(self):
        data = cache.get(self.identifier, None)
        if data:
            sd.delete(data.filePath)

    def delete(self):
        keys = list(cache.keys())
        for key in keys:
            if key.startswith(self.identifier):
                cache.pop(key, None)
