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
- `combine`: Combine into one file
- `index`: Create a concordance index of every word in every prayer

`--limit`: maximum number of prayers to retrieve, combine, or index. Default is all of them

Example:

```
python ./scripts/chaplains.py collect --limit=100
```

### data
As of February 8, 2013, there are 633 such guest prayers on the website. This script retrieves each of them and stores the relevant info in a JSON file. For example:

```
{
  "name": "Reverend Paul A. Stoot, Sr", 
  "opening": "O Lord our God, if ever we needed Thy wisdom and Thy guidance, it is now as this honorable body of great men and women begin a new day, a day that will hold many opportunities and many possibilities.\nWe pray that You will bless these men and these women who have been chosen by the great people of this great Nation, for You know them and You know their needs, You know their motives and their hopes and their fears. Lord Jesus, put Your arms around them and give them strength and speak to them to give them wisdom greater than their own. May they hear Your voice as You speak to them and as they seek to hear from You and Your guidance.\nMay they remember that You are concerned about what is said and what is done here and may they ever have a clear conscience before Thee, that they need fear no man. Bless us each according to our deepest needs as we are here today to use us to Your honor and to Your glory, we humbly ask. Amen.", 
  "state": "WA", 
  "sponsor": "Rep. Rep. Rick Larsen, (D-WA)", 
  "church": "Greater Trinity Missionary Baptist Church", 
  "date": "06/21/2001", 
  "party": "D", 
  "id": "1142", 
  "location": "Everett, WA"
}
```