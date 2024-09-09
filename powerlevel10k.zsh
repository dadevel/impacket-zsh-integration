function prompt_krbconf() {
    if [[ -e "$KRB5CCNAME" && -n "$KRB5CCNAME_DOMAIN" && -n "$KRB5CCNAME_USER" ]]; then
        if [[ -n "$KRB5CCNAME_HOST" ]]; then
            p10k segment -f 4 -i '' -t "$KRB5CCNAME_DOMAIN/$KRB5CCNAME_USER@$KRB5CCNAME_HOST"
        else
            p10k segment -f 4 -i '' -t "$KRB5CCNAME_DOMAIN/$KRB5CCNAME_USER"
        fi
    fi
}

function prompt_proxyconf() {
    declare -r netns="$(ip netns identify)"
    if [[ -n "$PROXYCHAINS_ENDPOINT" ]]; then
        declare -r proxy="$PROXYCHAINS_ENDPOINT"
    elif [[ "$LD_PRELOAD" == */usr/lib/libproxychains4.so* ]]; then
        declare -r proxy='proxychains'
    else
        declare -r proxy=''
    fi
    if [[ -n "${netns}" && -n "${proxy}" ]]; then
        p10k segment -f 2 -i '' -t "${proxy}@${netns}"
    elif [[ -n "${netns}" ]]; then
        p10k segment -f 2 -i '' -t "${netns}"
    elif [[ -n "${proxy}" ]]; then
        p10k segment -f 2 -i '' -t "${proxy}"
    fi
}
