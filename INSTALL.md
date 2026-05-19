# Instructions

**Required software:**
make
gcc
git
python3
python3-devel
rgbds

This project currently uses [RGBDS v0.9.1](https://github.com/gbdev/rgbds/releases/tag/v0.9.1). 

If you're on Windows, please use the WSL Terminal. It can be installed following the instructions described [**here**](https://learn.microsoft.com/en-us/windows/wsl/install).

The following ROMs are needed to build this project:
```
$ md5sum baseroms/baserom_alpha.gbc baseroms/baserom_beta.gbc
7f9dbafd6d16957e9687f89e33765f0b *baseroms/baserom_alpha.gbc
3c6b37b6162d599e3554689500b23af1 *baseroms/baserom_beta.gbc
```

The ROMs need to be named exactly as shown above above (**baserom_alpha.gbc** and **baserom_beta.gbc**) and placed into a directory named baseroms in the project's root directory. If the directory does not exist, create it.

# Step-by-Step Guide

1) Install all required software using your distro's package manager.
* **Note on RGBDS:** If RGBDS is missing or outdated, you will need to download and install it or build it from source, following the instructions [**here**](https://rgbds.gbdev.io/install).

2) Clone the repository to your preferred directory using the following command: 
`git clone https://github.com/telefang/bugsite`

3) Navigate into the directory you cloned this repository to using the following command:
`cd bugsite`.
* The **translation project** is on a specific branch. If you're interested in building it specifically, switch into the branch using the following command:
`git checkout patch`

4) Set up a Python 3 environment, then install the require software using the following commands:

```
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

5) Run `make`
