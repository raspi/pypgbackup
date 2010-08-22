#!/bin/env python
# Pekka Järvinen 2010
# Simple PostgreSQL database dumping script which categorizes dumps to active and non-active
# PostgreSQL connection information is read from environmental variables

import traceback
import sys
import os
import subprocess
import time

from pg8000 import DBAPI

os.putenv('PGHOST', os.getenv('PGHOST'))
os.putenv('PGDATABASE', os.getenv('PGDATABASE'))
os.putenv('PGUSERNAME', os.getenv('PGUSERNAME'))
os.putenv('PGPASSWORD', os.getenv('PGPASSWORD'))

if os.getenv('PGPORT') is not None:
  os.putenv('PGPORT', os.getenv('PGPORT'))


def run(cmd):
  print "Running " + ' '.join(cmd)
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  p.wait()
  return p

def getUsers(conn):
  cur = conn.cursor()
  cur.execute("""SELECT rolname FROM pg_authid WHERE rolcanlogin=true AND rolsuper=false""")
  rows = cur.fetchall()
  cur.close()
  users = {}
  for row in rows:
    users[row[0]] = {'Login': True}

  return users

def getDatabases(conn):
  cur = conn.cursor()
  cur.execute("""SELECT datname FROM pg_database""")
  rows = cur.fetchall()
  cur.close()
  databases = {}
  for row in rows:
    databases[row[0]] = {'Backup': False}

  return databases

def isActive(conn, dbname):
  dbname = str(dbname)
  cur = conn.cursor()
  cur.execute("""SELECT CASE WHEN COUNT(*) > 0 THEN true ELSE false END::boolean c FROM pg_stat_activity WHERE datname=%s""", (dbname, ))
  row = cur.fetchone()
  cur.close()
  return row[0]


def takeBackup(dbname, isActive):
  path = os.getenv('PGBDIR') + dbname
  
  if isActive:
    path += '_active'

  path += '.dump'

  cmd = [
    'pg_dump',
    '--no-password',
    '--username',
    os.getenv('PGUSERNAME'),
    '--format=custom',
    '--no-acl',
    '--no-owner',
    '--file',
    path,
    dbname
  ]
  
  p = run(cmd)
  if p.returncode == 0:
    return True

  if p is not None:
    print "\n".join(p.stderr.readlines())
    print "\n".join(p.stdin.readlines())
    print "\n".join(p.stdout.readlines())

  return False


if __name__ == "__main__":

  conn = DBAPI.connect(host=os.getenv('PGHOST'), database=os.getenv('PGDATABASE'), user=os.getenv('PGUSERNAME'), password=os.getenv('PGPASSWORD'));
  cur = conn.cursor()

  users = getUsers(conn)

  # Disable logins for users
  for i in users:
    cur.execute("""UPDATE pg_authid SET rolcanlogin=false WHERE rolname=%s""", (i, ))

  time.sleep(1)

  try:
    databases = getDatabases(conn)

    # Take backups per database
    for i in databases:
      try:
        databases[i]['Active'] = isActive(conn, i)
        databases[i]['Backup'] = takeBackup(i, databases[i]['Active'])
      except:
        print "Unexpected error:", sys.exc_info()
  except:
    print "Unexpected error:", sys.exc_info()

  # Enable logins for users
  for i in users:
    cur.execute("""UPDATE pg_authid SET rolcanlogin=true WHERE rolname=%s""", (i, ))

  for i in databases:
    print i + ':',
    for j in databases[i]:
      print j, '=', databases[i][j] ,
    print