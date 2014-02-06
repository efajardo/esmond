# Make sure that unpackaged files are noticed
%define _unpackaged_files_terminate_build      1

# Don't create a debug package
%define debug_package %{nil}

%define install_base /opt/esmond

%define init_script_1 espolld
%define init_script_2 espersistd
 
Name:           esmond
Version:        0.99       
Release:        1%{?dist}
Summary:        REPLACE
Group:          Development/Libraries
License:        REPLACE 
URL:            http://REPLACE
Source0:        http://REPLACE/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
AutoReqProv:	no
 
BuildRequires:  python
BuildRequires:  python-devel
BuildRequires:  python-setuptools
BuildRequires:  httpd

Requires:       mercurial
Requires:		wget
Requires:		python
Requires:		python-devel
Requires:		python-setuptools
Requires:       mod_wsgi
Requires:       httpd
Requires:		postgresql
Requires:		postgresql-devel
Requires:		sqlite
Requires:		sqlite-devel
Requires:		zlib-devel
Requires:		bzip2-devel
Requires:		openssl-devel
Requires:		ncurses-devel
Requires:		readline-devel
Requires:		tk-devel
Requires:		memcached
 
%description
Esmond is a system for collecting and storing large sets of SNMP data. Esmond
uses a hybrid model for storing data using TSDB for time series data and an SQL
database for everything else. All data is available via a REST style interface
(as JSON) allowing for easy integration with other tools.
 
%prep
%setup -q -n %{name}-%{version}

%build

%install
# Copy and build in place so that we know what the path in the various files
# will be
rm -rf %{buildroot}/%{install_base}
mkdir -p %{buildroot}/%{install_base}
cp -Ra . %{buildroot}/%{install_base}
cd %{buildroot}/%{install_base}

# Get rid of any remnants of the buildroot directory
find %{buildroot}/%{install_base} -type f -exec sed -i "s|%{buildroot}||" {} \;

# Move the default RPM esmond.conf into place
mv %{buildroot}/%{install_base}/rpm/config_files/esmond.conf %{buildroot}/%{install_base}/esmond.conf

# Move the init scripts into place
mkdir -p %{buildroot}/etc/init.d
mv %{buildroot}/%{install_base}/rpm/init_scripts/%{init_script_1} %{buildroot}/etc/init.d/%{init_script_1}
mv %{buildroot}/%{install_base}/rpm/init_scripts/%{init_script_2} %{buildroot}/etc/init.d/%{init_script_2}

# Move the apache configuration into place
mkdir -p %{buildroot}/etc/httpd/conf.d/
mv %{buildroot}/%{install_base}/rpm/config_files/apache-esdb.conf %{buildroot}/etc/httpd/conf.d/apache-esdb.conf

# Move the cron configuration into place
mkdir -p %{buildroot}/etc/cron.d/
mv %{buildroot}/%{install_base}/rpm/config_files/cron-generate_perfsonar_store_file %{buildroot}/etc/cron.d/cron-generate_perfsonar_store_file

# Move the apache mod_wsgi esdb CGI into place
mkdir -p %{buildroot}/%{install_base}/bin/
mv %{buildroot}/%{install_base}/rpm/bin/esdb_wsgi %{buildroot}/%{install_base}/bin/

# Get rid of the 'rpm' directory now that all the files have been moved into place
rm -rf %{buildroot}/%{install_base}/rpm

# XXX: For some reason, the DLNetSNMP gets installed into a subdirectory of the
# egg
for i in %{buildroot}/%{install_base}/bin/*; do
    sed -i 's/DLNetSNMP-\(.*\).egg/DLNetSNMP-\1.egg\/DLNetSNMP/' $i
done
 
%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%post
# Check for modern python and set up environment.
easy_install pip
pip install virtualenv
yum -y groupinstall "Development Tools"
mkdir -p /usr/local/src
if ! [ -a /usr/local/bin/python2.7 ] && 
	! [ -a /usr/bin/python2.7 ];
then
	echo "Installing alt python2.7"
	cd /usr/local/src
	wget http://python.org/ftp/python/2.7.6/Python-2.7.6.tgz
	tar zxvf Python-2.7.6.tgz
	cd /usr/local/src/Python-2.7.6
	./configure --prefix=/usr/local
	make && make altinstall
else
	echo "Python2.7 exists"
fi

cd %{install_base}
if [ -a /usr/local/bin/python2.7 ];
then
	virtualenv --prompt="(esmond)" --python=/usr/local/bin/python2.7 .
else
	virtualenv --prompt="(esmond)" --python=/usr/bin/python2.7 .
fi
. bin/activate
pip install -r requirements.txt
mkdir -p tsdb-data
touch tsdb-data/TSDB

# Create the 'esmond' user
/usr/sbin/groupadd esmond 2> /dev/null || :
/usr/sbin/useradd -g esmond -r -s /sbin/nologin -c "Esmond User" -d /tmp esmond 2> /dev/null || :

# Create the logging directories
mkdir -p /var/log/esmond
mkdir -p /var/log/esmond/crashlog
chown -R esmond:esmond /var/log/esmond

# Create the TSDB directory
mkdir -p /var/lib/esmond
touch /var/lib/esmond/TSDB
chown -R esmond:esmond /var/lib/esmond

# Create the 'run' directory
mkdir -p /var/run/esmond
chown -R esmond:esmond /var/run/esmond

%files
%defattr(-,root,root,-)
%{install_base}/*
/etc/init.d/%{init_script_1}
/etc/init.d/%{init_script_2}
/etc/httpd/conf.d
/etc/cron.d/cron-generate_perfsonar_store_file
 
%changelog
* Wed Apr 27 2011 Aaron Brown <aaron@internet2.edu> 1.0-1
- Initial Esmond Spec File
