#!/data/data/com.termux/files/usr/bin/env python

import sqlite3, sys, os, time

# set WhatsApp Database directory here, uses current directory on failure
DB_DIR = "/data/data/com.whatsapp/databases/"

whitelist = {"23489848747274"} # Modify this to include numbers to never disable

STATUS_PRFX = "STATUS_MSG" # Message caption to discriminate status vs regular msg

status_pool = "2348083454312@s.whatsapp.net" # Where all statuses should be stored

def disable_video():
   count = size = 0
   for (_id, key_remote_jid, media_size, media_caption, remote_resource) in video_statuses:
      if remote_resource.rstrip("@s.whatsapp.net") not in whitelist:
         if (not media_caption) or (media_caption and not media_caption.startswith(STATUS_PRFX)):
            sent_from = "wa.me/" + remote_resource.rstrip("@s.whatsapp.net")
            key_remote_jid = status_pool
            media_caption = media_caption if media_caption else ""
            media_caption = "%s|%s|%s"%(STATUS_PRFX, sent_from, media_caption)
            remote_resource = None
            count += 1
            size += media_size
            conn.cursor().execute('UPDATE messages SET key_remote_jid=?, media_caption=?, remote_resource=? WHERE _id=?',
                                  (key_remote_jid, media_caption, remote_resource, _id))
   return (count, size)

def enable_video(whitelist_all=False):
   count = size = 0
   for (_id, key_remote_jid, media_size, media_caption, remote_resource) in video_statuses:
      if media_caption and media_caption.startswith(STATUS_PRFX):
         sent_from = "".join(media_caption.split('|')[1:2])
         if whitelist_all or (sent_from.lstrip("wa.me/") in whitelist):
            remote_resource = sent_from.lstrip("wa.me/") + "@s.whatsapp.net"
            media_caption = "".join(media_caption.split('|')[2:])
            media_caption = None if not media_caption else media_caption
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
         video_statuses = conn.cursor().execute(
            'SELECT _id, key_remote_jid, media_size, media_caption, remote_resource\
            FROM messages WHERE key_remote_jid="{0}" AND media_mime_type="video/mp4" AND media_caption LIKE "{1}%"'.format(status_pool, STATUS_PRFX)
         ).fetchall()
         (count, size) = enable_video(not nums)
         conn.commit()

      conn.close()
      print ("Done, processed %d statuses of size %.2fMB"%(count, size/1000000.0))
   else:
      print ("msgstore.db file not found, place in current directory or specify in DB_DIR")
