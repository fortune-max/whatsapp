#!/data/data/com.termux/files/usr/bin/env python

import sqlite3, sys, os, time, re

# set WhatsApp Database directory here, uses current directory on failure
DB_DIR = "/data/data/com.whatsapp/databases/"

whitelist = {"23489848747274"} # Modify this to include numbers to never disable

STATUS_PRFX = "STATUS_MSG" # Message caption to discriminate status vs regular msg

TEXT_PRFX = "http://g.gl " # URL message to prefix plain text statuses to enable caption to show

WHATSAPP_DIR = "/sdcard/WhatsApp/" # Folder on internal/external storage where WhatsApp files are stored

DELETE_MISSING = False # In clear operation, continue deletion of record if media is missing

mime_types = ["video/mp4", "image/jpeg", None] # Status types to work on (video, image, text)

# Where video statuses, image statuses and text statuses should be stored
status_mime_pool = {"video/mp4": "2348083454312@s.whatsapp.net", "image/jpeg": "2347053205090@s.whatsapp.net", None: "2348033831003@s.whatsapp.net"}

def disable():
   count = size = 0
   for (_id, key_remote_jid, key_id, data, media_mime_type, media_size, media_caption, remote_resource) in statuses:
      if remote_resource.rstrip("@s.whatsapp.net") not in whitelist:
         if (not media_caption) or (media_caption and not media_caption.startswith(STATUS_PRFX)):
            key_remote_jid = status_mime_pool[media_mime_type]
            media_caption = media_caption if media_caption else ""
            media_caption = "%s|%s|%s|%s"%(STATUS_PRFX, contact_map.get(remote_resource), remote_resource, media_caption)
            remote_resource = None
            if media_mime_type == None:
               # Handle for text to show media_caption
               data = TEXT_PRFX + data
            count += 1
            size += media_size
            try:
               conn.cursor().execute('UPDATE messages SET key_remote_jid=?, data=?, media_caption=?, remote_resource=? WHERE _id=?',
                                     (key_remote_jid, data, media_caption, remote_resource, _id))
            except sqlite3.IntegrityError:
               # Delete older duplicate status update then retry updating newest
               conn.cursor().execute('DELETE FROM messages WHERE key_id=? AND key_remote_jid IS NOT "status@broadcast"',(key_id,))
               conn.cursor().execute('UPDATE messages SET key_remote_jid=?, data=?, media_caption=?, remote_resource=? WHERE _id=?',
                                     (key_remote_jid, data, media_caption, remote_resource, _id))
   return (count, size)

def enable(whitelist_all=False):
   count = size = 0
   for (_id, key_remote_jid, key_id, data, media_mime_type, media_size, media_caption, remote_resource) in statuses:
      caption_split = media_caption.split('|')
      if media_caption and media_caption.startswith(STATUS_PRFX) and (len(caption_split) >= 4):
         remote_resource = caption_split[2]
         if whitelist_all or (remote_resource.rstrip("@s.whatsapp.net") in whitelist):
            media_caption = "".join(caption_split[3:])
            media_caption = None if not media_caption else media_caption
            key_remote_jid = "status@broadcast"
            if media_mime_type == None:
               data = data.lstrip(TEXT_PRFX)
            count += 1
            size += media_size
            try:
               conn.cursor().execute('UPDATE messages SET key_remote_jid=?, data=?, media_caption=?, remote_resource=? WHERE _id=?',
                                     (key_remote_jid, data, media_caption, remote_resource, _id))
            except sqlite3.IntegrityError:
               # Just delete older status duplicate and leave newest as is
               conn.cursor().execute('DELETE FROM messages WHERE key_id=? AND key_remote_jid IS NOT "status@broadcast"',(key_id,))
   return (count, size)

def clear(delete_missing=False):
   # Only disabled statuses can be cleared
   count = size = 0
   for (_id, key_id, timestamp, media_mime_type, media_caption, thumb_image) in statuses:
      # First delete file in storage
      found_file = False
      file_paths = re.findall("Media/.*\.jpg", str(thumb_image)) + re.findall("Media/.*\.mp4", str(thumb_image))
      file_paths = [(WHATSAPP_DIR + x) for x in file_paths]
      for path in file_paths:
         if os.path.isfile(path):
            found_file = True
            print ("Deleting " + path)
            size += os.stat(path).st_size
            os.remove(path)
            break
         else:
            print ("Couldn't find path %s, timestamp = %s, media_caption = %s"%(path, timestamp, media_caption))
      # Then delete record in DB
      if found_file or delete_missing or media_mime_type == None:
         if media_mime_type:
            conn.cursor().execute('DELETE FROM message_thumbnails WHERE key_id=?',(key_id,))
         conn.cursor().execute('DELETE FROM messages WHERE _id=?',(_id,))
         count += 1
   return (count, size)

help_msg = """
      WhatsApp Status Utility built by lordfme

      Usage

      {0} disable [num num num ...]

            Disable all statuses except space separated nums
   
            eg. {0} disable 23483736767836 23480839776864

            Or to disable for everyone {0} disable

      {0} enable [num num num ...]

            Enable all statuses for all space separated nums if disabled

            eg. {0} enable 2348083727863 2341234567837

            Or to enable for everyone {0} enable

      Can also modify whitelist variable to add default numbers not to disable.

      {0} clear [all] [1 | 2 | 3 | ...]

            Clear disabled statuses older than 24h

            all argument means delete status even though media is absent

            number states how many days back statuses should be preserved
   """.format(sys.argv[0])

if len(sys.argv) < 2:
   print (help_msg)
else:
   if not os.path.isdir(DB_DIR):
      DB_DIR = "./"
   DB_FILE_MSGSTORE = DB_DIR + "msgstore.db"
   DB_FILE_WA = DB_DIR + "wa.db"
   if os.path.isfile(DB_FILE_MSGSTORE) and os.path.isfile(DB_FILE_WA):
      # Keep dictionary holidng contact number to name mapping
      conn_wa = sqlite3.connect(DB_FILE_WA)
      contacts = conn_wa.cursor().execute(
         'SELECT jid, sort_name FROM wa_contacts WHERE sort_name IS NOT NULL'
      ).fetchall()
      contact_map = dict(contacts)
      conn_wa.close()

      conn = sqlite3.connect(DB_FILE_MSGSTORE)
      cmd, nums = sys.argv[1], sys.argv[2:]
      whitelist |= set(nums)
      count, size = 0, 0
      mime_map = {"video/mp4": 'media_mime_type="video/mp4"', "image/jpeg": 'media_mime_type="image/jpeg"', None: 'media_mime_type IS NULL'}
      if cmd == "disable":
         statuses = conn.cursor().execute(
            'SELECT _id, key_remote_jid, key_id, data, media_mime_type, media_size, media_caption, remote_resource\
            FROM messages WHERE key_remote_jid="status@broadcast" AND ({0}) AND key_from_me=0'\
            .format(" OR ".join([mime_map[x] for x in mime_types]))
         ).fetchall()
         (count, size) = disable()
         conn.commit()
      elif cmd == "enable":
         statuses = conn.cursor().execute(
            'SELECT _id, key_remote_jid, key_id, data, media_mime_type, media_size, media_caption, remote_resource\
            FROM messages WHERE ({0}) AND ({1}) AND media_caption LIKE "{2}%"'\
            .format(" OR ".join(['key_remote_jid="{0}"'.format(status_mime_pool[x]) for x in mime_types]),\
                    " OR ".join([mime_map[x] for x in mime_types]), STATUS_PRFX)
         ).fetchall()
         (count, size) = enable(not nums)
         conn.commit()
      elif cmd == "clear":
         nums.sort()
         days = int(nums[0]) if nums and nums[0].isdigit() else 1
         delete_missing = nums[-1] == "all" if nums else DELETE_MISSING
         PREV_DAY_MS = str(int(time.time() - (days*24*3600))) + "000"
         statuses = conn.cursor().execute(
            'SELECT _id, key_id, timestamp, media_mime_type, media_caption, thumb_image FROM messages WHERE ({0}) AND ({1}) AND media_caption LIKE "{2}%" AND timestamp < {3}'\
            .format(" OR ".join(['key_remote_jid="{0}"'.format(status_mime_pool[x]) for x in mime_types]),\
                    " OR ".join([mime_map[x] for x in mime_types]), STATUS_PRFX, PREV_DAY_MS)
         ).fetchall()
         (count, size) = clear(delete_missing)
         conn.commit()
      else:
         print ("unknown option, run without arguments to see help file")
      conn.close()
      print ("Done, processed %d statuses of size %.2fMB"%(count, size/1000000.0))
   else:
      print ("msgstore.db and/or wa.db file not found, place in current directory or specify in DB_DIR")
