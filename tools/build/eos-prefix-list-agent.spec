# set binary rpm compression to xz-level2, for compatibility with
# the `librpm` version shipped with eos 4.26
%global _binary_payload w2.xzdio

Name:           eos-prefix-list-agent
Version:        %{_version}
Release:        0%{?dist}
Summary:        Foo

License:        MIT
URL:            https://github.com/wolcomm/eos-prefix-list-agent
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros

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
%autosetup -p1 -n eos-prefix-list-agent-%{version}


%build
# override the provided build macro to use `build` instead of `pip`
%global pyproject_wheel_isolated() %{expand:\\\
    mkdir -p "%{_pyproject_builddir}"
    CFLAGS="${CFLAGS:-${RPM_OPT_FLAGS}}" LDFLAGS="${LDFLAGS:-${RPM_LD_FLAGS}}" TMPDIR="%{_pyproject_builddir}" \\\
    %{__python3} -m build --wheel --outdir %{_pyproject_wheeldir}
}
%pyproject_wheel_isolated


%install
%pyproject_install
%pyproject_save_files 'prefix_list_agent'


%check


%files -n eos-prefix-list-agent -f %{pyproject_files}
%doc README.*
%license LICENSE*
%{_bindir}/PrefixListAgent


%changelog
* Tue May 9 2021 Ben Maddison <benm@workonline.africa>
-
