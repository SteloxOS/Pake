#!/usr/bin/python3

import inspect, os, re, shlex, subprocess, sys, importlib
from types import ModuleType, FunctionType
from inspect import getmro

def PakeCommand(command: str) -> FunctionType:
    module = inspect.currentframe().f_back

    module_name = module.f_globals['__name__']
    module_env = module.f_globals['env']

    pakefile = module_env.get_pakefile(module_name)

    parsed_command = pakefile.eval(command)

    def __pakecommand_execute__(args):
        module_env.run(parsed_command, pakefile.eval(args))

    __pakecommand_execute__.__pakecommand_command__ = parsed_command

    return __pakecommand_execute__

class PakeRule():
    """ A decorator for Pakefile rules. """
    
    def __init__(self, default: bool = False, target: str = None, dependency: str = None):
        self.name = None

        self.default = default
        self.target = target
        self.dependency = dependency

    def __call__(self, function):
        self.name = function.__name__

        env = function.__globals__.get('env')
        env.get_pakefile(function.__module__).__add_rule__(self.name, self, function)

        return None

    def get_name(self) -> str:
        """ Returns the name of this rule, always equal to the name of the function decorated """
        return self.name

    def is_default(self) -> bool:
        """ Returns True if this is the default rule of the Pakefile """
        return self.default

    def get_target(self) -> str:
        return self.target

    def get_dependency(self) -> str:
        return self.dependency

class Pakefile():
    """
    An object representing a loaded Pakefile. 
    Contains information on the script's variables and rules
    """

    def __init__(self):
        self.__rules__ = dict()
        self.__pakefile_class__ = None

    def eval(self, string: str) -> str:
        """ Evaluates the given string containing variables """

        parsed = string
        match = re.search(r'(\$\([\w]+\))', parsed)

        while match is not None:
            group = match.group(1)
            variable = group[2:-1]

            attr = getattr(self.__pakefile_class__, variable)
            str_attr = None

            # Account for PakeCommands!
            if type(attr) is FunctionType:
                pakecommand = getattr(attr, '__pakecommand_command__')
                str_attr = pakecommand
            
            if str_attr is None:
                str_attr = str(attr)

            parsed = parsed.replace(group, str_attr)

            match = re.search(r'(\$\([\w]+\))', parsed)

        return parsed

    def get_rules(self) -> dict:
        """
        Returns a dict of rule names and its respective rule.
        The name of the rule is simply the name of the method decorated
        """
        
        return self.__rules__
        
    def get_rule(self, name: str) -> tuple:
        return self.__rules__.get(name, None)

    def __add_rule__(self, name: str, rule: PakeRule, func):
        self.__rules__[name] = (rule, func)

    def execute_rule(self, rule_name: str):
        """ Executes the provided rule after searching and building dependencies """

        # .get_rule(str) returns a tuple: (PakeRule, function)
        rule = self.get_rule(rule_name)

        if rule is None:
            print("*** No rule '" + rule_name + "' in '" + self.__pakefile_class__.__module__ + "'. Stop ***")
            sys.exit()
            return

        dependency = rule[0].get_dependency()

        if dependency is None:
            # No dependency. Just build!
            rule[1]()
            return

        dependency = self.eval(dependency)
        target = rule[0].get_target()

        # Criteria for building dependency:
        # - if there is no target
        # - if the target doesn't exist
        # - if it doesn't exist
        # - if it was more recently changed than the target

        if target is not None:
            if os.path.exists(target):
                if os.path.exists(dependency):
                    if os.path.getmtime(target) >= os.path.getmtime(dependency):
                        print("*** Nothing to do for '{}' in '{}'. ***".format(dependency, self.__pakefile_class__.__module__))
                        return

        # Otherwise, find the dependency!
        found_dependency_rule_name = None

        for dependency_rule_name in self.get_rules():
            found_rule = self.get_rule(dependency_rule_name)[0]

            if found_rule.get_target() is not None:
                if self.eval(found_rule.get_target()) == dependency:
                    # We found our rule!
                    found_dependency_rule_name = dependency_rule_name

        if found_dependency_rule_name is None:
            if not os.path.exists(dependency):
                print("*** No rule found to build '{}' in '{}'. Stop ***".format(dependency, self.__pakefile_class__.__module__))
                sys.exit()
        else:
            self.execute_rule(found_dependency_rule_name)

        rule[1]()

    def __set_pakefile_class__(self, pakefile_class: type):
        self.__pakefile_class__ = pakefile_class

    def get_pakefile_class(self) -> type:
        return self.__pakefile_class__

class PakeEnvironment():
    """ An object containing state information of all loaded Pakefiles """

    def __init__(self):
        self.__pakefiles__ = dict()

    def get_pakefile(self, path: str) -> Pakefile:
        """ Returns the Pakefile object of the provided file """
        return self.__pakefiles__[os.path.abspath(path)]

    def __load_pakefile__(self, path: str) -> Pakefile:
        """ Loads a Pakefile from the given path """

        path = os.path.abspath(path)

        if not os.path.isfile(path):
            print("*** Could not find '{}'. Stop ***".format(path))
            return

        # We inject our own class declaration, so we need to generate our own valid, unique class name
        # This replaces any periods, colons, or path separators with underscores
        pakefile_class_name = re.sub("[.:\\" + os.sep + "]", '_', path)

        # The class name will always start with an underscore on Linux
        if pakefile_class_name.startswith('_'):
            pakefile_class_name = pakefile_class_name[1:]

        # Validate the class name
        if re.match(r'^[a-zA-Z]+(\w)*$', pakefile_class_name) is None:
            print("*** Could not generate a valid class name for '{}'. Stop ***".format(path))
            return None
        
        # Load and modify the file!
        pakefile_code = open(path).read()#.replace('\n', '\n\t')
        pakefile_code = "from pake import Pakefile, PakeCommand, PakeRule\n" + pakefile_code
        #pakefile_code = "from pake import Pakefile, PakeCommand, PakeRule\nclass " + pakefile_class_name + "():\n\t" + pakefile_code

        #pakefile_module = importlib.import_module(path)
        #print(pakefile_module)
        #sys.exit()

        pakefile_module = ModuleType(path)
        sys.modules[path] = pakefile_module

        globals = pakefile_module.__dict__
        globals['env'] = self

        pakefile = Pakefile()
        self.__pakefiles__[path] = pakefile

        # Execute the code!
        exec(pakefile_code, globals)

        pakefile_class = pakefile_module#getattr(pakefile_module, pakefile_class_name)
        pakefile.__set_pakefile_class__(pakefile_class)

        return pakefile

    def run(self, cmd: str, args: str = ""):
        try:
            res = subprocess.run([cmd] + shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            print("Pakefile: command '" + cmd + "' not found!")
            return

        if res.stdout != '':
            sys.stdout.write(res.stdout.decode('utf-8'))
            sys.stdout.flush()
        
        if res.stderr != '':
            sys.stdout.write('\033[91m' + res.stderr.decode('utf-8') + '\033[0m')
            sys.stdout.flush()

def main(argv):
    if len(argv) < 2:
        print("Usage: {} [Pakefile] <target> <ARGS...>".format(argv[0]))
        return

    env = PakeEnvironment()
    pakefile = env.__load_pakefile__(argv[1])

    rule_name = None

    if len(argv) >= 3:
        rule_name = argv[2]
    else:
        # Find default rule!
        for rule_tuple in pakefile.get_rules().values():
            rule = rule_tuple[0]

            if rule.is_default():
                rule_name = rule.get_name()

        if rule_name == None:
            print("*** No default rule found. Stop ***")
            return

    pakefile.execute_rule(rule_name)

if __name__ == "__main__":
    main(sys.argv)