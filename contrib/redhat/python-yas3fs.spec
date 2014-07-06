%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%global	upstream_name	yas3fs
%define	yas3fs_logdir	%{_localstatedir}/log/yas3fs

Name:			python-%{upstream_name}
Version:		2.2.16
Release:		4%{?dist}
Summary:		AWS S3 Filesystem

Group:			Development/Languages
License:		MIT
URL:			https://github.com/danilop/yas3fs
Source0:		https://pypi.python.org/packages/source/y/%{upstream_name}/%{upstream_name}-%{version}.tar.gz
Source1:		yas3fs.init
Source2:		yas3fs.sysconfig

Patch1:			yas3fs-fuse-doc.patch

BuildRoot:		%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:		noarch
BuildRequires:	python-devel

Requires:		python-argparse
# yas3fs "python requires" file says that python-setuptools 2.2 is needed. EL6 does not come with this version.
# It works with 0.6.10 too
Requires:		python-setuptools >= 0.6.10
Requires:		python-boto >= 2.25.0
Requires:		python-fusepy >= 2.0.2
Requires:		fuse, fuse-libs


%description
YAS3FS (Yet Another S3-backed File System) is a
Filesystem in Userspace (FUSE) interface to Amazon S3.

%prep
%setup -q -n %{upstream_name}-%{version}

# Create readme file for fuse
%patch1 -p1 -b .fusedoc

%build
%{__python2} setup.py build

%install
rm -rf %{buildroot}
%{__python2} setup.py install -O1 --skip-build --root %{buildroot}

# Install data directory
install -d -m 770 %{buildroot}%{_var}/lib/%{upstream_name}

# install the init script options file
install -d -m 755 $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig
install -m 640 %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/yas3fs

# install SYSV init stuff
install -d -m 755 $RPM_BUILD_ROOT/etc/rc.d/init.d
install -m 755 %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/yas3fs

# install log directory
install -d -m 755 $RPM_BUILD_ROOT%{yas3fs_logdir}

%pre
export YAS3FSUSER=%{upstream_name}
echo -n "Check %{upstream_name} user ... "
if id $YAS3FSUSER >/dev/null 2>&1; then
    echo "$YAS3FSUSER exists."
    # update home dir
    usermod -d /var/lib/%{upstream_name} $YAS3FSUSER
else
    useradd $YAS3FSUSER -r -d /var/lib/%{upstream_name}/ -s /sbin/nologin -c 'system user for %{upstream_name}' && echo "$YAS3FSUSER added."
fi

# yas3fs user needs to be in the fuse group in oder to execute fusermount
%{_bindir}/gpasswd -a yas3fs fuse 1>&2 > /dev/null || :

%post
/sbin/chkconfig --add %{upstream_name}

%preun
if [ $1 = 0 ]; then
        /sbin/service %{upstream_name} stop > /dev/null 2>&1 || :
        /sbin/chkconfig --del %{upstream_name}
fi

%postun
if [ $1 = 0 ]; then
        userdel %{upstream_name} > /dev/null 2>&1 || :
fi

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc README.fuse
#%doc CHANGES LICENSE README.md
%config %{_sysconfdir}/rc.d/init.d/yas3fs
%config(noreplace) %{_sysconfdir}/sysconfig/yas3fs
%{_bindir}/yas3fs
%{python2_sitelib}/%{upstream_name}
%{python2_sitelib}/%{upstream_name}-%{version}-*.egg-info

%defattr(-,root,yas3fs,-)
%attr(0770,root,yas3fs) %dir %{_var}/lib/%{upstream_name}
%attr(0770,-,-) %dir %{yas3fs_logdir}
%attr(0660,-,-) %config(noreplace) %{_sysconfdir}/sysconfig/%{upstream_name}

%changelog
* Sun Jul 06 2014 Marco Schirrmeister <marco@schirrmeister.net> - 2.2.16-4
- Added checks to the init script for minimum config and permissions
- Added readme file for fuse

* Sat Jul 05 2014 Marco Schirrmeister <marco@schirrmeister.net> - 2.2.16-3
- Added init script
- Added system user
- Added basic configuration file
- Added data directory in /var/lib
- Added log directory

* Fri Jul 04 2014 Marco Schirrmeister <marco@schirrmeister.net> - 2.2.16-2
- Added rhel dependency for python sitelib/sitearch based on a epel python package
- Added package dependencies

* Fri Jul 04 2014 Marco Schirrmeister <marco@schirrmeister.net> - 2.2.16-1
- Initial build

