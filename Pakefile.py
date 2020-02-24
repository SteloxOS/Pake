# Commands that are to be executed must be declared as PakeCommand objects
CC = PakeCommand('gcc')
ECHO = PakeCommand('echo')

# Variables can be declared using other variables and can be defined out-of-order
C_FLAGS = '-o $(EXE) $(C_SOURCES)'

C_SOURCES = "hello.c"
EXE = "hello"

# The PakeTarget decorator gives information on the target (duh).
# The system looks at the dependencies and executes the PakeTarget with the corresponding target.
# In this case, when running `./pake.py Pakefile.py run`, the `build` target will be executed first.
# Wildcards are not yet supported
@PakeTarget(
    dependencies = "$(EXE)",
    default = True # If the target is omitted when executing, this will be the target executed
)
def run(self):
    # `env.run(cmd, args)` is the preferred method of running shell commands:
    # it can evaluate vars passed as arguments and properly handle errors.
    # However, in this case, it would be better to write this as a variable in order to maintain consistency.
    # e.g.: RUN_HELLO = PakeCommand('./hello')
    env.run("./" + EXE)

@PakeTarget(
    dependencies = "$(C_SOURCES)",
    targets = "$(EXE)"
)
def build(self):
    ECHO('$(CC) $(C_FLAGS)')
    CC('$(C_FLAGS)')
