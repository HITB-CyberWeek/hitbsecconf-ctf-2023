import py_compile

# Компилируем файл .py в .pyc
py_compile.compile('test_obf1.py')

from uncompyle6.main import decompile_file

# Декомпилируем .pyc файл в исходный код
print(decompile_file('__pycache__/test_obf1.cpython-310.pyc'))
