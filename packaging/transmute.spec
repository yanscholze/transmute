%global debug_package %{nil}
# Frozen payload is already compressed; avoid costly recompression at level 19.
%global _binary_payload w3.zstdio
# Do not strip a PyInstaller onefile: its appended runtime must remain intact.
%global __os_install_post %{nil}
Name: transmute
Version: %{app_version}
Release: 1%{?dist}
Summary: Conversor desktop de bases para importação
License: LicenseRef-NotSpecified
URL: https://github.com/yanscholze/transmute
Source0: payload.tar.gz
Source1: transmute.sh
Source2: transmute.desktop
Source3: transmute.svg
BuildArch: x86_64
AutoReqProv: no
# Runtime Python/Qt is bundled; these are the host's graphical/system libraries.
Requires: /bin/sh, glibc >= 2.43, libstdc++, zlib, glib2, dbus-libs
Requires: libX11, libXext, libXrender, libXi, libxcb, libxkbcommon, libxkbcommon-x11
Requires: xcb-util-cursor, xcb-util-image, xcb-util-keysyms, xcb-util-renderutil, xcb-util-wm
Requires: mesa-libGL, mesa-libEGL, fontconfig, freetype

%description
Transmute organiza importações, modelos, regras e revisão de dados localmente.
Inclui runtime e modelos vazios. Preferências e dados ficam no diretório do
usuário e são preservados na remoção/atualização do aplicativo.

%prep
%setup -q -n payload

%build
# The payload was already compiled and tested on the native Linux runner.

%install
mkdir -p %{buildroot}/opt/transmute
cp -a . %{buildroot}/opt/transmute/
install -D -m 0755 %{SOURCE1} %{buildroot}/usr/bin/transmute
install -D -m 0644 %{SOURCE2} %{buildroot}/usr/share/applications/transmute.desktop
install -D -m 0644 %{SOURCE3} %{buildroot}/usr/share/icons/hicolor/scalable/apps/transmute.svg

%files
/opt/transmute
/usr/bin/transmute
/usr/share/applications/transmute.desktop
/usr/share/icons/hicolor/scalable/apps/transmute.svg

%changelog
* Thu Oct 22 2026 Transmute <https://github.com/yanscholze/transmute> - 1.2.0-1
- First native RPM installer; preserve per-user state on removal.
