#!/system/xbin/python

import sqlite3, sys, os

#set WhatsApp Database directory here, uses current directory on failure
DB_DIR = "/data/data/com.whatsapp/databases/"

whitelist = {"2348172839121"}

def disable_video():
   count = size = 0
   for (_id, remote_resource, media_size) in video_statuses:
      if remote_resource.strip("@s.whatsapp.net") not in whitelist:
         if remote_resource[0] != "X" :
            remote_resource = "X" + remote_resource
            count += 1
            size += media_size
            conn.cursor().execute('UPDATE messages SET _id=?, remote_resource=? WHERE _id=?', (_id, remote_resource, _id))
   return (count, size)

def enable_video(whitelist_all=False):
   count = size = 0
   for (_id, remote_resource, media_size) in video_statuses:
      if whitelist_all or (remote_resource.strip("@s.whatsapp.net") in whitelist):
         if remote_resource[0] == "X":
            remote_resource = remote_resource[1:]
            count += 1
            size += media_size
            conn.cursor().execute('UPDATE messages SET _id=?, remote_resource=? WHERE _id=?', (_id, remote_resource, _id))
   return (count, size)

if len(sys.argv) < 2: 
   print """
      WhatsApp Status Utility built by lordfme

      Usage

      ./vid_status.py disable [num num num ...]

            Disable all video statuses except space separated nums
   
            eg. ./vid_status.py disable 23483736767836 23480839776864

            Or to disable for everyone ./vid_status.py disable

      ./vid_status.py enable [num num num ...]

            Enable all video statuses for all space separated nums if disabled

            eg. ./vid_status.py enable 2348083727863 2341234567837

            Or to enable for everyone ./vid_status.py enable

      Can also modify whitelist variable to add default numbers not to disable.
   """
else:
   if not os.path.exists(DB_DIR):
      DB_DIR = "./"
   DB_FILE = DB_DIR + "msgstore.db"
   if os.path.exists(DB_FILE):
      conn=sqlite3.connect(DB_FILE)
      video_statuses = conn.cursor().execute('SELECT _id, remote_resource, media_size FROM messages WHERE key_remote_jid="status@broadcast" AND media_mime_type="video/mp4"').fetchall();
   
      cmd, nums = sys.argv[1], sys.argv[2:]
      whitelist |= set(nums)
      if cmd == "disable":
         (count, size) = disable_video()
         conn.commit()
      elif cmd == "enable":
         (count, size) = enable_video(not nums)
         conn.commit()

      conn.close()
      print ("Done, processed %d statuses of size %.2fMB"%(count, size/1000000.0))
   else:
      print ("msgstore.db file not found, place in current directory or specify in DB_DIR")
