from bpy.props import *
from animation_nodes . base_types import AnimationNode

updateTypeItems = [("REALTIME", "Real Time", "", "NONE", 0),
                   ("CACHED", "Cached", "", "NONE", 1)]

class cacheBase:
    instanceIndex = 0
    nodeCache = {}
    cacheIdentifier = None

    def incrementInstanceIndex(self):
        self.instanceIndex += 1

    def setCacheIdentifier(self, identifier):
        self.cacheIdentifier = identifier

    def getCacheIdentifier(self):
        return self.cacheIdentifier + str(self.instanceIndex)

    def getCacheValue(self):
        value = self.nodeCache.get(self.getCacheIdentifier())
        return value

    def setCacheValue(self, value):
        self.nodeCache[self.getCacheIdentifier()] = value

    def setCacheToNone(self, identifier):
        for key in self.nodeCache.keys():
            if key.startswith(identifier):
                self.nodeCache[key] = None
        self.refresh()

class cacheHelper(cacheBase):
    updateType: EnumProperty(items = updateTypeItems, default = "REALTIME",
                             update = AnimationNode.refresh)

    def drawCacheItems(self, layout, functionName):
        col = layout.column()
        col.scale_y = 1.5
        if self.updateType == "CACHED":
            self.invokeFunction(col, functionName,
                                text="Update",
                                description="Update cache",
                                icon="FILE_REFRESH")
        col = layout.column(align = True)
        row = col.row(align = True)
        row.prop(self, "updateType", expand = True)
        return row, col

def prepareCache(function):
    def wrapper(*args):
        instance = args[0]
        instance.setCacheIdentifier(instance.identifier)
        result = function(*args)
        instance.incrementInstanceIndex()
        return result
    return wrapper
