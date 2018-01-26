import json
import requests
import ConfigParser
from datetime import datetime

# Variables
config = ConfigParser.ConfigParser()
config.read('config.ini')
apiToken = config.get('supercell','apiToken')
webhookUrl = config.get('discord','webhook')

clanTag = 'CVCJR89'
apiPrefix = 'https://api.clashofclans.com/v1/'
clanUrl = apiPrefix + 'clans/%23'            # %23 is an encoded hashtag since urls can't actually have # in them
playerUrl = apiPrefix + 'players/%23'
headers = {'Accept':'application/json','Authorization':'Bearer ' + apiToken}

# Functions
def rgb(r,g,b):
  return (r*65536) + (g*256) + b

# Request clan information from API
url = clanUrl + clanTag
r = requests.get(url, headers=headers)
data = r.json()
clanName = data['name']
# \n (inside of quotes) is a line feed
print(data['name'] + ': ' + data['tag'] + '\nDescription:' + data['description'])
# Loop through all players and find the leader
for member in data['memberList']:
  if member['role'] == 'leader':
    leaderTag = member['tag'][1:]    # [1:] removes the first character. In this case, the #
    leaderName = member['name']
    break
print('Leader: ' + leaderName + ' (' + leaderTag + ')')

# Request player information from API
url = playerUrl + leaderTag
r = requests.get(url, headers=headers)
data = r.json()

# str() converts integers to strings
print('XP: ' + str(data['expLevel']) + '\nLeague: ' + data['league']['name'] + '\nTrophies: ' + str(data['trophies']))

# send information to Discord via webhook
message = 'Clan: ' + clanName + ' (#' + clanTag + ')\nLeader: ' + leaderName + ' (#' + leaderTag + ')'
payload = {'content' : message}
r = requests.post(webhookUrl, json=payload)

# send pretty information to Discord via webhook
payload = {
  'embeds' : [{
    'color' : rgb(181,0,0),
    'author' : {
      'name' : 'Author Name',
      'icon_url' : 'http://www.mayodev.com/images/hogrider.png'
    },
    'fields' : [
      {'name' : 'Clan','value' : clanName + ' (#' + clanTag + ')','inline' : True},
      {'name' : 'Leader','value' : leaderName + ' (#' + leaderTag + ')','inline' : True}
    ],
    'footer' : {
      'icon_url' : 'https://coc.guide/static/imgs/army/dark-elixir-barrack-6.png',
      'text' : str(datetime.now())
    }
  }]
}
r = requests.post(webhookUrl, json=payload)
