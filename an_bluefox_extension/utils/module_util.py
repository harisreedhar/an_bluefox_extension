import bpy
import glob
import importlib
import logging
import os
import subprocess
import sys

def isAvailable(module):
    return (module in locals() and
            type(locals()[module]) is importlib.types.ModuleType)

def isInstalled(module):
    try:
        importlib.import_module(module)
        return True
    except ImportError:
        return False

def installModule(module: str, options: str = None):
    executable = None
    try:
        for path in glob.glob('{}/bin/python*'.format(sys.exec_prefix)):
            if os.access(path, os.X_OK) and not path.lower().endswith('dll'):
                executable = path
                logging.debug(
                    'Blender\'s Python interpreter: {}'.format(executable))
                break
    except Exception as e:
        logging.error(e)
    if executable is None:
        logging.error('Unable to locate Blender\'s Python interpreter')

    if isInstalled('ensurepip'):
        subprocess.call([executable, '-m', 'ensurepip'])
    elif not isInstalled('pip'):
        url = 'https://bootstrap.pypa.io/get-pip.py'
        filepath = '{}/get-pip.py'.format(os.getcwd())
        try:
            requests = importlib.import_module('requests')
            response = requests.get(url)
            with open(filepath, 'w') as f:
                f.write(response.text)
            subprocess.call([executable, filepath])
        except Exception as e:
            logging.error(e)
        finally:
            if os.path.isfile(filepath):
                os.remove(filepath)

    if not isInstalled(module) and executable is not None:
        try:
            if options is None or options.strip() == '':
                subprocess.call([executable, '-m', 'pip', 'install', module])
            else:
                subprocess.call([executable, '-m', 'pip', 'install', options, module])
        except Exception as e:
            logging.error(e)

    return isInstalled(module)
