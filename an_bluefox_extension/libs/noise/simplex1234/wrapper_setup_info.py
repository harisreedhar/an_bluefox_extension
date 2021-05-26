import os
import subprocess

directory = os.path.dirname(__file__)
sourceDir = os.path.join(directory, "source")

def getCompileLibraryTasks(utils):
    return [compile_Test]

def compile_Test(utils):
    print("Compile Test\n")

    sourceFiles = list(utils.iterPathsWithExtension(sourceDir, [".c",".cpp", ".h"]))
    targetName, command, _ = getCompileInfo(utils)
    targetFile = os.path.join(sourceDir, targetName)

    if utils.dependenciesChanged(targetFile, sourceFiles):
        subprocess.run(command, cwd = sourceDir)
    else:
        print("Nothing changed. Skipping.")

def getExtensionArgs(utils):
    args = getCompileInfo(utils)[2]
    args["library_dirs"] = [sourceDir]
    return args

def getCompileInfo(utils):
    if utils.onWindows:
        return ("Simplex1234_windows.lib",
                [os.path.join(sourceDir, "compile_windows.bat")],
                {"libraries" : ["Simplex1234_windows"],
                 "extra_link_args" : ["/NODEFAULTLIB:LIBCMT"]})
    if utils.onLinux:
        return ("libSimplex1234_linux.a",
                ["sh", os.path.join(sourceDir, "compile_linux.sh")],
                {"libraries" : ["Simplex1234_linux"]})
    if utils.onMacOS:
        return ("libSimplex1234_macos.a",
                ["sh", os.path.join(sourceDir, "compile_macos.sh")],
                {"libraries" : ["Simplex1234_macos"]})
    raise Exception("unknown platform")
