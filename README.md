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
The network traffic of all following commands will be tunneled over the proxy.

~~~ bash
proxyconf set socks5 127.0.0.1 1080
nc -v dc01.corp.local 445
~~~

Stop tunneling traffic over the proxy.

~~~ bash
proxyconf unset
~~~

Tell subsequent tools to use a specific Kerberos ticket by setting the `$KRB5CCNAME` environment variable.

~~~ bash
krbconf set ./jdoeadm.ccache
impacket-smbclient -k -no-pass srv01.corp.local
~~~

Stop using the ticket.

~~~ bash
krbconf unset
~~~

Import a ticket in Kirbi format from Windows (e.g. from [Rubeus](https://github.com/GhostPack/Rubeus)).

~~~ bash
krbconf import ./jdoe.kirbi
krbconf import base64:doIFrTCCBamgAwIB...
~~~
