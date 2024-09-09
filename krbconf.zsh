krbconf() {
    declare result
    if [[ -x /opt/archpkgs/impacket-stable/bin/python3 ]]; then
        declare -r python=/opt/archpkgs/impacket-stable/bin/python3
    else
        declare -r python=python3
    fi
    "${python}" ~/.local/share/impacket-zsh-integration/krbconf.py "$@" | read -r result && eval "${result}"
}

compdef "_arguments '1:first arg:(import export set unset whoami exec)' '::optional arg:_files'" krbconf
