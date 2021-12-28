from setuptools import setup, find_packages

setup(name="Byunichenko_DB_and_PyQt_client_module",
      version="0.0.1",
      description="message_client_app",
      author="Byunichenko Mikhail",
      author_email="mbuinichienko@mail.ru",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )
