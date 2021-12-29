import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["common", "logs", "server"],
}

setup(name="Byunichenko_DB_and_PyQt_server_module",
      version="0.0.1",
      description="message_server_app",
      options={
          "build_exe": build_exe_options
      },
      executables=[Executable('server.py',
                              base='Win32GUI',
                              targetName='server.exe',
                              )]
      )
