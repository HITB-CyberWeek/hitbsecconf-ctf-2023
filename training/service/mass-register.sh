#!/bin/bash
if [ -z "$1" ]; then
	echo Usage: $(basename $0) COUNT
	exit 1
fi
for ((i=0; i<$1; i++)); do
	curl -s -F user=user$i -F password=pass$i -F flag=FLAG$i -F register=1 http://localhost:8080/ >/dev/null && echo $i OK
done
