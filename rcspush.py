import requests
import json
import logging
import pymssql
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('Starting rcspush.py')

clanList = ['2JU0P82U','22J8ULLL','VPVPC080','2Y28CGP8','QJ8YQG2','9RCRVL8V','CVCJR89','9PL8Y89','888GPQ0J','82U2UVU9','UUJ28VY','2CVLP0P0','PJUQVRC','8VQCC2YP','280V0VYL','CU8YQYCG','2UUCUJL','80YGRPC9','YPCCUR8','Q2PP8VY','202GG$

headers = {'Accept':'application/json','Authorization':'Bearer ' + settings['supercell']['apiKey']}

# Open SQL connection
conn1=pymssql.connect(settings['database']['server'], settings['database']['username'], settings['database']['password'], settings['database']['database'])
cursorMain=conn1.cursor()

def startPush():
  for tag in clanList:
    url = 'https://api.clashofclans.com/v1/clans/%25' + tag
    r = requests.get(url, headers=headers)
    clanData = r.json()
    logger.info('Clan: ' + clanData['name'])
    for member in clanData['memberList']:
      url = 'https://api.clashofclans.com/v1/players/%23' + member['tag'][1:]
      r = requests.get(url, headers=headers)
      memberData = r.json()
      logger.info(' - ' + memberData['name'])
      cursorMain.execute('INSERT INTO rcspush_2018_1 VALUES (%s, %s, %d, %d, %d, %d)', (memberData['tag'][1:], memberData['clan']['tag'][1:], memberData['trophies'], memberData['trophies'], memberData['bestTrophies'], memberData['$
      conn1.commit()


def updatePush():
  pass

if __name__ == '__main__':
  startPush()
