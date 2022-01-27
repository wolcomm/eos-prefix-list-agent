# set binary rpm compression to xz-level2, for compatibility with
# the `librpm` version shipped with eos 4.26
%global _binary_payload w2.xzdio

Name:           eos-prefix-list-agent-cli
Version:        %{_version}
Release:        0%{?dist}
Summary:        CLI extension package for EOS Prefix List Agent

License:        MIT
URL:            https://github.com/wolcomm/eos-prefix-list-agent
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python2-devel

%global _description %{expand:
An EOS SDK based agent that maintains up-to-date prefix-list policy objects for
use in EOS routing policy configurations, based on data in the IRR.

This package provides the CLI extension implementation.
}

%description %_description


%prep
%autosetup -p1 -n eos-prefix-list-agent-cli-%{version}


%build
# override the provided build macro to use `pip` instead of `setup.py`
%global py2_build_wheel() %{expand:\\\
  sleep 1
  CFLAGS="${CFLAGS:-${RPM_OPT_FLAGS}}" LDFLAGS="${LDFLAGS:-${RPM_LD_FLAGS}}"\\\
  %{__python2} -m pip wheel -w dist/ .
  sleep 1
}
%py2_build_wheel


%install
%py2_install_wheel eos_prefix_list_agent_cli-%{version}-py2-none-any.whl
mkdir -p %{buildroot}/%{_datadir}/CliExtension
mkdir -p %{buildroot}/%{python2_sitelib}/CliPlugin
ln -s %{python2_sitelib}/prefix_list_agent_cli/extension.yaml %{buildroot}%{_datadir}/CliExtension/PrefixListAgent.yaml
ln -s %{python2_sitelib}/prefix_list_agent_cli/extension.py %{buildroot}%{python2_sitelib}/CliPlugin/PrefixListAgent.py


%check


%files -n eos-prefix-list-agent-cli
%doc README.md
%license LICENSE
%{python2_sitelib}/eos_prefix_list_agent_cli-%{version}.dist-info/
%{python2_sitelib}/prefix_list_agent_cli/
%{python2_sitelib}/CliPlugin/PrefixListAgent.py
%{_datadir}/CliExtension/PrefixListAgent.yaml


%changelog
* Tue May 9 2021 Ben Maddison <benm@workonline.africa>
-
