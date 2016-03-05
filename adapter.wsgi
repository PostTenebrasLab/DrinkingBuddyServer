#!/usr/bin/python3

import sys

sys.path.insert(0, '/path/to/drinkingbuddy/')

from drinkingbuddy import app as application

### Example configuration for apache 2 webserver ###
#<VirtualHost *:80>
#        ServerName drinkingbuddy.lan.posttenebraslab.ch
#
#        WSGIDaemonProcess drinkingbuddy user=www-data group=www-data processes=1 threads=1
#        WSGIScriptAlias / /data/www_app/drinkingbuddy/adapter.wsgi
#
#        <Directory /data/www_app/drinkingbuddy>
#                WSGIProcessGroup drinkingbuddy
#                WSGIApplicationGroup %{GLOBAL}
#                Order deny,allow
#                Allow from all
#                Require all granted
#        </Directory>
#
#        ErrorLog /var/log/apache2/drinkingbuddy.posttenebraslab.ch-error.log
#        CustomLog /var/log/apache2/drinkingbuddy.posttenebraslab.ch-access.log combined
#
#</VirtualHost>
####
