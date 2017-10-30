import requests
import json
import re
import ConfigParser
import pymssql
from datetime import datetime

# SQL Variables
config = ConfigParser.ConfigParser()
config.read('/home/pi/rcs/sqlconfig.ini')
sqlu = config.get('SectionOne','username')
sqlp = config.get('SectionOne','password')
sqld = config.get('SectionOne','database')
sqls = config.get('SectionOne','server')

# COC Variables
token = config.get('SectionFour','

# Open SQL connection
conn1=pymssql.connect(sqls, sqlu, sqlp, sqld)
cursor1=conn1.cursor()  # multiple cursors needed to pull from various tables at the same time
cursor2=conn1.cursor()
cursor3=conn1.cursor()

# Pulls a list of active clans in our family
cursor1.execute('SELECT clanTag, clanName, clanLeader, discordTag FROM rcs_data')
fetched1 = cursor1.fetchall()

# Read from Discord Channel
token = 'BOT_TOKEN_HERE'
headers = {'Accept':'application/json','Authorization':'Bot ' + token}
url = 'https://discordapp.com/api/channels/CHANNEL_ID_HERE/messages'     # Replace CHANNEL_ID_HERE with the channel you are reading from
r = requests.get(url, headers=headers)
stringdata = str(r.json())

# RegEx to search for fields following "Tag: " or the 9 characters following a hashtag
regex = ur"[tT]ag:\s[a-zA-Z0-9]+|#[a-zA-Z0-9]+"
matches = re.finditer(regex, stringdata)

# Build array from data retrieved from Discord
banList = []
for match in matches:
  if match.group() != '#':
    banList.append(match.group().upper().replace('TAG: ','#'))
  else:
    banList.append(match.group())

# COC Variables
apiKey = config.get('SectionTwo', 'apikey')
headers = {'Accept':'application/json','Authorization':'Bearer ' + apiKey}

# Pull all members for each clan in the RCS and compare to the banList
for item in fetched1:
  print('Checking ' + item[1])
  url = 'https://api.clashofclans.com/v1/clans/%23' + item[0] + '/members'
  r = requests.get(url, headers=headers)
  data = r.json()
  try:
    for member in data['items']:
      if member['tag'] in banList:
        cursor3.execute('SELECT COUNT(timestamp) AS reported, clanTag, memberTag FROM rcs_notify WHERE memberTag = %s GROUP BY clanTag, memberTag', member['tag'][1:])
        if cursor3.rowcount == 0:
          # create payload and send to Discord
          print(member['name'] + ' (' + member['tag'] + ') should not be in ' + item[1] + '. Please check #leader-notes for details.')
          webhookUrl = 'https://discordapp.com/api/webhooks/...' 
          payload = {
            "content": '<@!' + item[3] + '> ' + member['name'] + ' (' + member['tag'] + ') is in ' + item[1] + '. Please search for `in:leader-notes ' + member['tag'] + '` for details.'
          }
          r = requests.post(webhookUrl, json=payload)
          cursor2.execute('INSERT INTO rcs_notify VALUES (%s, %s, %s)', (datetime.now().strftime('%m-%d-%Y %H:%M:%S'), item[0], member['tag'][1:]))
          conn1.commit()
        else:
          fetched3 = cursor3.fetchall()
          for clan in fetched3:
            if clan[1] == item[0] and clan[0] < 3:
              # create payload and send to Discord
              print(member['name'] + ' (' + member['tag'] + ') should not be in ' + item[1] + '. Please check #leader-notes for details.')
              bot_url = 'https://discordapp.com/api/webhooks/364947617639170050/4APE1HWbkSvmFPeKf1y193lXulR_DmKMkPplqq1IYXahGeXTe_Opn7kh7$
              payload = {
                "content": '<@!' + item[3] + '> ' + member['name'] + ' (' + member['tag'] + ') is in ' + item[1] + '. Please search for `$
              }
              #r = requests.post(bot_url, json=payload)
              #cursor2.execute('INSERT INTO rcs_notify VALUES (%s, %s, %s)', (datetime.now().strftime('%m-%d-%Y %H:%M:%S'), item[0], memb$
              #conn1.commit()
  except:
    print('Something broke with ' + member)

conn1.close()

