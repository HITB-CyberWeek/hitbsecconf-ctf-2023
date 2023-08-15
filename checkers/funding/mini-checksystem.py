#!/usr/bin/env python3
import subprocess
import random
import string
import sys

if len(sys.argv) < 3:
    print("Args: HOST ROUNDS")
    sys.exit(1)

HOST = sys.argv[1]
ROUNDS = int(sys.argv[2])
CHECKER_NAME = './funding.checker.js'

prefix = "".join(random.choices(string.ascii_lowercase, k=4))
print("Flag ID Prefix:", prefix)

for r in range(1, ROUNDS + 1):
    print(" ========= Round %d of %d ========= " % (r, ROUNDS))

    (code, out) = subprocess.getstatusoutput("%s check %s" % (CHECKER_NAME, HOST))
    print(code, out)
    assert code == 101

    print("=" * 64)

    flag_id = "%s%04d" % (prefix, r)
    flag_data = ("F"*32) + "="

    cmd = "%s put %s %s %s 1" % (CHECKER_NAME, HOST, flag_id, flag_data)
    print("RUN:", cmd)
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    assert proc.returncode == 101

    print("=" * 64)

    flag_id = out.decode().strip()
    # cmd = "%s get %s '%s' %s 1" % (CHECKER_NAME, HOST, flag_id.replace("'", "\\'"), flag_data)
    cmd = [CHECKER_NAME, "get", HOST, flag_id, flag_data]
    print("RUN:", cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    assert proc.returncode == 101


print("Completed. Good job!")
