#ble install
sudo apt-get install -y libbluetooth-dev bluez
sudo apt-get install -y python-dev python3-dev python3-setuptools python3-pip
sudo pip-3.2 install pybluez
sudo apt-get install -y python3-mysql.connector
sudo apt-get install -y vim
sudo apt-get update && sudo apt-get upgrade

#preparation for emoncms install
sudo apt-get install -y apache2 mysql-server mysql-client php5 libapache2-mod-php5 php5-mysql php5-curl php-pear php5-dev php5-mcrypt php5-common php5-redis git-core redis-server build-essential ufw ntp
sudo pear channel-discover pear.swiftmailer.org
sudo pecl install channel://pecl.php.net/dio-0.0.6 redis swift/swift
sudo sh -c 'echo "extension=dio.so" > /etc/php5/apache2/conf.d/20-dio.ini'
sudo sh -c 'echo "extension=dio.so" > /etc/php5/cli/conf.d/20-dio.ini'
sudo sh -c 'echo "extension=redis.so" > /etc/php5/apache2/conf.d/20-redis.ini'
sudo sh -c 'echo "extension=redis.so" > /etc/php5/cli/conf.d/20-redis.ini'
sudo nano /etc/apache2/apache2.conf
sudo ln -s ../mods-available/rewrite.load /etc/apache2/mods-enabled/rewrite.load
sudo systemctl restart apache2
sudo chown -R pi /var/www
cd /var/www && git clone -b stable https://github.com/emoncms/emoncms.git
mysql -u root -p <<EOF
create database emoncms;
create user 'emoncms'@'localhost' identified by 'new_secure_password';
grant all on emoncms.* to 'emoncms'@'localhost';
flush privileges;
exit
EOF

#create data repositories for emoncms feed engines
sudo mkdir /var/lib/{phpfiwa,phpfina,phptimeseries}
sudo mkdir /var/lib/phpfiwa
sudo mkdir /var/lib/phpfina
sudo mkdir /var/lib/phptimeseries

#set permissions
sudo chown www-data:root /var/lib/{phpfiwa,phpfina,phptimeseries}
sudo chown www-data:root /var/lib/phpfiwa
sudo chown www-data:root /var/lib/phpfina
sudo chown www-data:root /var/lib/phptimeseries

#configure emoncms database settings
cd /var/www/emoncms && cp default.settings.php settings.php
nano settings.php

cd /var/www/html && sudo ln -s /var/www/emoncms

sudo touch /var/log/emoncms.log
sudo chmod 666 /var/log/emoncms.log
