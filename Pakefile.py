# (import statement is unnecessary, it's only there to prevent errors in PyCharm)
from pake import PakeCommand, PakeRule

# Commands that are to be executed must be declared as PakeCommand objects
CC = PakeCommand('gcc')
ECHO = PakeCommand('echo')

# Variables can be declared using other variables and can be defined out-of-order
C_FLAGS = '-o $(EXE) $(C_SOURCES)'

C_SOURCES = "hello.c"
EXE = "hello"


# The PakeRule decorator gives information on the rule.
# Simplified, the system looks at the dependency and executes the PakeRule with the corresponding target.
# See Pakefile.execute_rule() for more specific conditions
#
# In this case, when running `./pake.py Pakefile.py run`, the `build` target will be executed first.
# Wildcards are not yet supported
@PakeRule(
    dependency="$(EXE)",
    default=True  # If the target is omitted when executing, this will be the target executed
)
def run():
    # `env.run(cmd, args)` is the preferred method of running shell commands:
    # it properly handle errors, but cannot evaluate variables inside the cmd/args
    # However, in this case, it would be better to write this as a variable in order to maintain consistency.
    # e.g.: RUN_HELLO = PakeCommand('./hello')
    env.run("./" + EXE)


@PakeRule(
    dependency="$(C_SOURCES)",
    target="$(EXE)"
)
def build():
    ECHO('$(CC) $(C_FLAGS)')
    CC('$(C_FLAGS)')
