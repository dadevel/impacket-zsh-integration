# Impacket ZSH Integration

![Screenshot](./assets/screenshot.png)

A bunch of scripts to reduce friction when pentesting Active Directory from Linux.

# Setup

Clone the repository.

~~~ bash
git clone --depth 1 https://github.com/dadevel/impacket-zsh-integration.git ~/.local/share/impacket-zsh-integration
~~~

Append the following snippet to your `~/.zshrc`:

~~~ bash
source ~/.local/share/impacket-zsh-integration/krbconf.zsh
source ~/.local/share/impacket-zsh-integration/proxyconf.zsh
~~~

Find your [Powerlevel10k](https://github.com/romkatv/powerlevel10k) config and modify it to look something like this:

~~~ bash
...
() {
    ...
    typeset -g POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(
        ...
        krbconf
        proxyconf
    )

    source ~/.local/share/impacket-zsh-integration/powerlevel10k.zsh
    ...
}()
...
~~~

Configure your terminal to use [Nerd Fonts](https://www.nerdfonts.com/) or change the icons in [powerlevel10k.zsh](./powerlevel10k.zsh).

# Usage

Configure a SOCKS proxy in the current shell with the help of [proxychains-ng](https://github.com/rofl0r/proxychains-ng).
The network traffic of following commands will be tunneled over the proxy.

~~~ bash
proxyconf set socks5 127.0.0.1 1080
nc -vz dc01.corp.local 445
~~~

Stop tunneling traffic over the proxy.

~~~ bash
proxyconf unset
~~~

Tell subsequent tools to use a specific Kerberos TGT or ST by setting the `$KRB5CCNAME` environment variable.

~~~ bash
krbconf set ./jdoeadm.ccache
impacket-smbclient -k -no-pass srv01.corp.local
~~~

If you additionally specify the hostname or FQDN of a domain controller with `-K` / `--kdc`, a suitable `$KRB5_CONFIG` is configured in the environment as well (thanks [@mpgn](https://twitter.com/mpgn_x64/status/1881252755131760659) for the idea).
This is required for certain tools like [evil-winrm](https://github.com/Hackplayers/evil-winrm).

~~~ bash
krbconf set ./jdoeadm.ccache -K dc01
evil-winrm -r $KRB5CCNAME_DOMAIN -i srv01.corp.local
~~~

Stop using the ticket.

~~~ bash
krbconf unset
~~~

Execute a one-off command in the context of a given ticket.

~~~ bash
krbconf exec ./jdoeadm.ccache impacket-smbclient -k -no-pass srv01.corp.local
~~~

Import a ticket in Kirbi format from Windows (e.g. from [Rubeus](https://github.com/GhostPack/Rubeus)).

~~~ bash
krbconf import ./jdoe.kirbi
krbconf import base64:doIFrTCCBamgAwIB...
~~~
