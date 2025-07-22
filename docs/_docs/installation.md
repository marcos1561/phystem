---
---

# Linux

## Creating a virtual environment
If you prefer, create a virtual environment, although this step is not mandatory. In addition to isolating the development environment (great for avoiding dependency issues between multiple projects), creating a virtual environment allows the user to install packages without problems, which can occur when you are not an administrator.

To create a virtual environment at the path `<venv path>`, execute:

```bash
python3 -m venv <venv path>
```

After creation, you need to activate the environment:

```bash
source <venv path>/bin/activate
```

To deactivate the environment, simply execute:

```bash
deactivate
```

> ℹ️
>
> For more information about virtual environments, <a href="https://packaging.python.org/en/latest/tutorials/installing-packages/#creating-virtual-environments" target="_blank">click here</a>.

## Method 1: From Git
The easiest way to install phystem is through Git, which only requires the following command:

```bash
pip install -e "git+https://github.com/marcos1561/phystem.git/#egg=phystem"
```

After its execution, it will be possible to run `import phystem` anywhere. The phystem files are installed in:

- `<venv path>/src/`: When using a virtual environment.
- `<current dir>/src/`: When using a global installation.

If desired, you can configure the installation location using the `--src` flag.

The `-e` flag makes the installation editable, so changes to the phystem files are applied automatically. Otherwise, you will need to reinstall after each modification.

## Method 2: Cloning the repository
First, clone the repository:

```bash
git clone https://github.com/marcos1561/phystem.git
```

Then, install it using `pip`:

```bash
pip install -e phystem
```

## Testing the installation
To test the installation, open a Python REPL and execute:

```python
>>> import phystem.test_install
```

A window should open containing an animation of the system implemented in the tutorial [How to use phystem?]({{ 'docs/tutorial_step_by_step.html' | relative_url }}).

## Compiling the C++ module
{: #installation_compilation}
To explore systems that use the module written in C++, it is necessary to compile this code.
To do so, simply execute the `build.sh` script located in the folder `/src/phystem/cpp/pybind`.
The compilation may take a while.

```bash
source <path to build.sh>/build.sh
```