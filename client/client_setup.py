import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    'packages': ['common', 'logs', 'client', 'sqlalchemy', 'sqlite3'],
}

setup(name='Byunichenko_DB_and_PyQt_client_module',
      version='0.0.1',
      description='message_client_app',
      options={
          'build_exe': build_exe_options
      },
      executables=[Executable('client.py',
                              base='Win32GUI',
                              target_name='client.exe',
                              )]
      )
