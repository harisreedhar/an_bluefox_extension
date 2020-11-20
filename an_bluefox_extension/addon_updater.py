import os
import sys
import shutil
import zipfile
import requests
import platform
import tempfile
import urllib.request

def downloadFile(url):
    try:
        r = requests.get(url, stream=True)
        fd = tempfile.TemporaryFile()
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)
        return fd
    except:
        print("Error downloading file")
        return False

def extractFile(source, destination):
    try:
        with zipfile.ZipFile(source,"r") as zip_ref:
            zip_ref.extractall(destination)
        return True
    except:
        print("Error extracting file")
        return False

def removeFile(filePath):
    try:
        os.remove(filePath)
        return True
    except:
        print("Failed removing file")
        return False

def removeDirectory(directory):
    try:
        shutil.rmtree(directory)
        return True
    except:
        print("Failed removing Directory")
        return False

def update():
    os_platform = platform.system()
    scriptPath = os.path.normpath(os.path.dirname(__file__))
    addonsPath = os.path.dirname(scriptPath)
    if os_platform == "Windows":
        url = "https://github.com/harisreedhar/an_bluefox_extension/releases/download/master-cd-build/an_bluefox_extension_v1_0_windows_py37.zip"
    elif os_platform == "Linux":
        if sys.version_info < (3, 8):
            url = "https://github.com/harisreedhar/an_bluefox_extension/releases/download/master-cd-build/an_bluefox_extension_v1_0_linux_py37.zip"
        else:
            url = "https://github.com/harisreedhar/an_bluefox_extension/releases/download/master-cd-build/an_bluefox_extension_v1_0_linux_py38.zip"
    elif os_platform == "Darwin":
        url = "https://github.com/harisreedhar/an_bluefox_extension/releases/download/master-cd-build/an_bluefox_extension_v1_0_macOS_py37.zip"
    else:
        return False

    filePath = downloadFile(url)
    if filePath:
        removedDirectory = removeDirectory(scriptPath)
        if removedDirectory:
            extracted = extractFile(filePath, addonsPath)
            if extracted:
                print("Updated to latest version")
                return True
    else:
        print("Updation failed")
        return False
