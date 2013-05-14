from __future__ import absolute_import, division, print_function, unicode_literals

import json
import logging
import os
import os.path
import re

LOG_FILE = '/tmp/change_daemon_log.log'
PERSISTENT_FILE = '/etc/change-daemon/results.json'
ADDRESS_FILE = '/etc/change-daemon/emails.json'
FROM = 'errors@swirly.com'
TO = 'tom@swirly.com'
HOST = 'swirly.com'
MATCH = re.compile(r'/home/(.+)/public_html/')
EXTENSIONS = set(['.pl', '.php'])
BASE = '/home'

MAIL_MESSAGE = """\
From: {from}
To: {to}

{body}
"""

def find_files(base, extensions, pattern):
  results = {}
  for root, dirs, files in os.walk(base):
    for f in files:
      if os.path.splitext(f) in extensions:
        path = os.path.join(root, f)
        match = pattern.match(path)
        if match:
          results[path] = os.path.getmtime(path), match.group(1)
  return results

def get_file(filename):
  if os.path.exists(filename):
    with open(filename, 'r') as f:
      return json.load(f)
  else:
    return {}

def write_file(filename, value):
  with open(filename, 'w') as f:
    json.dump(value, f)

def compare_files(old, new):
  results = {}
  for new_path, (new_time, owner) in new:
    added, changed = results.setdefault(owner, [[], []])
    old_entry = old.get(path, None)
    if not old_entry:
      added.append(new_path)
    elif new_time > old_entry[0]:
      changed.append(new_path)
  return results

def get_changes_save_and_send_mail():
  old = get_file(PERSISTENT_FILE)
  new = find_files(BASE, EXTENSIONS, MATCH)
  write_file(PERSISTENT_FILE, new)
  results = []
  for owner, (added, changed) in compare_files(old, new):
    results.append('Owner ' + owner)
    results.append('  Added')
    results.extend('    ' + a for a in added)
    results.append('')
    results.append('  changed')
    results.extend('    ' + a for a in changed)
    results.append('')
    results.append('---')
    results.append('')

  body = '\n'.join(results)
  mail = MAIL_MESSAGE.format(from=FROM, to=TO, body=BODY)

  if SEND_RESULTS:
    server = smtplib.SMTP(HOST)
    server.sendmail(FROM, [TO], BODY)
    server.quit()
  else:
    print(BODY)
