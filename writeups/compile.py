#!/usr/bin/env python3

import markdown
import glob
import logging
import os
import os.path
import pathlib
import shutil
import re

HEADER = """<!DOCTYPE html>
<head>
	<title>{service_name} | HITB CTF 2023</title>
	<meta charset="utf-8">
	<link rel="stylesheet" href="../styles.css">
	<link rel="stylesheet" href="../code.css">
</head>
<body>
"""

FOOTER = """
</body>
</html>
"""

logging.basicConfig(level=logging.INFO)

markdown = markdown.Markdown(extensions=['tables', 'codehilite'])

for writeup_filename in glob.glob("*/*.md"):
	writeup_folder = pathlib.Path(writeup_filename).parent
	service_name = writeup_folder.name
	html_filename = "compiled/" + writeup_filename.replace(".md", ".html").replace("README", "index")

	os.makedirs(pathlib.Path(html_filename).parent, exist_ok=True)

	logging.info(f"Compiling {writeup_filename} → {html_filename}")
	with open(writeup_filename) as writeup_file:
		writeup = writeup_file.read()

	result = markdown.convert(writeup)
	markdown.reset()

	result = re.sub(r'../../services/([^\"]+)/([^/"#]+)', r'../repo/r/repo/b/main/t/services/\1/f=\2.html', result)
	result = re.sub(r'../../sploits/([^\"]+)/([^/"#]+)', r'../repo/r/repo/b/main/t/sploits/\1/f=\2.html', result)
	result = re.sub(r'../../../../blob/main/services/([^\"]+)/([^/"#]+)', r'../repo/r/repo/b/main/t/services/\1/f=\2.html', result)
	result = re.sub(r'../../../../blob/main/sploits/([^\"]+)/([^/"#]+)', r'../repo/r/repo/b/main/t/sploits/\1/f=\2.html', result)
	result = re.sub(r'https://github.com/HITB-CyberWeek/hitbsecconf-ctf-2023/blob/[^/]+/services/([^\"]+)/([^/"#]+)', r'../repo/r/repo/b/main/t/services/\1/f=\2.html', result)
	result = re.sub(r'https://github.com/HITB-CyberWeek/hitbsecconf-ctf-2023/blob/[^/]+/sploits/([^\"]+)/([^/"#]+)', r'../repo/r/repo/b/main/t/sploits/\1/f=\2.html', result)
	result = re.sub(r"#L(\d+)", r"#line-\1", result)

	with open(html_filename, "w") as html_file:
		html_file.write(HEADER.replace("{service_name}", service_name))
		html_file.write(result)
		html_file.write(FOOTER)

	for additional_file in glob.glob(f"{writeup_folder}/*"):
		if additional_file.endswith(".md"):
			continue
		result_filename = "compiled/" + additional_file
		logging.info(f"Copying {additional_file} → {result_filename}")
		shutil.copy(additional_file, result_filename)
