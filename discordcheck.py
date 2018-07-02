import json
import requests
from datetime import datetime, date
import time # remove
import pymssql
import re
from config import settings

# Open SQL connection
conn=pymssql.connect(settings['database']['server'], settings['database']['username'], settings['database']['password'], settings['database']['database'])
cursor=conn.cursor()
# get list of clans to test against today
cursor.execute('SELECT * FROM rcs_vwDiscordClans')
fetch = cursor.fetchall()
dailyClanDict = [{'shortName': row[1], 'leaderTag': row[2], 'clanName': row[3]} for row in fetch]
# get full list of RCS clans
cursor.execute('SELECT shortName FROM rcs_data')
fetch = cursor.fetchall()
clanList = [] #[row[0] for row in fetch]
for row in fetch:
  if '/' in row[0]:
    for clan in row[0].split('/'):
      clanList.append(clan)
  else:
    clanList.append(row[0])
conn.close()

# Discord variables
guestRole = '301438407576387584'
memberRole = '296416358415990785'
discordServer = str(settings['discord']['rcsGuildId'])

headers = {'Accept':'application/json','Authorization':'Bot ' + settings['discord']['rcsbotToken']}
url = 'https://discordapp.com/api/guilds/' + discordServer + '/members?limit=1000'      # List RCS Discord members
r = requests.get(url, headers=headers)
data = r.json()

def getDiscordName(item):
  try:
    if 'nick' in item and item['nick'] is not None:
      return item['nick'].lower(),1
    else:
      return item['user']['username'].lower(),0
  except:
    print(item)

# Loop through clans. Build list of members that do not have the guest role.
others = []
errors = []
for clan in dailyClanDict:
  members = []
  if '/' in clan['shortName']:
    shortList = clan['shortName'].split('/')
  else:
    shortList = [clan['shortName']]
  for clanName in shortList:
    if clanName != 'reddit':
      regex = r"\W" + clanName + "\W"
    else:
      regex = r"\Wreddit[^\s]"
    for item in data:
      if memberRole in item['roles']:
        # function selects either nickname (if exists) or username
        discordName, discordFlag = getDiscordName(item)
        # if clan name is found in Discord name, we append to list and continue to next item in list
        if re.search(regex, discordName, re.IGNORECASE) is not None:
          reportName = item['nick'] if discordFlag == 1 else item['user']['username']
          members.append('Discord Name: ' + reportName)

  # Discord Payload here
  txtString = '<@!' + clan['leaderTag'] + '> Please check the following list of members to make sure everyone is still in your clan (or feeder). '
  txtString += 'If someone is no longer in your clan, please notify a Global Chat Mod to have their Member role removed.\n\n'
  txtString += '**Results for ' + clan['clanName'] + '**\n'
  for member in members:
    txtString += '   ' + member + '\n'
  if members != []:
    payload = {'content' : txtString}
    r = requests.post(settings['discord']['dangerBot'], json=payload)

# Once a week, we check for any users with the Members role that aren't otherwise connected to a clan
# catching some false once since people identify their clans differently
if date.today().weekday() == 6:
  for item in data:
    if memberRole in item['roles']:
      test = 0
      discordName, discordFlag = getDiscordName(item)
      for clanName in clanList:
        if clanName in discordName:
          test = 1
          break
      if test == 0:
        errors.append('<@' + item['user']['id'] + '> did not identify with any clan.')
  if errors != []:
    txtString = 'We found some Members without a clan:\n'
    for member in errors:
      txtString += '  ' + member + '\n'
    payload = {'content' : txtString[:1999]}
    r = requests.post(settings['discord']['botDev'], json=payload)
