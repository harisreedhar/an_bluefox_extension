import bpy
from bpy.props import *
from animation_nodes . base_types import AnimationNode, VectorizedSocket

class BF_RigidBodyTriggerNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_RigidBodyTriggerNode"
    bl_label = "Rigidbody Trigger"
    bl_width_default = 160
    errorHandlingType = "EXCEPTION"
    codeEffects = [VectorizedSocket.CodeEffect]

    nodeDict = {}
    nodeIndex = 0

    for attr in ["Object", "Active", "Enabled", "Threshold","Mass","Bounciness","Friction","LinearDamping",
                 "AngularDamping","EnableCollisionMargin","CollisionMargin","Collections"]:
        exec("use{}List: VectorizedSocket.newProperty()".format(attr), globals(), locals())

    def create(self):
        self.newInput(VectorizedSocket("Object", "useObjectList",
            ("Object", "object", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Objects", "objects"), codeProperties = dict(allowListExtension = False)))
        toProp = lambda prop: [prop, "useObjectList"]

        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput(VectorizedSocket("Float", toProp("useThresholdList"),
            ("Threshold", "threshold", dict(value = 0.5)),
            ("Thresholds", "thresholds")))

        self.newInput(VectorizedSocket("Boolean", toProp("useActiveList"),
            ("Active", "active", dict(value = 1)),
            ("Actives", "actives")))
        self.newInput(VectorizedSocket("Boolean", toProp("useEnabledList"),
            ("Dynamic", "enable", dict(value = 1)),
            ("Dynamics", "enables")))
        self.newInput(VectorizedSocket("Text", toProp("useCollectionsList"),
            ("Collision Shape", "collisionShape", dict(defaultDrawType = "PROPERTY_ONLY", value = "CONVEX_HULL")),
            ("Collision Shapes", "collisionShape")))
        self.newInput(VectorizedSocket("Float", toProp("useMassList"),
            ("Mass", "mass", dict(value = 1)),
            ("Masses", "mass")))
        self.newInput(VectorizedSocket("Float", toProp("useBouncinessList"),
            ("Bounciness", "bounciness", dict(value = 0)),
            ("Bouncinesses", "bounciness")))
        self.newInput(VectorizedSocket("Float", toProp("useFrictionList"),
            ("Friction", "friction", dict(value = 0.5)),
            ("Frictions", "friction")))
        self.newInput(VectorizedSocket("Float", toProp("useLinearDampingList"),
            ("Linear Damping", "linear_damping", dict(value = 0.040)),
            ("Linear Dampings", "linear_damping")))
        self.newInput(VectorizedSocket("Float", toProp("useAngularDampingList"),
            ("Angular Damping", "angular_damping", dict(value = 0.1)),
            ("Angular Dampings", "angular_damping")))
        self.newInput(VectorizedSocket("Boolean", toProp("useEnableCollisionMarginList"),
            ("Enable Collision Margin", "enable_collision_margin", dict(value = False)),
            ("Enable Collision Margins", "enable_collision_margin")))
        self.newInput(VectorizedSocket("Float", toProp("useCollisionMarginList"),
            ("Collision Margin", "collision_margin", dict(value = 0.04)),
            ("Collision Margins", "collision_margin")))
        self.newInput(VectorizedSocket("Text", toProp("useCollectionsList"),
            ("Collection Indices", "collections", dict(defaultDrawType = "PROPERTY_ONLY", value = "0,1,2")),
            ("Collection Indices List", "collections")))

        self.newOutput(VectorizedSocket("Object", "useObjectList",
            ("Object", "object", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Objects", "objects"), codeProperties = dict(allowListExtension = False)))

        for socket in self.inputs[3:]:
            socket.useIsUsedProperty = True
            socket.isUsed = False
            socket.hide = True

    def drawAdvanced(self, layout):
        col = layout.column()
        self.invokeFunction(col, "invokeAddRigidBody",
                            text="Add",
                            description="Link objects to rigidbody world",
                            icon = "ADD")

        self.invokeFunction(col, "invokeRemoveRigidBody",
                            text="Remove",
                            description="Unlink objects from rigidbody world",
                            icon = "REMOVE")

    def invokeAddRigidBody(self):
        objects = self.getStoredObjects()
        addRigidBody(objects, True)

    def invokeRemoveRigidBody(self):
        objects = self.getStoredObjects()
        addRigidBody(objects, False)

    def getStoredObjects(self):
        keys = list(self.nodeDict.keys())
        objects = []
        for key in keys:
            if key.startswith(self.identifier):
                objects.append(self.nodeDict.get(key))
        return objects

    def storeObjectToDict(self, data):
        identifier = str(self.identifier) + str(self.nodeIndex)
        self.nodeDict[identifier] = data

    def getExecutionCode(self, required):
        yield "self.nodeIndex += 1"
        yield "self.storeObjectToDict(object)"
        yield "rigid_body = self.getRigidBodyObject(object)"
        yield "if rigid_body is not None:"
        yield "    influence = self.evaluateFalloff(falloff, object)"
        yield "    trigger = threshold >= influence"
        s = self.inputs[3:]
        if s[0].isUsed: yield "    rigid_body.kinematic = active"
        else: yield "    rigid_body.kinematic = trigger"
        if s[1].isUsed: yield "    rigid_body.enabled = enable"
        else: yield "    rigid_body.enabled = not trigger"
        if s[2].isUsed:
            yield "    collisionShape = collisionShape.upper()"
            yield "    if collisionShape in ['BOX','SPHERE','CAPSULE','CYLINDER','CONE','CONVEX_HULL','MESH']:"
            yield "        rigid_body.collision_shape = collisionShape"
        if s[3].isUsed: yield "    rigid_body.mass = mass"
        if s[4].isUsed: yield "    rigid_body.restitution = bounciness"
        if s[5].isUsed: yield "    rigid_body.friction = friction"
        if s[6].isUsed: yield "    rigid_body.linear_damping = linear_damping"
        if s[7].isUsed: yield "    rigid_body.angular_damping = angular_damping"
        if s[8].isUsed: yield "    rigid_body.use_margin = enable_collision_margin"
        if s[9].isUsed: yield "    rigid_body.collision_margin = collision_margin"
        if s[10].isUsed:
            yield "    collectionValues = [False] * 20"
            yield "    try:"
            yield "        for index in [int(i) for i in collections.split(',')]:"
            yield "            collectionValues[index] = True"
            yield "    except: pass"
            yield "    if not any(collectionValues): collectionValues[0] = True"
            yield "    rigid_body.collision_collections = collectionValues"

    def getRigidBodyObject(self, object):
        if object is None:
            return None
        if object.type != 'MESH':
            self.setErrorMessage('Object is not Mesh type')
        else:
            rigid_body = object.rigid_body
            if rigid_body is None:
                self.setErrorMessage('Object must contain rigidbody attribute')
                return None
            return rigid_body

    def evaluateFalloff(self, falloff, object):
        location = (0,0,0)
        location = object.location
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        influence = falloffEvaluator(location, self.nodeIndex)
        return influence

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")

    def delete(self):
        keys = list(self.nodeDict.keys())
        for key in keys:
            if key.startswith(self.identifier):
                self.nodeDict.pop(key)

def addRigidBody(objects, activate):
    try:
        scene = bpy.context.scene
        rigidBodyWorld = scene.rigidbody_world
        if rigidBodyWorld is None:
            bpy.ops.rigidbody.world_add()
            rigidBodyWorld = scene.rigidbody_world
        rigidBodyWorld.enabled = True

        if rigidBodyWorld.collection is None:
            newCollection = bpy.data.collections.new("RigidBodyWorld")
            newCollection.use_fake_user = True
            rigidBodyWorld.collection = newCollection

        rigidBodyWorldObjects = rigidBodyWorld.collection.objects

        for ob in objects:
            if ob is None:
                continue
            if ob.type == 'MESH':
                ob.data.update()
                if activate:
                    if ob.name not in rigidBodyWorldObjects:
                        rigidBodyWorldObjects.link(ob)
                else:
                    if ob.name in rigidBodyWorldObjects:
                        rigidBodyWorldObjects.unlink(ob)
    except:
       print('False')
