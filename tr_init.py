#! flask/bin/python

import os
import sys

if len(sys.argv) != 2:
    print "usage: pythn tr_init.py <language-code>"
    sys.exit(1)
os.system('pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot app')
os.system('pybabel init -i messages.pot -d app/translations -l ' + sys.argv[1])
os.unlink('messages.pot')
