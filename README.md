# Pake
A modern take on GNU Make written using Python 3.8

Annoyed by the quirkiness of Make, the goal of Pake is to soften its rough edges: conditionals, variables, etc., and to make it more accessible by leveraging Python's feature set.

The tool is currently in an unusable alpha state--the basic structure is there (and a working example), but it is not yet ready for use.

## Using Pake
Simply drop the `pake.py` file into your project and:
- Windows: `python3 pake.py <Pakefile> [target] [ARGS...]`
- *nixes: `./pake.py <Pakefile> [target] [ARGS...]`

## Syntax
Pakefile currently uses annotations and types to differenciate between the various parts of a build script.

* Simple variables can be assigned as normal in Python.
    ```python
    QEMU_i386_ARGS = '--version'
    ```
* Variables that can be executed must be wrapped in a `PakeCommand` object
    ```python
    QEMU_i386 = PakeComand('qemu-system-i386')
    ```
* Targets are methods denoted by a `@PakefileTarget` annotation.
    ```python
    @PakefileTarget()
    def build(self):
        self.QEMU_i386(self.QEMU_i386_ARGS)
        ...
    ```

To execute the `build` target, assuming that code is put into a file called `Pakefile`, run `./pake.py Pakefile build`