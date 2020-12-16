#!/data/data/com.termux/files/usr/bin/env python

# ========================TODO===============================
# Feature to save pushed status updates to GC

# Run this SQL query on your DB to ensure thumbnails of cleared statuses don't clutter DB
# CREATE TRIGGER messages_bd_for_message_thumbnails_trigger BEFORE DELETE ON messages BEGIN DELETE FROM message_thumbnails WHERE key_id=old.key_id;

import os
import re
import time
import sqlite3
import argparse

DB_DIR = "/data/data/com.whatsapp/databases/" # WhatsApp DB directory
whitelist = {None,} # Modify this to include numbers to never disable
blacklist = {None,} # Modify this to include numbers to always disable
WHATSAPP_DIR = "/sdcard/WhatsApp/"  # WhatsApp folder on local storage
mime_types = ["video/mp4", "image/jpeg",None] # Status types to work on (video, image, text)
status_mime_pool = {
    "video/mp4": "2348083454312-1607815117@g.us",
    "image/jpeg": "2348083454312-1607785006@g.us",
    None: "2348083454312-1607815145@g.us",
} # Where video statuses, image statuses and text statuses should be stored in (Group chats)


def disable():
    count = size = 0
    for (_id, key_remote_jid, key_id, media_mime_type, media_size, remote_resource) in statuses:
        if remote_resource.rstrip("@s.whatsapp.net") in (whitelist - blacklist):
            continue
        start_id, stop_id = 0, 99999999999
        if args["unviewed"]:
            stop_id, start_id = sql(f"SELECT message_table_id, last_read_message_table_id FROM status_list WHERE key_remote_jid='{remote_resource}'", 0)()
        if (start_id < _id <= stop_id):
            key_remote_jid = status_mime_pool[media_mime_type]
            if media_mime_type != None:
                try:
                    sql(f"UPDATE message_thumbnails SET key_remote_jid='{key_remote_jid}' WHERE key_remote_jid='status@broadcast' AND key_id='{key_id}'")
                except sqlite3.IntegrityError:
                    # Delete older duplicate status thumbnail then retry updating newest
                    sql(f"DELETE FROM message_thumbnails WHERE key_id='{key_id}' AND key_remote_jid IS NOT 'status@broadcast'")
                    sql(f"UPDATE message_thumbnails SET key_remote_jid='{key_remote_jid}' WHERE key_remote_jid='status@broadcast' AND key_id='{key_id}'")
            count += 1; size += media_size
            try:
                sql(f"UPDATE messages SET key_remote_jid='{key_remote_jid}' WHERE _id={_id}")
            except sqlite3.IntegrityError:
                # Delete older duplicate status update then retry updating newest
                sql(f"DELETE FROM messages WHERE key_id='{key_id}' AND key_remote_jid IS NOT 'status@broadcast'")
                sql(f"UPDATE messages SET key_remote_jid='{key_remote_jid}' WHERE _id={_id}")
    return (count, size)


ap = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="""\
Presents status updates as regular WhatsApp messages to allow for storing statu\
ses to view at your own time and/or allowing finer control of which statuses ge\
t downloaded.""",
    epilog="""\
Only one of these operations can be done at a time (disable, enable or clear), \
extra operations will be ignored. Enabling statuses only works if status is sti\
ll present on status roll, WhatsApp automatically removes disabled statuses aft\
er a while from status roll. The day option allows for integers or floats and d\
efaults to 1

Examples

%(prog)s -d                 disables statuses currently in status roll and saves as messages
%(prog)s -d -D 1            same as above, disables statuses within the past 24h
%(prog)s -d -m 4            disable videos alone (moves video statuses to messages)
%(prog)s -d -m 4 -D 0.0833  disable video statuses received from the past 0.0833 of a day (last 2 hrs)
%(prog)s -c                 clear all disabled statuses older than 24h
%(prog)s -e                 enable statuses previously disabled (moves them back to status roll)
%(prog)s -e -m 1            enable text statuses previously disabled (moves them back to status roll)
%(prog)s -e -m 1 -D 0.05    enable text statuses previously disabled within last 1.2 hrs
%(prog)s -c -m 3 -D 2       clear text and image statuses older than 2 days

Disabled statuses can be found here {}

Built by lordfme (https://github.com/lordfme/whatsapp)""".format(
        ", ".join(
            map(
                lambda x: "http://wa.me/" + x.strip("@s.whatsapp.net"),
                status_mime_pool.values(),
            )
        )
    ),
)

ap.add_argument("-d", "--disable", action="store_true", help="Disable statuses")
ap.add_argument("-e", "--enable", action="store_true", help="Enable statuses")
ap.add_argument("-s", "--store", action="store_true", help="Store statuses")
ap.add_argument("-r", "--restore", action="store_true", help="Restore statuses")
ap.add_argument("-c", "--clear", action="store_true", help="Clear disabled statuses")
ap.add_argument("-u", "--unviewed", action="store_true", help="Only store unviewes statuses")
ap.add_argument("-M", "--muted", action="store_true", help="Also operate on muted statuses")
ap.add_argument("-D", "--days", default=1, type=float, help="Clear statuses older than D days ago, default 1")
ap.add_argument("-m", "--mode", default=7, type=int, help="Text (1), Images (2), Videos (4), sum to get mimetypes to operate on, default 7 (all)")
args = vars(ap.parse_args())

DB_DIR = DB_DIR if os.path.isdir(DB_DIR) else "./"
DB_FILE_MSGSTORE = DB_DIR + "msgstore.db"
DB_FILE_CHATSETT = DB_DIR + "chatsettings.db"

if os.path.isfile(DB_FILE_MSGSTORE) and os.path.isfile(DB_FILE_CHATSETT):
    if not args["muted"]:
        # Get muted contacts to add to whitelist
        conn_sett = sqlite3.connect(DB_FILE_CHATSETT)
        whitelist |= set([x[0].strip("@s.whatsapp.net") for x in conn_sett.cursor().execute("SELECT jid FROM settings WHERE status_muted=1").fetchall()])
        conn_sett.close()

    count, size, days = 0, 0, args["days"]
    PREV_DAY_MS = str(int(time.time() - (days * 24 * 3600))) + "000"
    mime_types = [mime_types[i] for i in range(3) if bin(args["mode"])[2:].zfill(3)[i] == "1"]
    mime_map = {
        "video/mp4": 'media_mime_type="video/mp4"',
        "image/jpeg": 'media_mime_type="image/jpeg"',
        None: "media_mime_type IS NULL",
    }
    able = "_id, key_remote_jid, key_id, media_mime_type, media_size, remote_resource"
    mimes = " OR ".join([mime_map[x] for x in mime_types])
    conn = sqlite3.connect(DB_FILE_MSGSTORE)
    sql = lambda cmd, all=True: getattr(conn.cursor().execute(cmd), "fetchall" if all else "fetchone")
    if args["disable"]:
        statuses = sql(f'SELECT {able} FROM messages WHERE key_remote_jid="status@broadcast" AND ({mimes}) AND key_from_me=0 AND timestamp > {PREV_DAY_MS}')()
        (count, size) = disable()
        conn.commit()
    elif args["store"]:
        statuses = sql(f'SELECT {able} FROM messages WHERE key_remote_jid="status@broadcast" AND ({mimes}) AND key_from_me=0 AND timestamp > {PREV_DAY_MS}')()
        (count, size) = store()
        conn.commit()
    else:
        ap.print_help()
    conn.close()
    print("Done, processed %d statuses of size %.2fMB" % (count, size / 1000000.0))
else:
    print("msgstore.db and/or chatsettings.db file not found, place in current directory or specify in DB_DIR")
