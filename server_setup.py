from setuptools import setup, find_packages

setup(name="Byunichenko_DB_and_PyQt_server_module",
      version="0.0.1",
      description="message_server_app",
      author="Byunichenko Mikhail",
      author_email="mbuinichienko@mail.ru",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )
