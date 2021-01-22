#!/usr/bin/env python

import os
import time
import logging
import sys
import shutil

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)

# Constants for converting bytes
K=1024
KB = K
MB=K * KB
GB=K * MB
TB=K * GB

def get_size(path):
  total_bytes = 0
  for dirpath, dirnames, filenames in os.walk(path):
    for f in filenames:
      fp = os.path.join(dirpath, f)
      try:
        total_bytes += os.path.getsize(fp)
      except os.error as e:
        # Path does not exist or is inaccessible
        logging.warning('Skipping due to os.error {0}'.format(e))
        pass
  return total_bytes

def get_age_days(path):
  mtime = os.path.getmtime(path)
  now = time.time()
  age_seconds = now - mtime
  age_days = age_seconds // 86400
  return int(age_days)

def get_directories_ages(parent):
  children = os.listdir(parent)
  directories_ages = []
  for child in children:
    path = os.path.join(parent, child)
    try:
      if os.path.isdir(path):
        age_days = get_age_days(path)
        # When tallying the subdirectories and ages, just use the relative path
        size_bytes = get_size(path)
        formatted_size = format_size(size_bytes)
        directories_ages.append((child, age_days, size_bytes, formatted_size))
    except os.error as e:
      logging.warning('Skipping due to os.error {0}'.format(e))
  sorted_by_age = sorted(directories_ages, key=lambda x: x[1], reverse=False)
  return sorted_by_age

def format_size(bytes):
  if bytes > TB: divisor, unit = TB, 'TB'
  elif bytes > GB: divisor, unit = GB, 'GB'
  elif bytes > MB: divisor, unit = MB, 'MB'
  else: divisor, unit = KB, 'KB'
  return '{0} {1}'.format(bytes / divisor, unit)

def main():
  if len(sys.argv) < 2:
    print('Usage: {0} <path>\n'.format(sys.argv[0]))
    exit(1)
  path = sys.argv[1]
  result = get_directories_ages(path)
  for r in result:
    print(r)

if __name__ == '__main__':
  main()

