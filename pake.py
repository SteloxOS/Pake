#!/usr/bin/python3

import sys, re, subprocess, os
from inspect import getmro
from types import FunctionType, MethodType, ModuleType
from importlib.machinery import SourceFileLoader

class PakeCommand():
    def __init__(self, command: str):
        self.command = command

class Pakefile:
    def __init__(self):
        pass

    def __setattr__(self, name, value):
        super(Pakefile, self).__setattr__(name, value)

    def __getattribute__(self, key):
        try:
            attribute = super(Pakefile, self).__getattribute__(key)

            if type(attribute) == PakeCommand:
                def execute(*args):
                    self.env.run(attribute.command, list(args))
                return execute

            return attribute
        except AttributeError as e:
            print("Getting: " + key)
            
            return self.env.get(self.__class__.__name__, key)

class PakeEnvironment():
    def __init__(self):
        self.__variables__ = dict()
        self.__targets__ = dict()
        self.__pakefiles__ = dict()

    def set(self, module: str, variable: str, value: object):
        try:
            self.__variables__[module][variable] = value
        except KeyError:
            self.__variables__[module] = dict()
            self.__variables__[module][variable] = value

    def get(self, module: str, variable: str) -> object:
        return self.__variables__[module][variable]

    def __get_targets__(self) -> dict:
        return self.__targets__

    def __get_module_targets__(self, module: str):
        try:
            if module in self.__targets__:
                return self.__targets__[module]
        except KeyError:
            return None

    def __has_target__(self, module: str, name: str) -> bool:
        try:
            if module in self.__targets__:
                if name in self.__targets__:
                    return True
        except KeyError:
            return False

    def __get_target__(self, module: str, name: str) -> object:
        if self.__has_target__(module, name):
            return self.__targets__[module][name]
        else:
            return None

    def __add_target__(self, module: str, name: str, target: object):
        if self.__get_module_targets__(module) is not None:
            self.__targets__[module][name] = target
        else:
            self.__targets__[module] = {name: target}

    def __load_pakefile__(self, path: str) -> Pakefile:
        path = os.path.abspath(path)

        # Need to generate a valid classname, requires some regex work
        classname = re.sub("[.:\\" + os.sep + "]", '_', path) #.replace(os.sep, '_') path.replace(os.sep, '_')
        
        # The classname will start with an '_' on Linux
        if classname.startswith('_'):
            classname = classname[1:]

        # Validate the classname
        if re.match(r'^[a-zA-Z]+(\w)*$', classname) is None:
            print("Error: Pakefile name '" + path + "' can only contain letters, numbers, and underscores and must start with a letter")
            return None

        # Generate the code
        pakefile_code = "from pake import PakeCommand, Pakefile, PakeTarget, PakeEnvironment\nclass " + classname + "(Pakefile):\n\t" + open(path).read().replace('\n', '\n\t')
        
        module = ModuleType(path)
        sys.modules[path] = module

        globals = module.__dict__
        globals['env'] = self
        
        # Execute the code!
        exec(pakefile_code, globals)

        # Find the class
        pakefile_class_name = None
        pakefile_class = None

        for attrib_name in dir(module):
            attrib = getattr(module, attrib_name)

            if type(attrib) == type:
                base_classes = getmro(getattr(module, attrib_name))

                if len(base_classes) >= 2:
                    if base_classes[1].__name__ == Pakefile.__name__:
                        pakefile_class_name = attrib_name
                        pakefile_class = attrib

        # Define the variables in the global dict
        for attrib_name in dir(pakefile_class):
            if not attrib_name.startswith('__'):
                attrib = getattr(pakefile_class, attrib_name)
                
                if type(attrib) != type and type(attrib) != FunctionType:
                    if type(attrib) != PakeCommand:
                        globals[attrib_name] = attrib
        
        # Re-execute the code with the new globals!
        exec(pakefile_code, globals)

        pakefile_class = getattr(module, pakefile_class_name)

        return pakefile_class()

    def __get_pakefile__(self, name: str) -> Pakefile:
        try:
            return self.__pakefiles__[name]
        except KeyError:
            return None

    def run(self, cmd: str, args: [str]):
        try:
            res = subprocess.run([cmd] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            print("Pakefile: command '" + cmd + "' not found!")
            return

        if res.stdout != '':
            sys.stdout.write(res.stdout.decode('utf-8'))
            sys.stdout.flush()
        
        if res.stderr != '':
            sys.stdout.write('\033[91m' + res.stderr.decode('utf-8') + '\033[0m')
            sys.stdout.flush()

class PakeDependency():
    def __init__(self):
        pass

class PakeTarget():
    def __init__(self, targets: [str] = None, dependencies: [str] = None, default: bool = False):
        self.targets = targets
        self.dependencies = dependencies
        self.default = default
        self.name = ""

    def __call__(self, function: MethodType):
        env = function.__globals__['env']
        
        if not env.__has_target__(function.__module__, function.__name__):
            env.__add_target__(function.__module__, function.__name__, self)

        return function

    def get_name(self):
        return self.name

    def get_targets(self):
        return self.targets

    def get_dependencies(self):
        return self.dependencies

    def is_default(self) -> bool:
        return self.default

'''
Convenience method for getting a value from an array or getting a default value
'''
def get_or_default(arr: [object], index: object, default: object) -> object:
    try:
        return arr[index]
    except IndexError:
        return default

def parse_arguments(argv: [str]):
    pass

def main(argv: [str]):
    if len(argv) < 2:
        # No Pakefile was passed!
        sys.exit("Usage: {} [Pakefile] <target> <...>".format(argv[0]))
    
    pakefile_name = argv[1]
    target_name = get_or_default(argv, 2, '')

    env = PakeEnvironment()

    pakefile = env.__load_pakefile__(argv[1])

    if pakefile is None:
        sys.exit("No Pakefile subclass found in {}!".format(pakefile_name))

    # Find the target to execute, either the provided one or the default one
    if target_name == '':
        target_dict = env.__get_module_targets__(pakefile.__module__)

        for name in target_dict.keys():
            if target_dict[name].is_default():
                getattr(pakefile, name)()
    else:
        getattr(pakefile, target_name)()

if __name__ == "__main__":
    main(sys.argv)