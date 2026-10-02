from __future__ import annotations
import csv, hashlib, json, re
from pathlib import Path

EMPTY = {"", "—", "-", "na", "n/a", "none", "null"}

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def read_csv(path):
    with open(path,newline='',encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fieldnames=None):
    rows=list(rows)
    fields=fieldnames or (list(rows[0].keys()) if rows else [])
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields)
        if fields: w.writeheader()
        w.writerows(rows)

def split_ids(value):
    return [x.strip() for x in re.split(r'[;,]', value or '') if x.strip() and x.strip().lower() not in EMPTY]
