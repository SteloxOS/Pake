QEMU_i386       = PakeCommand("qemu-system-i386")
QEMU_i386_ARGS  = "--version"

@PakeTarget(default = True)
def test_target(self):
    QEMU_i386(QEMU_i386_ARGS)

@PakeTarget()
def build(self):
    env.run("echo", ["Hello, world!"])