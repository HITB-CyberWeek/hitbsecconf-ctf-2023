python3 -m py_compile 1.py
cp __pycache__/1.cpython-38.pyc 1.pyc
pydisasm --format xasm 1.py > 1.pyasm
python3 obf_1.py
pyc-xasm 2.pyasm 
python3 2.pyc
decompyle3 2.pyc
