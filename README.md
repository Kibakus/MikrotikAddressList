# MikrotikAddressList

======INSTALL(Deb/Ubunt)=======
sudo apt install -y geany			(editor python)
sudo apt install -y python3-pip		(python3 + pip3)
pip3 install flask					(web)
pip3 install flask-login			(web login)
pip3 install passlib				(sha256)
pip3 install paramiko				(SSH connect)
pip3 install arpreq					(MAC find)
pip3 install dnspython				(nslookup)
===============================


=========Start(MANUAL)=========
python3 /home/ipadd/web.py
===============================


===========Edit Base===========
python3 /home/ipadd/base.py
===============================


====Create Daemon(AutoRun)=====

Nano(Vim) /etc/systemd/system/ipadd.service

"""START"""
[Unit]
Description=telebot
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/ipadd/web.py -s
TimeoutStartSec=0
Restart=always
RestartSec=60

[Install]
WantedBy=default.target
"""END"""

===============================


============Daemon=============
systemctl restart ipadd.service		(restart)
systemctl start ipadd.service		(Start)
systemctl enable ipadd.service		(ON AutoRun)
systemctl disable ipadd.service		(OFF AutoRun)
systemctl status ipadd.service		(STATUS AutoRun)
===============================


==============URL==============
http://192.168.10.29:10000
utp-inet:10000
===============================
© 2021 GitHub, Inc.
