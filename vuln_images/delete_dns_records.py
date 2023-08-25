#!/usr/bin/env python3

import settings
import digitalocean
import re

domain = digitalocean.Domain(token=settings.DO_API_TOKEN, name=settings.DNS_ZONE)
for record in domain.get_records():
    if re.fullmatch(r"[^.]+\.team\d+", record.name):
        print(record.name, record.data)
        domain.delete_domain_record(id=record.id)
