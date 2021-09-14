#!/opt/monitoring/plugins/junos-checks/venv/bin/python3
from jnpr.junos import Device
from pprint import pprint
import re
import sys
import getopt
import lxml

def usage():
    print("check_junos_alarms.py <-H|--host> <-u|--user> <-p|--pasword>")

def dump_xml(tree):
    print(lxml.etree.tostring(tree, encoding="unicode", pretty_print=True))

def check_alarms_active_xml(xml):
    if xml.xpath('./alarm-summary/no-active-alarms'):
        return 0
    else:
        return int(xml.xpath('./alarm-summary/active-alarm-count')[0].text)
    
def status_to_text(rc):
    if rc == 0:
        return "OK"
    elif rc == 1:
        return "Warning"
    elif rc == 2:
        return "Critical"
    else:
        return "Unknown"
            
def alarms_status_and_list(xml, re=None):
    text = ""
    rc = 0
    for alarm in res.xpath('./alarm-detail'):
        #time = alarm.findtext('alarm-time').strip()
        sev  = alarm.findtext('alarm-class').strip()
        desc = alarm.findtext('alarm-description')
        if sev == "Minor" and rc < 1:
            rc = 1
        elif sev == "Major" and rc < 2:
            rc = 2
        #text += "%10s %6s %s\n"%(time, sev, desc)
        if re:
            text += "%s: "%(re)
        text += "%s %s\n"%(sev, desc)
    return rc, text

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
    res = dev.rpc.get_system_alarm_information()
    dev.close()


    rc = 0
    alarms_text = ""
    if res.tag == 'multi-routing-engine-results':
        node_count = []
        for item in res.xpath('./multi-routing-engine-item'):
            re     = item.xpath('./re-name')[0].text
            ai     = item.xpath('./alarm-information')[0]
            n = check_alarms_active_xml(ai)
            node_count.append("%s: %s Alarms"%(re, n))
            if n:
                rc_new, alarms_text_new = alarms_status_and_list(ai, re)
                alarms_text += alarms_text_new
                if rc_new > rc:
                    rc = rc_new
        print("Alarms %s: %s"%(status_to_text(rc), ', '.join(node_count)))
    else:
        n = check_alarms_active_xml(res)
        if n:
            rc, alarms_text = alarms_status_and_list(res)
        print("Alarms %s: %d Alarms"%(status_to_text(rc), n))

    if len(alarms_text) > 0:
        print(alarms_text, end='')
    sys.exit(rc)
