import requests
import json
import re
import ConfigParser
import pymssql
from datetime import datetime

# SQL Variables
config = ConfigParser.ConfigParser()
config.read('/home/pi/rcs/config.ini')
sqlu = config.get('SectionOne','username')
sqlp = config.get('SectionOne','password')
sqld = config.get('SectionOne','database')
sqls = config.get('SectionOne','server')
token = config.get('SectionFive','token')

# Open SQL connection
conn1=pymssql.connect(sqls, sqlu, sqlp, sqld)
cursor1=conn1.cursor()
cursor2=conn1.cursor()
cursor3=conn1.cursor(as_dict=True)

# Fetch list of RCS Clans
cursor1.execute('SELECT clanTag FROM rcs_data')
fetch = cursor1.fetchall()
# I don't remember what error I was having, but I wasn't able to use fetch as a list later, so this
# section just puts the fetch into a python list
rcsClans = []
for clan in fetch:
  rcsClans.append(clan[0])

# Pull message history from the RCS Discord #leader-notes channel
headers = {'Accept':'application/json','Authorization':'Bot ' + token}
url = 'https://discordapp.com/api/channels/308300486719700992/messages'     # RCS leader-notes
r = requests.get(url, headers=headers)
stringdata = str(r.json())

# find text in message history that is preceeded by 'Tag: ' or '#'
regex = ur"[tT]ag:\s[a-zA-Z0-9]+|#[a-zA-Z0-9]{6,}"
matches = re.finditer(regex, stringdata)

banSet = set()
for match in matches:
  if match.group() != '#':
    banSet.add(match.group().upper().replace('TAG: ','#'))
  else:
    banSet.add(match.group())
# Convert to unique list (some players have multiple warnings
banList = list(banSet)

apiKey = config.get('SectionTwo', 'apikey')
headers = {'Accept':'application/json','Authorization':'Bearer ' + apiKey}
webhookUrl = 'https://discordapp.com/api/webhooks/364947617639170050/4APE1HWbkSvmFPeKf1y193lXulR_DmKMkPplqq1IYXahGeXTe_Opn7kh7fOx8eJ8av3H'  # Webhook for Discord Leader Chat

# Loop through all members who are listed in leader notes
# They aren't really banned, but have warnings worth knowning about
for member in banList:
  url = 'https://api.clashofclans.com/v1/players/%23' + member[1:]
  r = requests.get(url, headers=headers)
  data = r.json()
  # Used a try because if someone is not in a clan, the JSON will not have ['clan']['tag']
  try:
    if data['clan']['tag'][1:] in rcsClans:
      cursor2.execute('SELECT COUNT(timestamp) AS reported, clanTag, memberTag FROM rcs_notify WHERE memberTag = %s AND clanTag = %s GROUP BY clanTag, memberTag', (data['tag'][1:], data['clan']['tag'][1:]))
      fetch = cursor2.fetchall()
      if cursor2.rowcount == 0:
        reported = 0
      else:
        reported = fetch[0][0]
      if reported < 3:
        cursor3.execute('SELECT clanTag, discordTag FROM rcs_data WHERE clanTag = %s', data['clan']['tag'][1:])
        clan = cursor3.fetchone()
        print(data['name'] + ' (' + data['tag'] + ') is in ' + data['clan']['name'] + '. Please check #leader-notes for details.')
        payload = {
          'content' : '<@!' + clan['discordTag'] + '> ' + data['name'].encode('ascii','ignore') + ' (' + data['tag'] + ') is in ' + data['clan']['name'] + '. Please search for `in:leader-notes ' + data['tag'] + '` for details.'
        }
        r = requests.post(webhookUrl, json=payload)
        cursor2.execute('INSERT INTO rcs_notify VALUES (%s, %s, %s)', (datetime.now().strftime('%m-%d-%Y %H:%M:%S'), clan['clanTag'], data['tag'][1:]))
        conn1.commit()
  except:
    print('Error: ' + data['name'].encode('ascii','ignore') + ' (' + member + 'is not in a clan')

conn1.close()
