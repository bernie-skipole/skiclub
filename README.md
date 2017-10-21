# README #

skiclub is a 'skipole' project.

Allows users to log in as members or administrators, and admin's can create further users.

As a stand-alone project it does little else! It is intended to be imported into the skipole framework, copied and adapted as required, to be the basis of a users own project.

**Installation with manual start**

Download the latest version of the skiclub tar file from the Downloads section, and uncompress it into a directory of your choice.

Within the directory, use python3 to run the file:

sudo python3 \_\_main\_\_.py -p 80

and this will run the web server. You will be able to connect to it from a browser.

**Optionally use the Waitress web server**

As default \_\_main\_\_.py uses the python library wsgiref server, however if you have the package 'python3-waitress' installed using:

sudo apt-get install python3-waitress

The script can be run with the -w option, which uses the Waitress web server.

sudo python3 \_\_main\_\_.py -w -p 80

Note: this project, and the skipole web framework, is not associated with the Waitress web server project, the option is included because, in our opinion, it seems a good fit.

**Redis**

The code is dependent on a Redis server being available and the Python3 Redis client package being installed.

The python3 redis client:

sudo apt-get install python3-redis

**Installation with automatic boot up**

Download the latest version of the tar file from the Downloads section, and uncompress it into /opt, creating directory:

/opt/skiclub/

Give the directory and contents root ownership

sudo chown -R root:root /opt/skiclub

Then create a file :

/lib/systemd/system/skiclub.service

containing the following:


    [Unit]
    Description=My project description
    After=multi-user.target

    [Service]
    Type=idle
    ExecStart=/usr/bin/python3 /opt/skiclub/__main__.py -w -p 80

    WorkingDirectory=/opt/skiclub
    Restart=on-failure

    # Connects standard output to /dev/null
    StandardOutput=null

    # Connects standard error to journal
    StandardError=journal

    [Install]
    WantedBy=multi-user.target

You will notice the -w option uses Waitress, remove the option if you just wish to use the wsgiref server. However we recommend Waitress as it is a multi threaded server.

Then set permissions of the file

sudo chown root:root /lib/systemd/system/skiclub.service

sudo chmod 644 /lib/systemd/system/skiclub.service


Enable the service

sudo systemctl daemon-reload

sudo systemctl enable myproj.service

This starts /opt/skiclub/\_\_main\_\_.py serving on port 80 on boot up.

Useful functions to test the service:

sudo systemctl start skiclub

sudo systemctl stop skiclub

sudo systemctl restart skiclub

sudo systemctl status skiclub

sudo systemctl disable skiclub

Display last lines of the journal

sudo journalctl -n

Display and continuously print the latest journal entries

sudo journalctl -f

**Security**

Using these instructions the service will be running as root, and the password authentication is unencrypted. These factors are considered unsafe on the internet.

For further security consider using the wsgi function with ngix and uwsgi, see the skipole framework wiki for examples.

The project uses a redis server, with details, including password, set in the file cfg.py. You would generally run this server on the same machine with localhost access only.

**Further Development**

To further develop the web pages you need to be familiar with the skipole.py framework, and import the project, make a copy and develop it within the framework.

