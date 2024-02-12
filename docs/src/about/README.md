# About

**EOS Prefix List Agent** is an extension to Arista EOS that automatically
maintains BGP prefix-list filters based on IRR data.

The on-device agent based design integrates tightly with native EOS interfaces,
and keeps the contents of `prefix-list`s out of the `running-configuration`
which solves several operational challenges.

This has been used in production at [Workonline Communications (AS37271)][Workonline]
since 2019.

[Workonline]: https://workonline.africa
