#!/data/data/com.termux/files/usr/bin/env python

import sqlite3, sys, os, time

# set WhatsApp Database directory here, uses current directory on failure
DB_DIR = "/data/data/com.whatsapp/databases/"

whitelist = {"23489848747274"} # Modify this to include numbers to never disable

STATUS_PRFX = "STATUS_MSG: " # Message caption to discriminate status vs regular msg

def disable_video():
   count = size = 0
   for (_id, key_remote_jid, media_size, media_caption, remote_resource) in video_statuses:
      if remote_resource.strip("@s.whatsapp.net") not in whitelist:
         if (not media_caption) or (media_caption and not media_caption.startswith(STATUS_PRFX)):
            key_remote_jid = remote_resource
            media_caption = (STATUS_PRFX + media_caption) if media_caption else STATUS_PRFX
            remote_resource = None
            count += 1
            size += media_size
            conn.cursor().execute('UPDATE messages SET key_remote_jid=?, media_caption=?, remote_resource=? WHERE _id=?',
                                  (key_remote_jid, media_caption, remote_resource, _id))
   return (count, size)

def enable_video(whitelist_all=False):
   count = size = 0
   for (_id, key_remote_jid, timestamp, media_size, media_caption, remote_resource) in video_statuses:
      if whitelist_all or (key_remote_jid.strip("@s.whatsapp.net") in whitelist):
         if media_caption and media_caption.startswith(STATUS_PRFX):
            remote_resource = key_remote_jid
            media_caption = None if media_caption == STATUS_PRFX else media_caption.lstrip(STATUS_PRFX)
            key_remote_jid = "status@broadcast"
            count += 1
            size += media_size
            conn.cursor().execute('UPDATE messages SET key_remote_jid=?, media_caption=?, remote_resource=? WHERE _id=?',
                                  (key_remote_jid, media_caption, remote_resource, _id))
   return (count, size)

if len(sys.argv) < 2:
   print ("""
      WhatsApp Status Utility built by lordfme

      Usage

      {0} disable [num num num ...]

            Disable all video statuses except space separated nums
   
            eg. {0} disable 23483736767836 23480839776864

            Or to disable for everyone {0} disable

      {0} enable [num num num ...]

            Enable all video statuses for all space separated nums if disabled

            eg. {0} enable 2348083727863 2341234567837

            Or to enable for everyone {0} enable

      Can also modify whitelist variable to add default numbers not to disable.
   """).format(sys.argv[0])
else:
   if not os.path.exists(DB_DIR):
      DB_DIR = "./"
   DB_FILE = DB_DIR + "msgstore.db"
   if os.path.exists(DB_FILE):
      conn=sqlite3.connect(DB_FILE)
      cmd, nums = sys.argv[1], sys.argv[2:]
      whitelist |= set(nums)
      if cmd == "disable":
         video_statuses = conn.cursor().execute(
            'SELECT _id, key_remote_jid, media_size, media_caption, remote_resource\
            FROM messages WHERE key_remote_jid="status@broadcast" AND media_mime_type="video/mp4"'
         ).fetchall()
         (count, size) = disable_video()
         conn.commit()
      elif cmd == "enable":
         PREV_DAY = str(time.time()-86400).split('.')[0] + "000"
         video_statuses = conn.cursor().execute(
            'SELECT _id, key_remote_jid, timestamp, media_size, media_caption, remote_resource\
            FROM messages WHERE timestamp > {0} AND media_mime_type="video/mp4" AND media_caption LIKE "{1}%"'.format(PREV_DAY, STATUS_PRFX)
         ).fetchall()
         (count, size) = enable_video(not nums)
         conn.commit()

      conn.close()
      print ("Done, processed %d statuses of size %.2fMB"%(count, size/1000000.0))
   else:
      print ("msgstore.db file not found, place in current directory or specify in DB_DIR")
