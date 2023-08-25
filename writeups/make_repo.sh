#!/bin/bash

set -ex

rm -rf compiled/repo
pushd ../../git-arr/
./git-arr --config config.conf generate --output ../../hitbsecconf-ctf-2023/writeups/compiled/repo
popd

rm -rf compiled/repo/r/repo/b/pure/
rm -rf compiled/repo/r/repo/c/
rm -rf compiled/repo/r/repo/b/main/t/ansible/
rm -rf compiled/repo/r/repo/b/main/t/checkers/
rm -rf compiled/repo/r/repo/b/main/t/vuln_images/
rm -rf compiled/repo/r/repo/b/main/t/cs/
rm -rf compiled/repo/r/repo/b/main/t/training/
rm -rf compiled/repo/r/repo/b/main/t/.github

for f in `seq 0 10`
do
    rm -rf compiled/repo/r/repo/b/main/t/$f.html
    rm -rf compiled/repo/r/repo/b/main/$f.html
done


