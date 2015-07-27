## Project 5 Details

This readme is to serve as reference for graders of project 5 for udacity's full stack series.

### Login information
The udacity virtual machine to log into is at ip address - 52.11.104.202.
The SSH port is 2200 as requested in the project specifications.
You can use the key in the notes to ssh as user grader on the machine.

### URL of hosted application
The catalog application is hosted at / on the machine.
You can use http://52.11.104.202/ to visit it.

### Changes made to VM

1. A new user named grader was created with a password included in the notes section
```bash
useradd -d /home/grader -m grader
passwd grader
```
2. User grader was granted sudo by adding the user to sudo group
```bash
usermod -a -G sudo grader
```
4. Upgraded all installed packages and fetched new ones
```bash
apt-get update
apt-get upgrade
apt-get dist-upgrade
```
5. SSH port was changed from 22 and 2200
6. Configured the Uncomplicated Firewall (UFW) to only allow incoming connections 
for SSH (port 2200), HTTP (port 80), and NTP (port 123)
```bash 
ufw status
Status: active
To                         Action      From
--                         ------      ----
2200/tcp                   ALLOW       Anywhere
80                         ALLOW       Anywhere
123                        ALLOW       Anywhere
2200/tcp (v6)              ALLOW       Anywhere (v6)
80 (v6)                    ALLOW       Anywhere (v6)
123 (v6)                   ALLOW       Anywhere (v6)
```
This was done by ufw commands to delete existing rules and add new rules for the 3 ports in questions, while also
restarting the ssh service to pickup the changes
7. Configured the local timezone to UTC. This was done via the command below and following the visual instructions of the
utility.
```bash
dpkg-reconfigure tzdata
```
8. Installed and configured Apache to serve a Python mod_wsgi application
```bash
apt-get install apache2
apt-get install libapache2-mod-wsgi
service apache2 restart
a2enmod #to enable mod_wsgi via prompt
```
9. Installed and configured PostgreSQL
--*. Installation
```bash
apt-get install postgresql
service postgresql start
```
--*. Disabled remote connections - this is disabled by default
--*. Created a new user named catalog_admin that has limited permissions to the catalog application database
Note: The use is named catalog_admin to avoid confusion with the name of the project, which was catalog from before
```bash
su - postgres
createuser -dRS catalog_admin
su catalog_admin -c 'createdb'
passwd catalog_admin
# restrict user to catalog_live database only
vim /etc/postgresql/9.3/main/pg_hba.conf
service postgresql restart
service apache2 restart
```
10. Installed git, cloned and setup my Catalog App project (from your GitHub repository from earlier in the Nanodegree program) 
so that it functions correctly when visiting your server’s IP address in a browser.
--*. Installation and repository cloning
```bash
apt-get install git
git clone https://github.com/mozuk/udacity
```
--*. Installation of dependencies for the catalog application
```bash
apt-get install pip
apt-get install python-dev # needed for some packages
 pip install -r ./udacity/catalog/requirements.txt
```
--*. Configuration changes to make it run with apache2
```bash
# inserted enviromental variables needed into apache global vars
vim /etc/apache2/envvars
# created wsgi control script to launch application within apache2 
vim /home/catalog_admin/udacity/catalog/catalog.wsgi
# created site configuration for apache2 to run the wsgi script
vim /etc/apache2/sites-available/catalog.conf
# enabled site on apache2 instance
a2ensite
```

### Resources used

* http://manpages.ubuntu.com/ - Ubuntu documentation
* http://help.ubuntu.com - Ubuntu community
    * https://help.ubuntu.com/14.04/serverguide/serverguide.pdf
* http://stackoverflow.com/ - Stack Overflow
* http://www.postgresql.org/docs/ - Postgre Documentation