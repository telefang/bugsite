A partial disassembly of Bugsite Alpha and Beta versions.

To build, the following ROMs of Network Adventure Bugsite Alpha and Beta
versions are required:

```
$ md5sum baseroms/baserom_alpha.gbc baseroms/baserom_beta.gbc
7f9dbafd6d16957e9687f89e33765f0b *baseroms/baserom_alpha.gbc
3c6b37b6162d599e3554689500b23af1 *baseroms/baserom_beta.gbc
```

A modern version of RGBDS (inc. rgbgfx) is required to compile this project.

# Python considerations

This project expects a Python 3 capable virtual environment at `env`. You must
create one and install the project dependencies with the following commands:

```
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

At the end of running these commands you will have a prepared Python
environment for your current system. You can deactivate the Python environment
with `deactivate` to return to your system Python (or open a new shell). The
project will automatically enter the Python environment when it needs to run
build scripts.

If you skip these steps, you *will* need to install global Python packages,
which is not recommended.

# Building

The project uses a makefile, so just run `make`.
