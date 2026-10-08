Name:           nimvex
Version:        0.1.0
Release:        1%{?dist}
Summary:        Nimvex web browser
License:        LicenseRef-Nimvex
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires: python3-devel
BuildRequires: desktop-file-utils
Requires:      python3
Requires:      python3-pyside6 >= 6.11.2
Requires:      dnf5
Requires:      PackageKit
Requires:      polkit

%description
Nimvex web browser with application-menu integration and project assets.
Includes an RPM-aware updater and official signed-repository configuration.
Updates require user approval and system authorization.

%prep
%setup -q

%build

%install
install -d %{buildroot}%{_datadir}/nimvex/assets
install -m 0644 browser.py nimvex_rpm_updater.py %{buildroot}%{_datadir}/nimvex/
install -m 0644 assets/* %{buildroot}%{_datadir}/nimvex/assets/
install -D -m 0755 nimvex %{buildroot}%{_bindir}/nimvex
install -D -m 0644 nimvex.desktop %{buildroot}%{_datadir}/applications/nimvex.desktop
install -D -m 0644 assets/nimvex.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/nimvex.png
install -D -m 0644 nimvex.repo %{buildroot}%{_sysconfdir}/yum.repos.d/nimvex.repo
install -D -m 0644 RPM-GPG-KEY-nimvex %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-nimvex

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/nimvex.desktop

%files
%license License
%{_bindir}/nimvex
%{_datadir}/nimvex/
%{_datadir}/applications/nimvex.desktop
%{_datadir}/icons/hicolor/256x256/apps/nimvex.png
%config(noreplace) %{_sysconfdir}/yum.repos.d/nimvex.repo
%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-nimvex

%changelog
* Thu Oct 08 2026 HexandRoach <Hexandroach@protonmail.com> - 0.1.0-1
- Package the RPM updater, desktop integration, assets, and release license.
- Include the official repository configuration and public signing key.
