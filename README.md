# WhatsApp Utilities

Bunch of utilities I hacked together to achieve some goal at some point or other. Mostly random, will update as I make more.

Sadly some lost to time and may stumble across and upload in the future.

Requirements / Dependencies
---

* Make sure [Termux](https://play.google.com/store/apps/details?id=com.termux&hl=en_US) is installed and root access available
* Open Termux and run **pkg install tsu** to allow root execution of scripts
* Install git as well to clone this repo **pkg install git**
* Also install python if not installed **pkg install python**
* Clone repo **git clone https://github.com/lordfme/whatsapp**
* **tsu -c whatsapp/script.py** (replace script.py with name of script to run)

Or run these lines on Termux in turn

>
    pkg install git tsu python
    git clone https://github.com/lordfme/whatsapp
    cd whatsapp
    ln -s consensual_contacts.py ../consensual_contacts.py
    ln -s vid_status.py ../vid_status.py
    cd ..
    tsu -c ./consensual_contacts.py
    tsu -c ./vid_status.py
    

Consensual Contacts
----
To display contacts who saved your number which you haven't saved in return and vice versa.

Useful to increase statuses you receive.


Vid Status
---
For disabling and enabling received WhatsApp video status broadcasts.

Ensure DB_DIR is correct and edit whitelist set to include numbers you want unaffected then run.


    usage: vid_status.py [-h] [-d] [-e] [-c] [-D DAYS] [-m MODE]

    Presents status updates as regular WhatsApp messages to allow for storing statuses to view at your own time and/or allowing finer control of which statuses get downloaded.

    optional arguments:
      -h, --help            show this help message and exit
      -d, --disable         Disable statuses
      -e, --enable          Enable statuses
      -c, --clear           Clear disabled statuses
      -D DAYS, --days DAYS  Clear statuses older than D days ago, default 1
      -m MODE, --mode MODE  Text (1), Images (2), Videos (4), sum to get mimetypes
                            to operate on, default 7 (all)

    Only one of these operations can be done at a time (disable, enable or clear), extra operations will be ignored. Enabling statuses only works if status is still present on status roll, WhatsApp automatically removes disabled statuses after a while from status roll. The day option allows for integers or floats and defaults to 1

    Examples

    vid_status.py -d                 disables statuses currently in status roll and saves as messages
    vid_status.py -d -D 1            same as above, disables statuses within the past 24h
    vid_status.py -d -m 4            disable videos alone (moves video statuses to messages)
    vid_status.py -d -m 4 -D 0.0833  disable video statuses received from the past 0.0833 of a day (last 2 hrs)
    vid_status.py -c                 clear all disabled statuses older than 24h
    vid_status.py -e                 enable statuses previously disabled (moves them back to status roll)
    vid_status.py -e -m 1            enable text statuses previously disabled (moves them back to status roll)
    vid_status.py -e -m 1 -D 0.05    enable text statuses previously disabled within last 1.2 hrs
    vid_status.py -c -m 3 -D 2       clear text and image statuses older than 2 days

    Disabled statuses can be found here http://wa.me/2348033831003, http://wa.me/2348083454312, http://wa.me/2347053205090
