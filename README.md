# WhatsApp Utilities

Bunch of utilities I hacked together to achieve some goal at some point or other. Mostly random, will update as I make more.

Sadly some lost to time and may stumble across and upload in the future.

Requirements / Dependencies
---

* Make sure [Termux](https://play.google.com/store/apps/details?id=com.termux&hl=en_US) is installed and root access available
* Open Termux and run **pkg install tsu** to allow root execution of scripts
* Also install python if not installed **pkg install python**
* Place script.py in Termux home directory and run **chmod 755 script.py** to enable execution
* **tsu -c ./script.py** or **tsu -c python ./script.py**
* Ensure shebang (first line) is correct if executing script directly without python fails, some Android versions use a different app directory scheme

Or run these lines on Termux in turn

>
    pkg install git tsu python
    git clone https://github.com/lordfme/whatsapp
    cd whatsapp
    chmod 755 *
    ln -s consensual_contacts.py ../consensual_contacts.py
    ln -s vid_status.py ../vid_status.py
    cd ..
    tsu -c ./consensual_contacts.py
    tsu -c ./vid_status.py

If incorrect shebang use this or fix shebang
>
    tsu -c python ./consensual_contacts.py
    tsu -c python ./vid_status.py
    

Consensual Contacts
----
To display contacts who saved your number which you haven't saved in return and vice versa.

Useful to increase statuses you receive.


Vid Status
---
For disabling and enabling received WhatsApp video status broadcasts.

Ensure DB_DIR is correct and edit whitelist set to include numbers you want unaffected then run.

