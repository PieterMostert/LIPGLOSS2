# Lipgloss2
Cross-platform Python app for creating glaze recipes.

This is an improved version of Lipgloss, which uses the CVXOPT linear-programming API instead of PuLP. The calculations run faster, and it is hopefully easier to install.

See README.pdf in README LaTeX files for more info. This needs to be updated to reflect the changes in the API, but the functionality is the same. A user guide can be found [here](https://wiki.glazy.org/t/using-lipgloss/238).

## Requirements: 

I *think* the following will be enough to get set up on a Windows machine:

* Install the latest version of [MiniConda3](https://docs.conda.io/en/latest/miniconda.html) (Currently Python 3.7).
* Open the Anaconda Prompt, and type `conda install -c conda-forge cvxopt` to install the pre-built [CVXOPT](https://cvxopt.org/install/index.html) API.
* Clone this repository using Git: `git clone https://github.com/PieterMostert/LIPGLOSS2.git`.
* Run the main.py script to open the GUI.
* If you encounter problems using Visual Code Studio, this [Stackoverflow answer](https://stackoverflow.com/a/62531033) may provide a solution.


If you manage to install Lipgloss2 on another operating system, please add instructions to this file.
