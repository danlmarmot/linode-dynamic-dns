linode-dynamic-dns
==================

Simple dynamic DNS updater for Linode.
Includes an email notification if it detects your DNS has changed via sendmail

To install:
- pip install -r requirements.txt

To use, just add a cron job:
0 * * * *    python /path/to/scripts/linode-dynamic-dns.py

