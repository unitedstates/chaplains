import os
import re
import sys
import json
from utils import download, write

try:
    keys = json.load(open(os.getcwd() + "/keys.json", 'r'))
except:
    print "Couldn't load 'keys.json' from root directory"
    sys.exit()
    
key = keys.get("nytimes", False)
    
if not key:
    print "Couldn't find New York Times API key in keys.json"
    sys.exit()
    
# Thanks to Peter Norvig for edit distance code
# http://norvig.com/spell-correct.html
alphabet = 'abcdefghijklmnopqrstuvwxyz'

def edits1(word):
   splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
   deletes    = [a + b[1:] for a, b in splits if b]
   transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
   replaces   = [a + c + b[1:] for a, b in splits for c in alphabet if b]
   inserts    = [a + c + b     for a, b in splits for c in alphabet]
   return set(deletes + transposes + replaces + inserts)
    
def one_away(word1, word2):
    if word1 in edits1(word2):
        return True
    return False    

# bare-bones wrapper for API
def get_members(congress, chamber):
    if chamber[0].lower() == 'h':
        chamber = 'house'
    elif chamber[0].lower() == 's':
        chamber = 'senate'
    else:
        print "Couldn't guess which chamber you meant by '%s'" % chamber
        return
    
    url = "http://api.nytimes.com/svc/politics/v3/us/legislative/congress/%d/%s/members.json?api-key=%s" % (congress, chamber, key)
    members = json.loads(download(url, os.getcwd() + "/members/%s_%d.json" % (chamber, congress)))
    return members

def lookup(name, congress=113, state='', chamber='house'):
    if len(state) > 2:
        print "Please use abbreviation for state"
        sys.exit()
    state = state.upper()
    
    if type(name) is str:
        name = name.split(' ')
    
    #build a list of all possible versions of surname
    matches = [name[-1]]
    #if three names and second-to-last is not an initial
    #Thanks for nothing, Sheila Jackson-Lee
    if len(name) > 2 and len(name[-2]) > 2:
        matches.append(name[-2] + '-' + name[-1])
    #likewise, if a hyphen, include both a double name and just the second name
    #Thanks for nothing, Cathy McMorris Rodger
    if "-" in name[-1]:
        matches.append(name[-1].split('-')[1])
        matches.append(name[-1].replace('-', ' '))
        
    #take care of any apostrophes and special characters
    #API appears to remove apostophes (See Rosa De'Lauro, D-CT in 112th)
    if ("'" in name[-1]):
        matches.append(name[-1].replace("'", ""))
    if (name[-1].encode('ascii', 'replace') != name[-1]):
        matches.append(name[-1].encode('ascii', 'replace'))
    
    members = get_members(congress, chamber)['results'][0]['members']
    candidates = []
    for member in members:
        if member['last_name'].encode('utf-8') in matches:
            #if first + last match, return right away. Else, add to candidate matches
            if member['first_name'] == name[0]:
                member['status'] = 'Found'        
                return member
            candidates.append(member)
    if len(candidates) == 1:
        candidates[0]['status'] = 'Found'        
        return candidates[0]
        
    #if multiple matches, match based on state, then firstname
    #TO DO: Make this iterative
    for candidate in candidates:
        if candidate['state'] != state:
            candidates.remove(candidate)

    if len(candidates) == 1:
        candidates[0]['status'] = 'Found'        
        return candidates[0]

    for candidate in candidates:
        #match on first three letters of first name, which can capture some nicknames
        if candidate['first_name'][:3] != name[0][:3]:
            candidates.remove(candidate)

    if len(candidates) == 1:
        candidates[0]['status'] = 'Found'        
        return candidates[0]

    # if STILL no matches, start looking for misspellings of one edit distance:
    for member in members:
        for match in matches:            
            if one_away(match, re.sub("I+", "", member['last_name']).replace("Jr.", "")):
                #for now, let's only return a misspelling if first name matches 
                if member['first_name'][:3] == name[0][:3]:
                    member['status'] = 'Found'
                    return member

    return { 'status': 'Not found' }