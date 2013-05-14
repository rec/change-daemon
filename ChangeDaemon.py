#!/usr/bin/env python

from __future__ import absolute_import, division, print_function #, unicode_literals

import json
import logging
import os
import os.path
import re
import smtplib

LOG_FILE = '/root/change-daemon/og.log'
PERSISTENT_FILE = '/root/change-daemon/results.json'
ADDRESS_FILE = '/root/change-daemon/emails.json'
FROM = 'new-scripts@swirly.com'
TO = 'tom@swirly.com'
HOST = 'swirly.com'
MATCH = re.compile(r'/home/(.+)/public_html/')
EXTENSIONS = set(['.pl', '.php'])
BASE = '/home'

WRITE_RESULTS = True
SEND_RESULTS = True

MAIL_MESSAGE = """\
From: {from_addr}
To: {to_addr}
Subject: {subject}

Some script files have changed on the server:

{body}

--

A signature goes here.

"""

def find_files(base, extensions, pattern):
  results = {}
  for root, dirs, files in os.walk(base):
    for f in files:
      if os.path.splitext(f)[1] in extensions:
        path = os.path.join(root, f)
        match = pattern.match(path)
        if match:
          results[path] = [os.path.getmtime(path), match.group(1)]

  return results

def get_file(filename):
  if os.path.exists(filename):
    with open(filename, 'r') as f:
      return json.load(f)
  else:
    return {}

def write_file(filename, value):
  if WRITE_RESULTS:
    with open(filename, 'w') as f:
      json.dump(value, f)

def compare_files(old, new):
  results = {}
  for new_path, (new_time, owner) in new.iteritems():
    old_entry = old.get(new_path, None)
    if not old_entry:
      added, changed = results.setdefault(owner, [[], []])
      added.append(new_path)
    elif new_time > old_entry[0]:
      added, changed = results.setdefault(owner, [[], []])
      changed.append(new_path)
  return results

def get_changes_save_and_send_mail():
  old = get_file(PERSISTENT_FILE)
  new = find_files(BASE, EXTENSIONS, MATCH)
  write_file(PERSISTENT_FILE, new)
  results = []
  diffs = compare_files(old, new)
  if not diffs:
    return

  files, count = 0, 0
  for owner, (added, changed) in diffs.iteritems():
    count += 1
    results.append('Owner ' + owner)
    files += len(added) + len(changed)
    if added:
      results.append('  Added:')
      results.extend('    ' + a for a in added)
      results.append('')
    if changed:
      results.append('  Changed:')
      results.extend('    ' + a for a in changed)
      results.append('')
    results.append('')
    results.append('--------------------------------------------')
    results.append('')

  body = '\n'.join(results)
  files_plural = '' if files == 1 else 's'
  count_plural = '' if count == 1 else 's'
  subject = 'ax.to: new activity on %d file%s from %s owner%s.' % (
    files, files_plural, count, count_plural)
  mail = MAIL_MESSAGE.format(from_addr=FROM, to_addr=TO, subject=subject, 
                             body=body)

  if SEND_RESULTS:
    server = smtplib.SMTP(HOST)
    server.sendmail(FROM, [TO], mail)
    server.quit()
    print('sent.')
  else:
    print(body)

if __name__ == '__main__':
  get_changes_save_and_send_mail()
