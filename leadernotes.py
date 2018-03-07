import requests
import json
import re
import pymssql
from datetime import datetime
from config import settings

def fetch_notification_count(memberTag, clanTag):
  cursor = conn1.cursor()
  cursor.execute('SELECT COUNT(timestamp) AS reported, clanTag, memberTag FROM rcs_notify WHERE memberTag = %s AND clanTag = %s GROUP BY clanTag, memberTag', (memberTag, clanTag))
  fetch = cursor.fetchall()
  if cursorMain.rowcount == 0:
    return 0
  else:
    return fetch[0][0]

def fetch_discord_tag(clanTag):
  cursor = conn1.cursor()
  cursor.execute('SELECT clanTag, discordTag FROM rcs_data WHERE clanTag = %s', clanTag)
  fetch = cursor.fetchall()
  return fetch[0][1]

# Open SQL connection
conn1=pymssql.connect(settings['database']['server'], settings['database']['username'], settings['database']['password'], settings['database']['database'])
cursorMain=conn1.cursor()

# Fetch list of RCS Clans
cursorMain.execute('SELECT clanTag FROM rcs_data')
fetch = cursorMain.fetchall()
rcsClans = [clan[0] for clan in fetch]

# Pull message history from the RCS Discord #leader-notes channel
headers = {'Accept':'application/json','Authorization':'Bot ' + settings['discord']['leaderToken']}
url = 'https://discordapp.com/api/channels/308300486719700992/messages'     # RCS leader-notes
r = requests.get(url, headers=headers)
stringdata = str(r.json())

# find text in message history that is preceeded by 'Tag: ' or '#'
regex = ur"[tT]ag:\s[a-zA-Z0-9]+|#[a-zA-Z0-9]{6,}"

banSet = set()
for match in re.finditer(regex, stringdata):
  if match.group() != '#':
    banSet.add(match.group().upper().replace('TAG: ','#'))
  else:
    banSet.add(match.group())
# Convert to unique list (some players have multiple warnings)
banList = list(banSet)

headers = {'Accept':'application/json','Authorization':'Bearer ' + settings['supercell']['apiKey']}

# Loop through all members who are listed in leader notes
# They aren't really banned, but have warnings worth knowning about
for member in banList:
  url = 'https://api.clashofclans.com/v1/players/%23' + member[1:]
  r = requests.get(url, headers=headers)
  data = r.json()
  # Used a try because if someone is not in a clan, the JSON will not have ['clan']['tag']
  try:
    if data['clan']['tag'][1:] in rcsClans:
      reported = fetch_notification_count(data['tag'][1:], data['clan']['tag'][1:])
      if reported < 3:
        discordTag = fetch_discord_tag(data['clan']['tag'][1:])
        payload = {
          'content' : '<@!' + discordTag + '> ' + data['name'].encode('ascii','ignore') + ' (' + data['tag'] + ') is in ' + data['clan']['name'] + '. Please search for `in:leader-notes ' + data['tag'] + '` for details.'
        }
        r = requests.post(settings['discord']['leaderDanger'], json=payload)
        cursorMain.execute('INSERT INTO rcs_notify VALUES (%s, %s, %s)', (datetime.now().strftime('%m-%d-%Y %H:%M:%S'), clan['clanTag'], data['tag'][1:]))
        conn1.commit()
  except Exception as inst:
    print('Exception: ' + member + ' - ' + str(type(inst)))
    print(inst)

conn1.close()
