# WhatsApp Utilities

Bunch of utilities I hacked together to achieve some goal at some point or other. Mostly random, will update as I make more.

Sadly some lost to time and may stumble across and upload in the future.

Requirements / Dependencies
---

* Make sure Termux is installed and root access available
* **pkg install tsu** in Termux to allow root execution of scripts
* Most scripts are written by default in python 2.7 but should work with 3 with little to no changes
* Modify the shebang to suit your python install, for Termux this should be **/data/data/com.termux/files/usr/bin/env python2** alternatively just run  with **python2 script.py [args]**
* Place script.py in Termux home directory, cd to home dir and run **chmod 755 script.py** to enable execution
* **tsu -c ./script.py** or **tsu -c python2 ./script.py**

Consensual Contacts
----
For viewing contacts who saved your number which you haven't saved in return and vice versa.

Useful to increase statuses you receive.

Place python script consensual_contacts.py in same folder as axolotl.db and wa.db then run. (Script in Py 2.7).


Vid Status
---
For disabling and enabling WhatsApp video status broadcasts.

Ensure DB_DIR is correct and edit whitelist set to include numbers you want unaffected then run. (Script both 2 and 3 compatible)
