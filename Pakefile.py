CC = PakeCommand('gcc')
ECHO = PakeCommand('echo')

C_FLAGS = '-o $(EXE) $(C_SOURCES)'

C_SOURCES = "hello.c"
EXE = "hello"

@PakeTarget(
    dependencies = "$(EXE)",
    default = True
)
def run(self):
    env.run("./" + EXE)

@PakeTarget(
    dependencies = "$(C_SOURCES)",
    targets = "$(EXE)"
)
def build(self):
    ECHO('$(CC) $(C_FLAGS)')
    CC('$(C_FLAGS)')