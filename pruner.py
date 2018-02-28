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

def get_oldest_directory(parent, exclude=[]):
  children = os.listdir(parent)
  # remove anything we're supposed to exclude
  [children.remove(x) for x in exclude if x in children]
  directories_ages = []
  for child in children:
    path = os.path.join(parent, child)
    try:
      if os.path.isdir(path):
        age_days = get_age_days(path)
        # When tallying the subdirectories and ages, just use the relative path
        directories_ages.append((child, age_days))
    except os.error as e:
      logging.warning('Skipping due to os.error {0}'.format(e))
  sorted_by_age = sorted(directories_ages, key=lambda x: x[1], reverse=True)
  if sorted_by_age:
    return sorted_by_age[0]
  else:
    return None

def get_free_bytes(path):
  result = os.statvfs(path)
  free_bytes = result.f_bfree * result.f_frsize
  return free_bytes

def delete(path):
  logging.debug('Deleting {0}'.format(path))
  shutil.rmtree(path) # ignore errors

def format_size(bytes):
  if bytes > TB: divisor, unit = TB, 'TB'
  elif bytes > GB: divisor, unit = GB, 'GB'
  elif bytes > MB: divisor, unit = MB, 'MB'
  else: divisor, unit = KB, 'KB'
  return '{0} {1}'.format(bytes / divisor, unit)

def clean(path, desired_free_bytes, min_age_days, dry_run=True):
  free_bytes = get_free_bytes(path)
  logging.info('Starting, current free space: {0}, desired {1}. Considering directories older than {2} days'.format(format_size(free_bytes), format_size(desired_free_bytes), min_age_days))

  # For dry-run
  reclaimed_dirs=[]
  reclaimed_bytes=0
  prefix = 'DRY-RUN:' if dry_run else ''

  while free_bytes < desired_free_bytes:
    logging.debug('Current free space: {0}, desired: {1}'.format(format_size(free_bytes), format_size(desired_free_bytes)))
    oldest_directory = get_oldest_directory(path, exclude=reclaimed_dirs)
    if not oldest_directory:
      logging.info('Stopping: No directories found')
      break
    name, age_days = oldest_directory
    absolute_path = os.path.join(path, name)
    if age_days > min_age_days:
      size = get_size(absolute_path)
      logging.info('{0}Delete {1}. Age: {2} days, Size: {3}'.format(prefix, name, age_days, format_size(size)))
      if dry_run:
        # on dry_run, won't actually delete anything, but do count
        reclaimed_bytes += size
        reclaimed_dirs.append(name)
      else:
        delete(absolute_path)
    else:
      logging.info('Stopping: Oldest directory {0} age is {1} days, newer than our minimum of {2}'.format(name, age_days, min_age_days))
      break
    free_bytes = get_free_bytes(path) + reclaimed_bytes
  else:
    logging.info('Current free space: {0} exceeds desired free space: {1}, done!'.format(format_size(free_bytes), format_size(desired_free_bytes)))

def main():
  if len(sys.argv) < 4:
    print 'Usage: {0} <path> <desired free space in TB> <number of days to keep> [--remove]\n'.format(sys.argv[0])
    print 'Without --remove, the script will not delete any data, just report what would be removed to meet desired criteria.'
    exit(1)
  path = sys.argv[1]
  desired_free_bytes = float(sys.argv[2]) * TB
  min_age_days = int(sys.argv[3])

  if '--remove' in sys.argv:
    dry_run = False
  else:
    dry_run = True

  clean(path, desired_free_bytes, min_age_days, dry_run)

if __name__ == '__main__':
  main()

