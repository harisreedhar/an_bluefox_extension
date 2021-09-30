import bpy
from bpy.props import *
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

lengthTypeItems = {
    ("CONSTANT", "Constant", "Constant input list length", "", 0),
    ("VARIABLE", "Variable", "Variable input list length", "", 1)
}

class BF_DiskCacheWriterNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_DiskCacheWriterNode"
    bl_label = "Disk Cache Writer"
    bl_width_default = 180
    errorHandlingType = "EXCEPTION"

    nodeCache = {}
    filePath    : StringProperty(name = "File Path", subtype='FILE_PATH', default = "/tmp/an_cache.npy", update = AnimationNode.refresh)
    classType   : EnumProperty(name = "Input List Type", default = "VECTOR", items = classTypeItems, update = AnimationNode.refresh)
    lengthType  : EnumProperty(default = "CONSTANT", items = lengthTypeItems, update = AnimationNode.refresh)
    startFrame  : IntProperty(default = 1, update = AnimationNode.refresh)
    endFrame    : IntProperty(default = 100, update = AnimationNode.refresh)
    maxLength   : IntProperty(name = "Maximum list length", default = 100, update = AnimationNode.refresh)
    listLength  : IntProperty(default = 1, update = AnimationNode.refresh)
    executeFlag : BoolProperty(default = False, update = AnimationNode.refresh)

    def create(self):
        socketType = self.classType.title() + " List"
        self.newInput(socketType, "Data", "in")

    def draw(self, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "filePath", text="")
        subcol = col.column(align=True)
        subcol.scale_y = 1.5
        subrow = subcol.row(align=True)
        self.invokeFunction(subrow, "writeToDisk", description="Write to disk", text="Write", icon="DISK_DRIVE")
        self.invokeFunction(subrow, "deleteDiskCache", description="Delete from disk", text="Delete", icon="TRASH")

        col = layout.column(align=True)
        subcol = col.column(align=True)
        row = subcol.row(align=True)
        subcol.prop(self, "classType", text='')
        row = subcol.row(align=True)
        row.prop(self, "lengthType", expand=True)
        subcol.prop(self, "startFrame", text='Start Frame')
        subcol.prop(self, "endFrame", text='End Frame')
        if self.lengthType == "VARIABLE":
            subcol.prop(self, "maxLength", text='Max Input Length')

    def writeToDisk(self):
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        wm.progress_update(1)
        self.executeFlag = True

        try:
            filePath = self.filePath
            length = self.maxLength if self.lengthType == "VARIABLE" else self.listLength
            if self.listLength == 0:
                return
            n = self.endFrame - self.startFrame + 1
            info = {
                'n': n,
                'max_length': length,
                'start_frame': self.startFrame,
                'end_frame': self.endFrame,
                'class_type': self.classType
            }
            with sd.Writer(filePath, info) as f:
                count = 0
                for i in range(self.startFrame, self.endFrame + 1):
                    bpy.context.scene.frame_set(i)
                    data = self.nodeCache.get(self.identifier)
                    if data is None:return
                    f.add(data)
                    wm.progress_update(int((count/n) * 100))
                    count += 1
        except Exception as e:
            print("Disk writing Failed")
            print(str(e))

        self.executeFlag = False
        self.delete()
        wm.progress_end()

    def execute(self, data):
        if self.executeFlag:
            if self.startFrame >= self.endFrame:
                self.endFrame = self.startFrame + 1
            self.nodeCache[self.identifier] = data
            self.listLength = len(data)

    def deleteDiskCache(self):
        sd.delete(self.filePath)

    def delete(self):
        keys = list(self.nodeCache.keys())
        for key in keys:
            if key.startswith(self.identifier):
                self.nodeCache.pop(key, None)
