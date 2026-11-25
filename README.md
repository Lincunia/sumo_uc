# SUMO - Universidad Central


## Source code installation

1. You have to SUMO and JuPedSim by checking 
[the instructions](https://sumo.dlr.de/docs/Installing/)
depending on the system being used, install the dependencies described on the
section named "Installing required tools and libraries".

<details>
<summary>Notes for the people who want to install by compiling</summary>

I (Altamoid) use Arch Linux and the AUR package manager was tricky during the
installation, so I decided to compile SUMO and JuPedSim. After trying to
install them several times. I decided to create a guide for the ones who are
interested to do the same thing as me.

### Dependencies
* C compiler
* Cmake
* Xerces-C
* Proj
* GDAL library
* Swig
* Maven
* Rust
* GEOS

### JuPedSim Installation from source code
```
git clone https://github.com/PedestrianDynamics/jupedsim
cd jupedsim
git submodule update --init
cmake -B build .
sudo cmake --build build
```

After installing JuPedSim, we're able to install SUMO propperly.

### SUMO Installation from source code
```
git clone https://github.com/eclipse-sumo/sumo
cmake -B build
cmake --build build -j $(nproc)
sudo cmake --install build
```
Append the `export SUMO_HOME=/usr/local/share/sumo` line to the `.bashrc` or
`.profile` file.

Maybe doing this wasn't necesary since this was made by reading a the
installation guide from the SUMO developpers, but I put it there to make the
process as literally described.

> I just got comfortable using Arch Linux I didn't get any issue
</details>


3. Check the installation by running `sumo`, `sumo-gui` and check that
`SUMO_HOME` variable is appended to the `PATH`. If no error reported, then
`sumo_uc` can run.

4. Clone this repository by running:
`git clone https://v15.next.forgejo.org/Altamoid/sumo_uc.git`

5. Translate the `locale` files by going [here](#handling-language-modifications)

6. For POSIX systems, you can run: `make run` to install the dependencies on
the a virtual environment and run the program on it.

7. For Windows, you can run `run.bat` to do the same methodology as in the fifth
step.

### Handling language modifications

This process is based on
[this website](https://lokalise.com/blog/translating-apps-with-gettext-comprehensive-tutorial/#getting-started-with-gettext).

---

For this we use these commands:
 * xgettext
 * msginit
 * msgfmt


For UNIX-like users, to get the language modules for Linux/MacOS users, run
this (assuming that the previous commands are runable) if you want to remove the
previous translations and applu a new one:
```
make clean
make gen_langs
```
If you want to translate the .po files, you run this command:
```
make compile_langs
```

---

For Windows users, you can use
[these tools](https://sourceforge.net/projects/getgnuwin32/files/)
to use the same comands (in CMD or Powershell) explained as in the Makefile.
After decompressing the download, you run this batch file on CMD to translate
the .po files:
```
compile_langs.bat <gnuwin32 path>
```
If you change the strings in the program, to apply the translation run this
command to generate the new .po files:
```
gen_langs.bat <gnuwin32 path>
```
