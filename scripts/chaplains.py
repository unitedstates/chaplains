import os
import sys
import json
import argparse
import re
from collections import defaultdict
from utils import download, write, uniq
from lxml import etree
from lxml.html import fromstring

#crawl the House Chaplain Web site and download all guest prayers. Caches by default
def collect(options = {}):
    page  = fromstring(download('http://chaplain.house.gov/chaplaincy/guest_chaplains.html'))
    links = page.xpath("//td/a/@href")
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
        hs = html.xpath("//h3/text()")
        if len(hs) > 1:
            info['church'] = hs[0].strip()
            info['location'] = hs[1].strip()
        else:
            #print hs
            info['location'] = hs[0].strip()
            
        for pair in html.xpath('//strong'):
            if pair.tail:
                label, data = pair.text.replace(':', '').strip(), pair.tail.strip()
                info[label.lower().split(" ")[0]] = data
            elif pair.getnext().tag == 'a':
                label, data = pair.text.replace(':', '').strip(), pair.getnext().xpath("text()")[0].strip()
                info[label.lower().split(" ")[0]] = data
    
        for pair in html.xpath('//h4'):
            if pair.getnext().tag == 'p':
                label, data = pair.text.replace(':', '').strip(), '\n'.join([x.strip() for x in pair.getnext().xpath("text()")])
                info[label.lower().split(" ")[0]] = data
        if "one" in info:
            info.pop("one")
        info['id'] = uid
        if 'sponsor' in info:
            #fix a recurring typo on House Chaplain website            
            info['sponsor'] = info['sponsor'].replace("Rep. Rep.", "Rep.")
            
            m = re.findall("\(([A-Z])-([A-Z]+)\)", info["sponsor"])
            info['party'] = m[0][0]
            info['state'] = m[0][1]
        else:
            info['party'] = 'N'
            info['state'] = ''
            
        write(json.dumps(info, indent=2), os.getcwd() + "/data/" +  uid + ".json")
        #print uid

#create a single file for use in browser. 723kb without indentation
def combine(options = {}):
    alld  = {}
    files = [x for x in os.listdir(os.getcwd() + "/data/") if re.sub("\d+\.json", "", x) == ""]
    if options.get('limit', False):
        files = files[:options.get('limit')]
        
    for file in files:
        sermon = json.load(open(os.getcwd() + "/data/" + file, 'r'))        
        alld[sermon['id']] = sermon
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
    args = parser.parse_args()
    
    if args.task == "collect":
        collect({ 'limit': args.limit })
    elif args.task == "combine":
        combine({ 'limit': args.limit })    
    elif args.task == "index":
        index({ 'limit': args.limit })    
    elif args.task == "find":
        find()    
    
if __name__ == "__main__":
    main()