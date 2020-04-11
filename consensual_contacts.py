import sqlite3

conn=sqlite3.connect("axolotl.db")
status_cands = set([str(x[0]) for x in conn.cursor().execute('SELECT sender_id FROM sender_keys WHERE group_id="status@broadcast"').fetchall()])

conn=sqlite3.connect("wa.db")
listed_contacts = set([str(x[0].strip("@s.whatsapp.net")) for x in conn.cursor().execute('SELECT jid FROM wa_contacts WHERE sort_name IS NOT NULL').fetchall()])

not_saved_by_me = status_cands - listed_contacts

not_saved_by_them = listed_contacts - status_cands

def resolve_wa_name(num):
    num += "@s.whatsapp.net"
    result = conn.cursor().execute('SELECT wa_name FROM wa_contacts WHERE jid=?',(num,)).fetchone()
    if result and result[0]:
        return result[0]
    return False

print "<===============================NOT SAVED BY ME==============================>"
for num in not_saved_by_me:
    name = resolve_wa_name(num)
    if name:
        print name.encode("ascii","ignore"), "wa.me/"+num

print "<===============================NOT SAVED BY THEM============================>"
for num in not_saved_by_them:
    name = resolve_wa_name(num)
    if name:
        print name.encode("ascii","ignore"), "wa.me/"+num
