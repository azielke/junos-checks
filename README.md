# junos-checks

A set of Scripts to check Juniper JunOS devices via NETCONF

## Installation

Clone this repo to /opt/monitoring/plugins/junos-checks
and run `install.sh` to create the python venv and dependencies

```
mkdir -p /opt/monitoring/plugins
git clone <repo> junos-checks
cd junos-checks
./install.sh
```

## Juniper setup

netconf over ssh needs to be enabled:

```
set system services netconf ssh
```

## Icinga2

The file `templates/check_junos.conf` contains Icinga2 checkCommand
definitions. Copy it to your icinga2 installation.

### Example Services

The following vars need to be set with proper usernames:

```
vars.junos_netconf_user = "user"
vars.junos_netconf_password = "password"
```

```
object Service "ip-monitoring failover-to-sat" {
    import "generic-service"
    host_name = "srx-ha"
    check_command = "junos-ipmonitoring"
    retry_interval = 40s
    vars.junos_netconf_user = "user"
    vars.junos_netconf_password = "password"
    vars.junos_ipmonitoring_policy = "failover-to-sat"
}

object Service "HA" {
        import "generic-service"
        host_name = "srx-ha"
        check_command = "junos-clusterled"
        vars.junos_netconf_user = "user"
        vars.junos_netconf_password = "password"
}

```
