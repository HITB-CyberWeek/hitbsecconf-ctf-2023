cp assemble.py /usr/local/lib/python3.8/site-packages/xasm/
python3 -m py_compile 1.py
cp __pycache__/1.cpython-38.pyc 1.pyc
pydisasm --format xasm 1.py > 1.pyasm
python3 obf_1.py
pyc-xasm 2.pyasm 
pydisasm --format xasm 2.pyc > 2_dec.pyasm

