#!/usr/bin/python
__author__ = 'danlmarmot'

"""
linode-dns.py
A script to update a DNS record on Linode to your external IP.
Expects to run on a *nix like system.
Sends mail if there's a change detected in your external IP address.

References:
  http://pushingkarma.com/notebook/setup-dynamic-dns-using-linode/
  https://pypi.python.org/pypi/linode/

To use:
    Add a cron job like this to run it once an hour:
    0 * * * *    python /path/to/scripts/linode-dynamic-dns.py

"""

import requests
import re
import os
from linode import api
import datetime

# Linode API key
APIKEY = 'YourLinodeAPIKeyGoesHere000000wrHLGe5Y1mwpcGY8o7gIVLx97ixo8rm8gv'
DOMAIN = 'somedomain.com'
DNSHOSTNAME = 'dnshostname'
CHECK_IP_URL = "http://checkip.dyndns.org:8245/"

# Set USEMAIL to False if you don't want email going out
USEMAIL = True
SENDMAIL = "/usr/sbin/sendmail"
SMTPSERVER = "localhost"
MAILFROM = "sender@somedomain.com"
MAILTO = ["reciever@somedomain.com", ]
MAILSUBJECT = DNSHOSTNAME + "." + DOMAIN + " IP address updated"


def get_external_ip(url):
    r = requests.get(url)
    return re.findall('[0-9.]+', r.content)[0]


def set_dns_target(ipAddress, udomain=DOMAIN, dnsHostname=DNSHOSTNAME):
    linConn = api.Api(APIKEY)
    nowStr = datetime.datetime.now().strftime("%Y-%b-%d, %H:%M:%S local")
    for domain in linConn.domain.list():
        if domain['DOMAIN'] == udomain:
            # Look through DNS entries for our domain
            for record in linConn.domain.resource.list(domainid=domain['DOMAINID']):

                # if domain exists, update it as needed and return early
                if record['NAME'] == dnsHostname:
                    if record['TARGET'] == ipAddress:
                        # DNS Entry already exists and is the same IP address
                        msg = "Host %s.%s continues to be set to %s.\nTime is %s" % (
                            dnsHostname, udomain, ipAddress, nowStr)
                        return "ok", msg

                    else:
                        # DNS entry found but IP address different, so update needed
                        result = linConn.domain.resource.update(
                            domainid=domain['DOMAINID'],
                            resourceid=record['RESOURCEID'],
                            target=ipAddress)
                        msg = "Updated host %s.%s to %s.\nTime is %s" % (dnsHostname, udomain, ipAddress, nowStr)
                        return "changed", msg

            # DNS entry not found, so create it
            result = linConn.domain.resource.create(
                domainid=domain['DOMAINID'],
                name=dnsHostname,
                type='A',
                target=ipAddress,
                ttl_sec=3600)
            msg = "Created host %s.%s with IP address %s.\nTime is %s" % (dnsHostname, udomain, ipAddress, nowStr)
            return "changed", msg

    # Return if domain isn't present, or on other errors.
    msg = "Error: Domain %s not found, or possible other error." % udomain
    return "error", msg


def send_mail(body=""):
    message = """\
From: %s
To: %s
Subject: %s

%s
""" % (MAILFROM, ", ".join(MAILTO), MAILSUBJECT, body)

    print message

    p = os.popen("%s -t -i" % SENDMAIL, "w")
    p.write(message)
    p.close()
    return


if __name__ == '__main__':
    print get_external_ip(CHECK_IP_URL)
    status, msg = set_dns_target(get_external_ip(CHECK_IP_URL), DOMAIN, DNSHOSTNAME)
    print msg
    if USEMAIL and status == "changed":
        send_mail(msg)

