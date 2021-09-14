#!/opt/monitoring/plugins/junos-checks/bin/python3
from jnpr.junos import Device
from pprint import pprint
import re
import sys
import getopt

def usage():
    print("check_junos_ipmonitoring.py <-r|--router> <-u|--user> <-p|--pasword> <-t|--test>")

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "r:u:p:t:h", ["router=","user=","password=","test="])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(3)

    router   = None
    user     = None
    password = None
    policy   = None
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(3)
        elif opt in ("-r", "--router"):
            router = arg
        elif opt in ("-u", "--user"):
            user = arg
        elif opt in ("-p", "--password"):
            password = arg
        elif opt in ("-t", "--test"):
            policy = arg
        else:
            usage()
            sys.exit(3)

    if router is None or user is None or password is None or policy is None:
        usage()
        sys.exit(3)

    dev = Device(host=router, user=user, password=password)
    try:
        dev.open()
    except Exception as err:
        print("Cannot connect")
        sys.exit(3)
    res = dev.rpc.get_ip_monitoring_status(policy=policy)
    dev.close()

    status_re = re.compile('\(Status: (.*)\)')
    header = res.xpath('.//policy-header/policy-name')[0].text
    try:
        status = status_re.search(header).group(1)
    except AttributeError as err:
        print("Cannot get status")
        sys.exit(3)

    probes = res.xpath(".//status/probe-status")
    tests  = res.xpath(".//status/test-name")
    num_probes = len(probes)
    failed_probes = 0
    for i, s in enumerate(probes):
        if s.text != "PASS":
            failed_probes += 1

    print("Status: %s (%s of %s probes failed)"%(status, failed_probes, num_probes))
    if status != "PASS":
        sys.exit(2)
    if failed_probes > 1:
        sys.exit(1)
    sys.exit(0)
