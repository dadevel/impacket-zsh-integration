proxyconf() {
    case "$#:$1" in
        4:set)
            declare -r protocol="$2"
            declare -r host="$3"
            declare -r port="$4"
            cat << EOF > "/tmp/proxychains-$$.conf"
quiet_mode
proxy_dns
remote_dns_subnet 224
tcp_read_time_out 1000
tcp_connect_time_out 1000
[ProxyList]
${protocol} ${host} ${port}
EOF
            export LD_PRELOAD=/usr/lib/libproxychains4.so PROXYCHAINS_CONF_FILE="/tmp/proxychains-$$.conf" PROXYCHAINS_QUIET_MODE=1 PROXYCHAINS_ENDPOINT="${protocol}://${host}:${port}"
            ;;
        1:unset)
            if [[ "$PROXYCHAINS_CONF_FILE" == /tmp/proxychains-*.conf ]]; then
                rm -f "$PROXYCHAINS_CONF_FILE"
            fi
            unset LD_PRELOAD PROXYCHAINS_CONF_FILE PROXYCHAINS_QUIET_MODE PROXYCHAINS_ENDPOINT
            ;;
        1:whereami)
            echo "$PROXYCHAINS_ENDPOINT"
            ;;
        *:exec)
            if (( $3 < 6 )); then
                echo 'bad arguments' >&2
                return 1
            fi
            proxyconf set "$2" "$3" "$4"
            "${@:5}"
            ;;
        *)
            echo 'bad arguments' >&2
            echo >&2
            echo 'usage:' >&2
            echo '  set http|socks4|socks5 HOST PORT' >&2
            echo '  unset' >&2
            echo '  whereami' >&2
            echo '  exec http|socks4|socks5 HOST PORT CMDLINE...' >&2
            return 1
            ;;
    esac
}

compdef "_arguments '1:first arg:(set unset whereami exec)'" proxyconf
