# set binary rpm compression to xz-level2, for compatibility with
# the `librpm` version shipped with eos 4.26
%global _binary_payload w2.xzdio

Name:           eos-prefix-list-agent-cli
Version:        %{_version}
Release:        0%{?dist}
Summary:        Foo

License:        MIT
URL:            https://github.com/wolcomm/eos-prefix-list-agent
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python2-devel

%global _description %{expand:
An EOS SDK based agent that maintains up-to-date prefix-list policy objects for
use in EOS routing policy configurations, based on data in the IRR.

The agent will periodically check the running configuration of the device to
gather a list of prefix-lists that it is responsible for maintaining. It will
then retrieve the required data from the IRR via an RPTK web service, and
update the prefix-lists without calling the EOS config parser.
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


%check


%files -n eos-prefix-list-agent-cli
%doc README.*
%license LICENSE*
%{python2_sitelib}/eos_prefix_list_agent_cli-%{version}.dist-info/
%{python2_sitelib}/prefix_list_agent_cli/


%changelog
* Tue May 9 2021 Ben Maddison <benm@workonline.africa>
-
