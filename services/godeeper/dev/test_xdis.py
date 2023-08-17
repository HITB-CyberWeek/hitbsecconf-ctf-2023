import xdis

# Декомпилируем байт-код
code = xdis.load_module('__pycache__/test_obf1.cpython-39.pyc')

# Выводим декомпилированный код
print(code.code.co_code)
