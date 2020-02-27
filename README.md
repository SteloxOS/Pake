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
    * Like Make, variables can be defined using the values of other variables.
    ```python
    C_FLAGS = '-o $(EXE) $(C_SOURCES)'
    C_SOURCES = 'hello.c'
    EXE = 'hello'
    # They also can be declared out-of-order!
    # Variables are not evaluated until executed
    ```
* Variables that can be executed must be wrapped in a `PakeCommand` object
    ```python
    CC = PakeComand('gcc')
    ```
* Rules are methods denoted by a `@PakeRule` annotation.
    ```python
    @PakeRule()
    def build():
        QEMU_i386(QEMU_i386_ARGS)
        ...
    ```

To execute the `build` target, assuming that code is put into a file called `Pakefile.py`, run `./pake.py Pakefile.py build`

## Performance
Performance data for the sample script (`Pakefile.py`) can be seen visualized in `pycallgraph.png`.

This was gathered using [pycallgraph](https://pycallgraph.readthedocs.io/en/master/), using the command `pycallgraph graphviz -- ./pake.py Pakefile.py run`