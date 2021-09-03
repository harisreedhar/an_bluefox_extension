import bpy
from bpy.props import *
from ... utils import save_to_disk as sd
from animation_nodes . base_types import AnimationNode
from animation_nodes . data_structures import (
    BooleanList,
    LongList,
    DoubleList,
    Vector3DList,
    ColorList,
    QuaternionList,
    Matrix4x4List
)

classTypeItems = {
    ("BOOLEAN", "Boolean", "Cache Boolean list", "", 0),
    ("INTEGER", "Integer", "Cache Integer list", "", 1),
    ("FLOAT", "Float", "Cache Float list", "", 2),
    ("VECTOR", "Vector", "Cache 3D Vector list", "", 3),
    ("COLOR", "Color", "Cache Color list", "", 4),
    ("QUATERNION", "Quaternion", "Cache Quaternion list", "", 5),
    ("MATRIX", "Matrix", "Cache 4x4 Matrix list", "", 6)
}

lengthTypeItems = {
    ("CONSTANT", "Constant", "Constant input list length", "", 0),
    ("VARIABLE", "Variable", "Variable input list length", "", 1)
}

class BF_DiskCacheNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_DiskCacheNode"
    bl_label = "Disk Cache"
    bl_width_default = 180
    errorHandlingType = "EXCEPTION"

    nodeCache = {}
    reader = None
    listLength  : IntProperty(default = 1, update = AnimationNode.refresh)
    startFrame  : IntProperty(default = 1, update = AnimationNode.refresh)
    endFrame    : IntProperty(default = 100, update = AnimationNode.refresh)
    classType   : EnumProperty(name = "Input List Type", default = "VECTOR", items = classTypeItems, update = AnimationNode.refresh)
    filePath    : StringProperty(name = "File Path", subtype='FILE_PATH', default = "/tmp/an_cache.npy", update = AnimationNode.refresh)
    lengthType  : EnumProperty(default = "CONSTANT", items = lengthTypeItems, update = AnimationNode.refresh)
    maxLength   : IntProperty(name = "Maximum list length", default = 100, update = AnimationNode.refresh)

    def create(self):
        socketType = self.classType.title() + " List"
        self.newInput(socketType, "Data", "in")
        self.newInput("Integer", "Offset", "offset")
        self.newInput("Boolean", "Loop", "loop", value=False)
        self.newOutput(socketType, "Data", "out")
        self.newOutput("Generic", "Reader", "reader", hide=True)

    def draw(self, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "filePath", text="")
        self.invokeFunction(row, "reloadFile", description="Reload", text="", icon="FILE_REFRESH")
        subcol = col.column(align=True)
        subcol.scale_y = 1.5
        subrow = subcol.row(align=True)
        self.invokeFunction(subrow, "writeToDisk", description="Save to disk", text="Save", icon="DISK_DRIVE")
        self.invokeFunction(subrow, "deleteDiskCache", description="Delete from disk", text="Delete", icon="TRASH")

        col = layout.column(align=True)
        row = col.row(align=True)
        col.prop(self, "classType", text='')
        row = col.row(align=True)
        row.prop(self, "lengthType", expand=True)
        col.prop(self, "startFrame", text='Start Frame')
        col.prop(self, "endFrame", text='End Frame')
        if self.lengthType == "VARIABLE":
            col.prop(self, "maxLength", text='Max Input Length')

    def writeToDisk(self):
        filePath = self.filePath
        self.reader = None
        length = self.maxLength if self.lengthType == "VARIABLE" else self.listLength
        n = self.getAmount()
        with sd.Writer(filePath, n, length, classType=self.classType) as f:
            for i in range(self.startFrame, self.endFrame+1):
                bpy.context.scene.frame_set(i)
                data = self.nodeCache.get(self.getCacheKey())
                if data is None:return
                f.add(data)

    def execute(self, data, offset, loop):
        if self.startFrame >= self.endFrame:
            self.endFrame = self.startFrame + 1

        self.nodeCache[self.getCacheKey()] = data
        self.listLength = len(data)

        try:
            if self.reader is None:
                self.reader = sd.Reader(self.filePath, classType=self.classType)
            index = self.getIndex(offset, loop=loop)
            return self.reader[index], self.reader
        except Exception as e:
            self.raiseErrorMessage("ERROR:" + str(e))
            return self.getDefaultOutput(), self.reader

    def deleteDiskCache(self):
        sd.delete(self.filePath)

    def reloadFile(self):
        self.reader = sd.Reader(self.filePath, classType=self.classType)

    def getIndex(self, offset, loop=False):
        current = bpy.context.scene.frame_current
        index = int((current - self.startFrame + offset) % self.getAmount())
        if not loop:
            if current < self.startFrame:
                index = 0
            if current > self.endFrame:
                index = -1
        return index

    def getAmount(self):
        return self.endFrame - self.startFrame + 1

    def getCacheKey(self):
        return self.identifier

    def getDefaultOutput(self):
        if self.classType == "BOOLEAN":
            return BooleanList()
        elif self.classType == "INTEGER":
            return LongList()
        elif self.classType == "FLOAT":
            return DoubleList()
        elif self.classType == "VECTOR":
            return Vector3DList()
        elif self.classType == "COLOR":
            return ColorList()
        elif self.classType == "VECTOR":
            return QuaternionList()
        elif self.classType == "MATRIX":
            return Matrix4x4List()
