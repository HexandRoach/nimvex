Name:           nimvex
Version:        0.0.0
Release:        0.1.test%{?dist}
Summary:        Experimental Nimvex web browser
License:        LicenseRef-Nimvex
Source0:        nimvex-0.0.0.tar.gz
BuildArch:      noarch
BuildRequires: python3-devel
BuildRequires: desktop-file-utils
Requires:      python3
Requires:      python3-pyside6 >= 6.11.2

%description
Local test package of the experimental Nimvex browser.
Includes application-menu integration and project assets.
In-browser Git updates are disabled in this package.

%prep
%setup -q

%build

%install
install -d %{buildroot}%{_datadir}/nimvex/assets
install -m 0644 browser.py %{buildroot}%{_datadir}/nimvex/
install -m 0644 assets/* %{buildroot}%{_datadir}/nimvex/assets/

install -D -m 0755 nimvex %{buildroot}%{_bindir}/nimvex
install -D -m 0644 nimvex.desktop %{buildroot}%{_datadir}/applications/nimvex.desktop
install -D -m 0644 assets/nimvex.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/nimvex.png

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/nimvex.desktop

%files
%license License
%{_bindir}/nimvex
%{_datadir}/nimvex/
%{_datadir}/applications/nimvex.desktop
%{_datadir}/icons/hicolor/256x256/apps/nimvex.png
