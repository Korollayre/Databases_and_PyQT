import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    'packages': ['common', 'logs', 'server', 'sqlalchemy', 'sqlite3'],
}

setup(name='byunichenko_server_module',
      version='0.0.1',
      description='message_server_app',
      options={
          'build_exe': build_exe_options
      },
      executables=[Executable('server.py',
                              base='Win32GUI',
                              target_name='server.exe',
                              )]
      )
