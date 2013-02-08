import os, os.path, errno, sys, traceback
import re, htmlentitydefs
import json
from pytz import timezone
import datetime, time
from lxml import html, etree
import scrapelib
import pprint
import logging

import smtplib
import email.utils
from email.mime.text import MIMEText
import getpass


# read in an opt-in config file for changing directories and supplying email settings
# returns None if it's not there, and this should always be handled gracefully
path = "config.yml"
if os.path.exists(path):
  config = yaml.load(open(path, 'r'))
else:
  config = None

eastern_time_zone = timezone('US/Eastern')

# scraper should be instantiated at class-load time, so that it can rate limit appropriately
scraper = scrapelib.Scraper(requests_per_minute=120, follow_robots=False, retry_attempts=3)

class UnmatchedIdentifer(Exception):
  def __init__(self, id_type, id_value, help_url):
    super(UnmatchedIdentifer, self).__init__("%s=%s %s" % (id_type, str(id_value), help_url))

def format_datetime(obj):
  if isinstance(obj, datetime.datetime):
    return eastern_time_zone.localize(obj.replace(microsecond=0)).isoformat()
  elif isinstance(obj, str):
    return obj
  else:
    return None

# Download file at `url`, cache to `destination`. 
# Takes many options to customize behavior.

def download(url, destination=None, options={}):
  # uses cache by default, override (True) to ignore
  force = options.get('force', False)

  # saves in cache dir by default, override (False) to save to exact destination
  to_cache = options.get('to_cache', True)

  # unescapes HTML encoded characters by default, set this (True) to not do that
  xml = options.get('xml', False)

  # used by test suite to use special (versioned) test cache dir
  test = options.get('test', False)

  # if need a POST request with data
  postdata = options.get('postdata', False)

  if test:
    cache = test_cache_dir()
  else:
    cache = cache_dir()

  if destination:
    if to_cache:
      cache_path = os.path.join(cache, destination)
    else:
      cache_path = destination

  if destination and (not force) and os.path.exists(cache_path):
    if not test: logging.info("Cached: (%s, %s)" % (cache, url))
    with open(cache_path, 'r') as f:
      body = f.read()
  else:
    try:
      logging.info("Downloading: %s" % url)
      
      if postdata:
        response = scraper.urlopen(url, 'POST', postdata)
      else:
        response = scraper.urlopen(url)
      body = response.bytes # str(...) tries to encode as ASCII the already-decoded unicode content
    except scrapelib.HTTPError as e:
      logging.error("Error downloading %s:\n\n%s" % (url, format_exception(e)))
      return None

    # don't allow 0-byte files
    if (not body) or (not body.strip()):
      return None

    # cache content to disk
    if destination:
      write(body, cache_path)

  if not xml:
    body = unescape(body)
    
  return body

def write(content, destination):
  mkdir_p(os.path.dirname(destination))
  f = open(destination, 'w')
  f.write(content)
  f.close()

def read(destination):
  if os.path.exists(destination):
    with open(destination) as f:
      return f.read()

# dict1 gets overwritten with anything in dict2
def merge(dict1, dict2):
  return dict(dict1.items() + dict2.items())

# de-dupe a list, taken from:
# http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
def uniq(seq):
  seen = set()
  seen_add = seen.add
  return [ x for x in seq if x not in seen and not seen_add(x)]

import os, errno

# mkdir -p in python, from:
# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc: # Python >2.5
    if exc.errno == errno.EEXIST:
      pass
    else: 
      raise

def xpath_regex(doc, element, pattern):
  return doc.xpath(
    "//%s[re:match(text(), '%s')]" % (element, pattern), 
    namespaces={"re": "http://exslt.org/regular-expressions"})

# taken from http://effbot.org/zone/re-sub.htm#unescape-html
def unescape(text):
  def remove_unicode_control(str):
    remove_re = re.compile(u'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]')
    return remove_re.sub('', str)

  def fixup(m):
    text = m.group(0)
    if text[:2] == "&#":
      # character reference
      try:
        if text[:3] == "&#x":
          return unichr(int(text[3:-1], 16))
        else:
          return unichr(int(text[2:-1]))
      except ValueError:
        pass
    else:
      # named entity
      try:
        text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
      except KeyError:
        pass
    return text # leave as is

  try:
    text = re.sub("&#?\w+;", fixup, text)
  except:
    text = text.decode('latin-1')
    text = re.sub("&#?\w+;", fixup, text)
  text = remove_unicode_control(text)
  return text

# uses config values if present
def cache_dir():
  cache = None

  if config:
    output = config.get('output', None)
    if output:
      cache = output.get('cache', None)

  if not cache:
    cache = "cache"

  return cache

def test_cache_dir():
  return "test/fixtures/cache"

# uses config values if present
def data_dir():
  data = None

  if config:
    output = config.get('output', None)
    if output:
      data = output.get('data', None)

  if not data:
    data = "data"

  return data

# if email settings are supplied, email the text - otherwise, just print it
def admin(body):
  try:
    if isinstance(body, Exception):
      body = format_exception(body)

    logging.error(body) # always print it

    if config:
      details = config.get('email', None)
      if details:
        send_email(body)
    
  except Exception as exception:
    print "Exception logging message to admin, halting as to avoid loop"
    print format_exception(exception)

def format_exception(exception):
  exc_type, exc_value, exc_traceback = sys.exc_info()
  return "\n".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

# this should only be called if the settings are definitely there
def send_email(message):
  settings = config['email']

  # adapted from http://www.doughellmann.com/PyMOTW/smtplib/
  msg = MIMEText(message)
  msg.set_unixfrom('author')
  msg['To'] = email.utils.formataddr(('Recipient', settings['to']))
  msg['From'] = email.utils.formataddr((settings['from_name'], settings['from']))
  msg['Subject'] = "%s - %i" % (settings['subject'], int(time.time()))

  server = smtplib.SMTP(settings['hostname'])
  try:
    server.ehlo()
    if settings['starttls'] and server.has_extn('STARTTLS'):
      server.starttls()
      server.ehlo()

    server.login(settings['user_name'], settings['password'])
    server.sendmail(settings['from'], [settings['to']], msg.as_string())
  finally:
    server.quit()

  logging.info("Sent email to %s" % settings['to'])