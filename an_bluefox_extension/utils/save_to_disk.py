# Reference: https://github.com/jutanke/memmappy
import json
import numpy as np
from os import remove
from time import sleep
from os.path import isfile
from animation_nodes . data_structures import (
    BooleanList,
    LongList,
    DoubleList,
    Vector3DList,
    ColorList,
    QuaternionList,
    Matrix4x4List
)

# Helper functions
type1List = ["BOOLEAN", "INTEGER", "FLOAT"]
type2List = ["VECTOR", "COLOR", "QUATERNION"]

def getLookup(classType, n):
    if classType in type1List:
        return np.ones((n, 2), 'int32') * -1
    elif classType in type2List:
        return np.ones((n, 2), 'int32') * -1
    elif classType == "MATRIX":
        return np.ones((n, 3), 'int32') * -1

def getDtype(classType):
    if classType in ["VECTOR", "MATRIX", "QUATERNION", "COLOR"]:
        return "float32"
    if classType == "BOOLEAN":
        return "bool"
    if classType == "INTEGER":
        return "int"
    if classType == "FLOAT":
        return "float64"

def getMaxShape(classType, maxLength):
    if classType in type1List:
        return (maxLength,)
    elif classType == "VECTOR":
        return (maxLength, 3)
    elif classType in ["QUATERNION", "COLOR"]:
        return (maxLength, 4)
    elif classType == "MATRIX":
        return (maxLength, 4, 4)

def delete(fileName):
    assert isfile(fileName)
    name = fileName[0:-4] if fileName.endswith('.npy') else fileName
    lookupFile = name + '_lookup.npy'
    assert isfile(lookupFile)
    metaFile = name + '_meta.json'
    assert isfile(metaFile)
    remove(fileName)
    remove(metaFile)
    remove(lookupFile)
    sleep(0.01)

def dataToArray(data, classType):
    dType = getDtype(classType)
    if classType == "BOOLEAN":
        return np.frombuffer(data.asNumpyArray(), dtype=dType)
    elif classType == "INTEGER":
        return data.asNumpyArray().astype(dType)
    elif classType == "FLOAT":
        return data.asNumpyArray().astype(dType)
    elif classType == "VECTOR":
        return data.asNumpyArray().reshape(-1,3).astype(dType)
    elif classType == "COLOR":
        return data.asNumpyArray().reshape(-1,4).astype(dType)
    elif classType == "QUATERNION":
        return data.asNumpyArray().reshape(-1,4).astype(dType)
    elif classType == "MATRIX":
        return data.asNumpyArray().reshape(-1,4,4).astype(dType)

def arrayToData(array, classType):
    dType = getDtype(classType)
    if classType == "BOOLEAN":
        return BooleanList.fromNumpyArray(array.astype(dType))
    elif classType == "INTEGER":
        return LongList.fromNumpyArray(array.astype(dType))
    elif classType == "FLOAT":
        return DoubleList.fromNumpyArray(array.astype(dType))
    elif classType == "VECTOR":
        return Vector3DList.fromNumpyArray(array.ravel().astype(dType))
    elif classType == "COLOR":
        return ColorList.fromNumpyArray(array.ravel().astype(dType))
    elif classType == "QUATERNION":
        return QuaternionList.fromNumpyArray(array.ravel().astype(dType))
    elif classType == "MATRIX":
        return Matrix4x4List.fromNumpyArray(array.ravel().astype(dType))

# Write to Disk

class Writer:
    def __init__(self, fileName, info={}):
        n = info.get('n')
        assert n > 0

        name = fileName[0:-4] if fileName.endswith('.npy') else fileName
        lookupFile = name + '_lookup.npy'
        metaFile = name + '_meta.json'

        classType = info.get('class_type')
        dtype = getDtype(classType)
        maxShape = getMaxShape(classType, info.get('max_length'))
        shape = (n, *maxShape)
        meta = {
            "max_shape": maxShape,
            "n": n,
            "dtype": dtype,
            "class_type": classType,
            "start_frame": info.get('start_frame'),
            "end_frame": info.get('end_frame')
        }
        with open(metaFile, 'w+') as f:
            metaDmp = json.dumps(meta)
            f.write(metaDmp)

        currentPointer = 0
        X = np.memmap(fileName, shape=shape, dtype=dtype, mode='w+')

        self.currentPointer = currentPointer
        self.lookup = getLookup(classType, n)
        self.metaFile = metaFile
        self.lookupFile = lookupFile
        self.X = X
        self.maxShape = maxShape
        self.n = n
        self.classType = classType

    def add(self, data):
        if self.currentPointer < 0:
            raise BufferError("out of bounds")
        assert self.currentPointer < self.n

        data = dataToArray(data, self.classType)
        self.insert(self.currentPointer, data)
        curp = self.currentPointer + 1
        self.currentPointer = curp if curp < self.n else -1

    def insert(self, i, data):
        assert i < self.n
        assert self.lookup[i, 0] == -1 and self.lookup[i, 1] == -1
        assert len(data.shape) == len(self.maxShape)
        for a, b in zip(data.shape, self.maxShape):
            assert a <= b

        if self.classType in type1List:
            h, = data.shape
            self.X[i, 0:h] = data
            self.lookup[i, 0] = h
        elif self.classType in type2List:
            h, w = data.shape
            self.X[i, 0:h, 0:w] = data
            self.lookup[i, 0] = h
            self.lookup[i, 1] = w
        elif self.classType == "MATRIX":
            h, w, c = data.shape
            self.X[i, 0:h, 0:w, 0:c] = data
            self.lookup[i, 0] = h
            self.lookup[i, 1] = w
            self.lookup[i, 2] = c

    def flush(self):
        if self.X is not None:
            del self.X
        try:
            remove(self.lookupFile)
            sleep(0.01)
        except:
            pass
        np.save(self.lookupFile, self.lookup)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()

# Read from Disk

class Reader:
    def __init__(self, fileName, classType="VECTOR"):
        assert isfile(fileName)
        name = fileName[0:-4] if fileName.endswith('.npy') else fileName
        lookupFile = name + '_lookup.npy'
        assert isfile(lookupFile)
        metaFile = name + '_meta.json'
        assert isfile(metaFile)
        lookup = np.load(lookupFile)

        with open(metaFile, 'r') as f:
            meta = json.loads(''.join(f.readlines()))

        n = meta['n']
        maxShape = meta['max_shape']
        dtype = meta['dtype']

        shape = (n, *maxShape)
        X = np.memmap(fileName, shape=shape, dtype=dtype, mode='r')
        self.X = X
        self.lookup = lookup
        self.classType = meta['class_type']
        self.startFrame = meta['start_frame']
        self.endFrame = meta['end_frame']
        self.n = n

    def __getitem__(self, item):
        if isinstance(item, int):
            if self.classType in type1List:
                h, w = self.lookup[item]
                array = self.X[item, 0:h]
                return arrayToData(array, self.classType)
            elif self.classType in type2List:
                h, w = self.lookup[item]
                array = self.X[item, 0:h, 0:w]
                return arrayToData(array, self.classType)
            elif self.classType == "MATRIX":
                h, w, c = self.lookup[item]
                array = self.X[item, 0:h, 0:w, 0:c]
                return arrayToData(array, self.classType)
        else:
            raise ValueError("Cannot get ", item)
