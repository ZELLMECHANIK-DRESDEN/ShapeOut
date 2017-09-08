Appveyor recipe
---------------

Files that are used by ../appveyor.yaml to build a Windows installer

- `hook-*.py` : PyInstaller hooks   
  Packages not found by PyInstaller automatically and data files

- `patch_libraries` : patches existing Python libraries      
  For example `pyface` raised unneccessary `NotImplementedError`s
  when frozen. 

- `pinned` : pin packages in Anaconda   
  Keep certain packages at older version to ensure they work
  well together.

- `run_with_compiler.cmd` : powershell tools   
  Something required for running stuff on i386 and x64
  
- `win_shapeout.iss` : InnoSetup file   
  Configuration for building the installer
  
- `win_shapeout.spec` : PyInstaller spec file      
  The configuration for building the binaries with PyInstaller
      