#!/opt/monitoring/plugins/junos-checks/venv/bin/python3
from jnpr.junos import Device
from pprint import pprint
import re
import sys
import getopt

def usage():
    print("check_junos_clusterled.py <-H|--host> <-u|--user> <-p|--pasword>")

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:],
            "H:u:p:h",
            ["host=","user=","password=","help"]
        )
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(3)

    router   = None
    user     = None
    password = None
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(3)
        elif opt in ("-H", "--host"):
            router = arg
        elif opt in ("-u", "--user"):
            user = arg
        elif opt in ("-p", "--password"):
            password = arg
        else:
            usage()
            sys.exit(3)

    if router is None or user is None or password is None:
        usage()
        sys.exit(3)

    dev = Device(host=router, user=user, password=password)
    try:
        dev.open()
    except Exception as err:
        print("Cannot connect: %s"%err)
        sys.exit(3)
    res = dev.rpc.get_chassis_cluster_information()
    dev.close()

    rc = 0
    leds = []
    status_re = re.compile('\(Status: (.*)\)')
    for item in res.xpath('.//multi-routing-engine-item'):
        re    = item.xpath('.//re-name')[0].text
        color = item.xpath('.//chassis-cluster-information/chassis-cluster-led-information/current-led-color')[0].text
        leds.append("%s: %s"%(re, color))
        if color == "Green":
            pass
        elif color == "Amber":
            rc = 2
        else:
            print("Unknown color: %s: %s"%(re, color))
            sys.exit(3)

    status = None
    if rc == 0:
        status = "OK"
    elif rc == 1:
        status = "Warning"
    elif rc == 2:
        status = "Critical"
    else:
        status = "Unknown"

    print("HA %s: "%(status) + ', '.join(leds))
    sys.exit(rc)
