#!/usr/bin/env python

import os
import sys
import json
import argparse
import re
import math
from member_lookup import lookup
from collections import defaultdict
from utils import download, write, uniq
from lxml import etree
from lxml.html import fromstring

#crawl the House Chaplain Web site and download all guest prayers. Caches by default
def collect(options = {}):
    #landing page with links to all guest prayers
    page  = fromstring(download('http://chaplain.house.gov/chaplaincy/guest_chaplains.html'))
    links = uniq(page.xpath("//td/a/@href"))
    limit = options.get("limit", False)
    if limit:
        links = links[:limit]
    
    for link in links:
        try:
            uid = link.split('id=')[1]
        except Exception, e:
            print e
            continue
        html = fromstring(download('http://chaplain.house.gov/chaplaincy/' + link, uid + '.html'))
        info = {}
        info['name'] = html.xpath("//h2/text()")[0]     
        
        #get h3 pairings, guess whether a church is listed based on number of hits
        hs = html.xpath("//h3/text()")
        if len(hs) > 1:
            info['church'] = hs[0].strip()
            info['location'] = hs[1].strip()
        else:
            info['location'] = hs[0].strip()

        # get boldface pairings
        for pair in html.xpath('//strong'):
            if pair.tail:
                label, data = pair.text.replace(':', '').strip(), pair.tail.strip()
                info[label.lower().split(" ")[0]] = data
            elif pair.getnext().tag == 'a':
                label, data = pair.text.replace(':', '').strip(), pair.getnext().xpath("text()")[0].strip()
                info[label.lower().split(" ")[0]] = data
    
        # add h4/p pairings
        for pair in html.xpath('//h4'):
            if pair.getnext().tag == 'p':
                label, data = pair.text.replace(':', '').strip(), '\n'.join([x.strip() for x in pair.getnext().xpath("text()")])
                info[label.lower().split(" ")[0]] = data
        if "one" in info:
            info["introduction"] = info["one"]
            info.pop("one")

        #sessions
        info["session"] = int(math.floor((int(info["date"].split("/")[-1]) - 1789) / 2) + 1)
        info['uid'] = uid
        info['member'] = {}
        
        #get bioguide match for sponsor
        if 'sponsor' in info:
            #fix a recurring typo on House Chaplain website            
            info['member'] = {}
            info['sponsor'] = info['sponsor'].replace("Rep. Rep.", "Rep.")
            pieces = re.search("\s(.+?), \(([A-Z])-([A-Z]{2})\)", info['sponsor']).groups()
            info['member']['name'] = pieces[0]
            info['member']['party'] = pieces[1]
            info['member']['state'] = pieces[2]
            member_info = lookup(info['member']['name'], info['session'], info['member']['state'], 'house')
            
            if member_info['status'] == 'Found':
                #use name info from API instead since it's more canonical 
                if not member_info['middle_name']:
                    member_info['middle_name'] = ''
                info['member']['name'] = member_info["first_name"] + " " + member_info['middle_name'] + " " + member_info['last_name']
                info['member']['name'] = info['member']['name'].replace("  ", " ")
                info['member']['state'] = member_info["state"]
                info['member']['bioguide'] = member_info['id']
            else:
                print member_info['status'], info['member']['name']
                print "Unable to find %s (%d) in the NYT API" % (info['sponsor'], info['session'])                  
                info['member']['bioguide'] = None
            info.pop("sponsor")
        write(json.dumps(info, indent=2), os.getcwd() + "/data/" +  uid + ".json")

#create a single file for use in browser, from whatever we find in the /data/ folder. 723kb without indentation
def combine(options):
    alld  = {}
    files = [x for x in os.listdir(os.getcwd() + "/data/") if re.sub("\d+\.json", "", x) == ""]
    ignore = options.get("ignore", [])
    for file in files:
        sermon = json.load(open(os.getcwd() + "/data/" + file, 'r'))        
        for i in ignore:
            if i in sermon:
                sermon.pop(i)
        alld[sermon['uid']] = sermon
    write(json.dumps(alld, indent=2, sort_keys=True), os.getcwd() + "/data/all.json")
    write(json.dumps(alld, sort_keys=True), os.getcwd() + "/data/all.min.json")

# build a concordance index for fast word lookup
def index(options = {}):
    concordance = defaultdict(list)
    files = [x for x in os.listdir(os.getcwd() + "/data/") if re.sub("\d+\.json", "", x) == ""]
    if options.get('limit', False):
        files = files[:options.get('limit')]

    for file in files:
        sermon = json.load(open(os.getcwd() + "/data/" + file, 'r'))
        words = uniq(re.findall(r"\b[A-z]+\b", sermon['opening'].replace('\n', ' ').lower()))
                
        '''
        if options.get("uniques", False):
            words = uniq(re.findall(r"\b[A-z]+\b", sermon['opening'].replace('\n', ' ').lower()))
        else:
            words = re.findall(r"\b[A-z]+\b", sermon['opening'].replace('\n', ' ').lower())
        '''
        for word in words:
            if len(word) > 2:
                concordance[word].append(file.replace('.json', ''))
                
    write(json.dumps(concordance, sort_keys=True, indent=2), os.getcwd() + "/src/data/index.json")
    write(json.dumps(concordance, sort_keys=True), os.getcwd() + "/src/data/index.min.json")

def main():  
    parser = argparse.ArgumentParser(description="Retrieve guest chaplain invocations")    
    parser.add_argument(metavar="TASK", dest="task", type=str, default="parse",
                        help="which task to run: collect, combine, index")
    parser.add_argument("-l", "--limit", metavar="INTEGER", dest="limit", type=int, default=None,
                        help="minimum number of invocations to retrieve")
    parser.add_argument("-i", "--ignore", metavar="string", dest="ignore", type=str, default='',
                        help="fields not to include in combo file")
    args = parser.parse_args()
        
    if args.task == "collect":
        collect({ 'limit': args.limit })
    elif args.task == "combine":
        combine({'ignore': args.ignore.split(",")})    
    elif args.task == "index":
        index({ 'limit': args.limit })    
    else:
        print "Unknown task (options are collect, combine, index)"
    
if __name__ == "__main__":
    main()