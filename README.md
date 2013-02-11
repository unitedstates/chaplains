# Guest Chaplains

To quote the [House Chaplain's website](http://chaplain.house.gov/chaplaincy/guest_chaplains.html):
> One of the special privileges and great joys of being House Chaplain is to welcome guest chaplains who have been recommended by the Members of Congress. This is a wonderful opportunity to affirm pastoral leaders from many different backgrounds. This practice manifests the freedom of worship enjoyed across this nation.

## Quick setup

It's recommended to make a virtualenv, then run:

```bash
pip install -r requirements.txt
```

## Running

### chaplains.py
Options:

`task`: Which task to perform. Options are:
- `collect`: Scrape the prayers from the House Chaplain website 
- `combine`: Combine all prayers in /data/ directory into one file
- `index`: Create a concordance index of every word in every prayer in the /data/directory

####collect params
`--limit`: maximum number of prayers to retrieve, combine, or index. Default is all of them

####combine params
`--ignore`: fields in the individual prayer files to leave out of combined file to reduce size. Options include any top-level key in sample data structure below

Example:
```
python ./scripts/chaplains.py collect --limit=100
```

### data
As of February 8, 2013, there are 633 such guest prayers on the website. This script retrieves each of them and stores the relevant info in a JSON file. For example:

```
{
  "name": "Reverend Daniel P. Coughlin", 
  "opening": "Almighty God,\nwe pause this morning to give You thanks.\nWe thank you for another day to live and work in the USA.\nWe thank you for your Word, which teaches us righteousness and justice and equity.\nWe thank you for giving us a system of government that honors our dignity and checks our depravity.\nWe repent for the spirit of self\u2013sufficiency that tells us we do not need You, and the spirit of arrogance that tells us we do not need others.\nOn this first day of May, dear Father, we make a new commitment to live out our nation's motto, \"In God we trust.\"\nFor You are the Rock of our salvation,\nYou are our Hiding Place in times of terror,\nYou are the Truth in Whom we can rely.\nOur nation needs a third great spiritual awakening.  May it begin here, with each of us.\nBless these men and women, who represent America.\nBless them in their deliberations to seek and find Your wisdom, that Thy will be done on earth as it is in heaven.\nHear our prayer, for you are our Lord and Savior.  Amen.", 
  "introduction": "Mr. Speaker, I rise this morning to welcome my good friend, Pastor Jim Congdon, to the floor of the House of Representatives.  It was my distinct honor to invite Pastor Congdon to deliver our opening prayer this morning, and I am grateful for his willingness to do so.\nPastor Congdon is from Topeka, Kansas, and pastors the Topeka Bible Church, which my family and I attended for several years.  It was a privilege to call Jim my pastor, and I am grateful for his continued friendship and dedication to the ministry.\nI also want to welcome Jim's wife, Melody, to the House Chamber.  I know she came with Jim and she speaks for a lot of different people in the church.  She is a constant source of strength and support in the ministry at the Topeka Bible Church.\nFinally, I want to welcome the 62 students from Cair Paravel Latin School that are seated in the gallery.  Pastor Congdon teaches philosophy at Cair Paravel, and these 9th and 10th graders are in D.C. for part of their studies.  I thank them all for being here.\nI thank Jim and Melody for their presence, and God bless them.;", 
  "member": {
    "party": "R", 
    "state": "KS", 
    "name": "Jim R. Ryun", 
    "bioguide": "R000566"
  }, 
  "session": 107, 
  "church": "Topeka Bible Church", 
  "date": "05/01/2002", 
  "uid": "1069", 
  "location": "Topeka, KS"
}
```

## Internal method of member lookup
To get the [Congressional Bioguide](http://bioguide.congress.gov/biosearch/biosearch.asp) ID for each member, I wrote a small library called `member_lookup.py`, which compares the plaintext name of the member to the NYT API for that session

### Setup
You need to get an [NYT API key](http://developer.nytimes.com/docs/reference/keys) with access to the Congress api. Put it in a file called keys.json in the root directory like so:
```
   {
      "nytimes": "[key]"
   }
```
"keys.json" is included in .gitignore

###How it works:
- If fed a string for the name, the function assumes it's in first, middle, last order. Can also accept a list of names in that order
- If there are three names, not including initials, it adds both the surname and a hyphenated middle-last name to the list of names to search, since no one can agree on whether Sheila Jackson Lee uses a hyphen
- Likewise, if fed a surname with a hyphen, this function also searches for that name with just a space and with just the second of the two names
- The function then finds all members of the inputed session and chamber with a matching surname. Often this is just one person, so we have a high-confidence match
- If multiple members for the inputed session have the same surname, it then reduces the list of possible matches by state and then first name.
- If there's still no good match, when then start comparing the inputed surname to all members, allowing for an edit distance of one, which will catch common misspellings without too high a risk of false positives

Members this function can find in spite of errors on House Chaplain website:
- "Rep. Rep. Jim Ryn (R-KS)" correctly finds Jim Ryan
- "Rep. Rep. Deborah Halverson (D-IL)" finds Debbie Halvorson
- "Rep. Jean Schmidt (R-AL)" finds Jean Schmidt of Ohio

Members who currently trip up the function for TK reason:
- Rep. Hon. Stephanie Herseth Sandlin, (D-SD) (110)
- Rep. Hon. John Spratt, (D-SC) (109)
- Rep. Cathy McMorris, (R-WA) (109)
- Rep. Hon. Tom Davis, (R-VA) (108)
- Rep. Chris Van Hollen, (D-MD) (108)
- Rep. John Duncan, Jr., (R-TN) (107)