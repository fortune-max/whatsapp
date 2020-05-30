#!/data/data/com.termux/files/usr/bin/env python

import sqlite3, sys, os, time, re, argparse

# set WhatsApp Database directory here, uses current directory on failure
DB_DIR = "/data/data/com.whatsapp/databases/"

whitelist = {"2349030455845", "2348159186070", "2348139319159", "2348022219174", "2348170021596", "2348109143064", "233542912743", "2349090775802", "2347081584968", "2348105073022", "2349026885579"} # Modify this to include numbers to never disable

STATUS_PRFX = "STATUS_MSG" # Message caption to discriminate status vs regular msg

TEXT_PRFX = "http://f.me " # URL message to prefix plain text statuses to enable caption to show

WHATSAPP_DIR = "/sdcard/WhatsApp/" # Folder on internal/external storage where WhatsApp files are stored

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
               data = "" if not data else data
               data = TEXT_PRFX + data
            else:
               try:
                  conn.cursor().execute('UPDATE message_thumbnails SET key_remote_jid=? WHERE key_remote_jid=? AND key_id=?',
                                        (key_remote_jid, "status@broadcast", key_id))
               except sqlite3.IntegrityError:
                  # Delete older duplicate status thumbnail then retry updating newest
                  conn.cursor().execute('DELETE FROM message_thumbnails WHERE key_id=? AND key_remote_jid IS NOT "status@broadcast"', (key_id,))
                  conn.cursor().execute('UPDATE message_thumbnails SET key_remote_jid=? WHERE key_remote_jid=? AND key_id=?',
                                        (key_remote_jid, "status@broadcast", key_id))
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

def enable():
   count = size = 0
   for (_id, key_remote_jid, key_id, data, media_mime_type, media_size, media_caption, remote_resource) in statuses:
      caption_split = media_caption.split('|')
      if media_caption and media_caption.startswith(STATUS_PRFX) and (len(caption_split) >= 4):
         remote_resource = caption_split[2]
         media_caption = "".join(caption_split[3:])
         media_caption = None if not media_caption else media_caption
         key_remote_jid = "status@broadcast"
         if media_mime_type == None:
            data = data.lstrip(TEXT_PRFX)
            data = None if not data else data
         else:
            try:
               conn.cursor().execute('UPDATE message_thumbnails SET key_remote_jid=? WHERE key_remote_jid=? AND key_id=?',
                                     (key_remote_jid, status_mime_pool[media_mime_type], key_id))
            except sqlite3.IntegrityError:
               # Just delete older status thumbnail and leave newest as is
               conn.cursor().execute('DELETE FROM message_thumbnails WHERE key_id=? AND key_remote_jid IS NOT "status@broadcast"', (key_id,))
         count += 1
         size += media_size
         try:
            conn.cursor().execute('UPDATE messages SET key_remote_jid=?, data=?, media_caption=?, remote_resource=? WHERE _id=?',
                                  (key_remote_jid, data, media_caption, remote_resource, _id))
         except sqlite3.IntegrityError:
            # Just delete older status duplicate and leave newest as is
            conn.cursor().execute('DELETE FROM messages WHERE key_id=? AND key_remote_jid IS NOT "status@broadcast"',(key_id,))
   return (count, size)

def clear():
   # Only disabled statuses can be cleared
   count = size = 0
   for (_id, key_id, timestamp, media_mime_type, media_caption, thumb_image) in statuses:
      # First delete file in storage
      file_paths = re.findall("Media/.*\.jpg", str(thumb_image)) + re.findall("Media/.*\.mp4", str(thumb_image))
      file_paths = [(WHATSAPP_DIR + x) for x in file_paths]
      for path in file_paths:
         if os.path.isfile(path):
            print ("Deleting " + path)
            size += os.stat(path).st_size
            os.remove(path)
            break
         else:
            print ("Couldn't find path %s, timestamp = %s, media_caption = %s"%(path, timestamp, media_caption))
      # Then delete record in DB
      if media_mime_type:
         conn.cursor().execute('DELETE FROM message_thumbnails WHERE key_id=?',(key_id,))
      conn.cursor().execute('DELETE FROM messages WHERE _id=?',(_id,))
      count += 1
   return (count, size)

ap = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter, 
description = "Presents status updates as regular WhatsApp messages to allow for storing statuses to view at your own time and/or allowing finer control of which statuses get downloaded.",
epilog = """Days option can only be used with clear operation, will be ignored otherwise. Only one of these operations can be done at a time (enable, disable or clear), extra operations will be ignored. Enabling statuses only works if status is still present on status roll, WhatsApp removes disabled statuses after a while from status roll.

Examples

%(prog)s -d                 disables statuses currently in status roll and saves as messages
%(prog)s -d -m 4            disable videos alone (moves video statuses to messages)
%(prog)s -c                 clear all disabled statuses older than 24h
%(prog)s -e                 enable statuses previously disabled (moves them back to status roll)
%(prog)s -e -m 1            enable text statuses previously disabled (moves them back to status roll)
%(prog)s -c -m 3 -D 2       clear text and image statuses older than 2 days

Disabled statuses can be found here {}

Built by lordfme (https://github.com/lordfme/whatsapp)""".format(" ".join(map(lambda x: "http://wa.me/"+x.strip("@s.whatsapp.net"),status_mime_pool.values()))))

ap.add_argument("-d", "--disable", action="store_true", help = "Disable statuses")
ap.add_argument("-e", "--enable", action="store_true", help = "Enable statuses")
ap.add_argument("-c", "--clear", action="store_true", help = "Clear disabled statuses")
ap.add_argument("-D", "--days", default=1, type=int, help = "Clear statuses older than D days ago, default 1")
ap.add_argument("-m", "--mode", default=7, type=int, help = "Text (1), Images (2), Videos (4), sum to get mimetypes to operate on, default 7 (all)")
args = vars(ap.parse_args())

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
   count, size = 0, 0
   mime_types = [mime_types[i] for i in range(3) if bin(args['mode'])[2:].zfill(3)[i] == '1']
   mime_map = {"video/mp4": 'media_mime_type="video/mp4"', "image/jpeg": 'media_mime_type="image/jpeg"', None: 'media_mime_type IS NULL'}
   if args["disable"]:
      statuses = conn.cursor().execute(
         'SELECT _id, key_remote_jid, key_id, data, media_mime_type, media_size, media_caption, remote_resource\
         FROM messages WHERE key_remote_jid="status@broadcast" AND ({0}) AND key_from_me=0'\
         .format(" OR ".join([mime_map[x] for x in mime_types]))
      ).fetchall()
      (count, size) = disable()
      conn.commit()
   elif args["enable"]:
      statuses = conn.cursor().execute(
         'SELECT _id, key_remote_jid, key_id, data, media_mime_type, media_size, media_caption, remote_resource\
         FROM messages WHERE ({0}) AND ({1}) AND media_caption LIKE "{2}%"'\
         .format(" OR ".join(['key_remote_jid="{0}"'.format(status_mime_pool[x]) for x in mime_types]),\
                 " OR ".join([mime_map[x] for x in mime_types]), STATUS_PRFX)
      ).fetchall()
      (count, size) = enable()
      conn.commit()
   elif args["clear"]:
      days = args["days"]
      PREV_DAY_MS = str(int(time.time() - (days*24*3600))) + "000"
      statuses = conn.cursor().execute(
         'SELECT _id, key_id, timestamp, media_mime_type, media_caption, thumb_image FROM messages WHERE ({0}) AND ({1}) AND media_caption LIKE "{2}%" AND timestamp < {3}'\
         .format(" OR ".join(['key_remote_jid="{0}"'.format(status_mime_pool[x]) for x in mime_types]),\
                 " OR ".join([mime_map[x] for x in mime_types]), STATUS_PRFX, PREV_DAY_MS)
      ).fetchall()
      (count, size) = clear()
      conn.commit()
   else:
      ap.print_help()
   conn.close()
   print ("Done, processed %d statuses of size %.2fMB"%(count, size/1000000.0))
else:
   print ("msgstore.db and/or wa.db file not found, place in current directory or specify in DB_DIR")
