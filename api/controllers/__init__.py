import importlib
import os


_PYTHON_EXTENSION = ".py"

controllers = []

for file_name in os.listdir(os.path.dirname(os.path.realpath(__file__))):
    if file_name.startswith("_"):
        continue

    controller_name = "." + file_name.rstrip(_PYTHON_EXTENSION)
    controller = importlib.import_module(controller_name, package="api.controllers")
    controllers.append(controller)

__all__ = [controllers]
