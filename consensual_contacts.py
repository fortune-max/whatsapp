#!/data/data/com.termux/files/usr/bin/env python

import sqlite3, os

DB_DIR = "/data/data/com.whatsapp/databases/"

def resolve_wa_name(num):
    num += "@s.whatsapp.net"
    result = conn.cursor().execute('SELECT wa_name FROM wa_contacts WHERE jid=?',(num,)).fetchone()
    if result and result[0]:
        return result[0]
    return False

if not os.path.exists(DB_DIR):
    DB_DIR = "./"

DB_FILE_WA = DB_DIR + "wa.db"
DB_FILE_AXOLOTL = DB_DIR + "axolotl.db"

if os.path.exists(DB_FILE_AXOLOTL) and os.path.exists(DB_FILE_WA):
    conn=sqlite3.connect(DB_FILE_AXOLOTL)
    status_cands = set([str(x[0]) for x in conn.cursor().execute('SELECT sender_id FROM sender_keys WHERE group_id="status@broadcast"').fetchall()])

    conn=sqlite3.connect(DB_FILE_WA)
    listed_contacts = set([str(x[0].strip("@s.whatsapp.net")) for x in conn.cursor().execute('SELECT jid FROM wa_contacts WHERE sort_name IS NOT NULL').fetchall()])

    not_saved_by_me = status_cands - listed_contacts

    not_saved_by_them = listed_contacts - status_cands

    print ("<===============================NOT SAVED BY ME==============================>")
    for num in not_saved_by_me:
        name = resolve_wa_name(num)
        if name:
            print (name.encode("ascii","ignore").decode() + " wa.me/"+num)

    print ("<===============================NOT SAVED BY THEM============================>")
    for num in not_saved_by_them:
        name = resolve_wa_name(num)
        if name:
            print (name.encode("ascii","ignore").decode() + " wa.me/"+num)

    conn.close()
else:
    print ("axolotl.db and/or wa.db file not found, place in current directory or specify in DB_DIR")
