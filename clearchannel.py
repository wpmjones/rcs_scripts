import requests, time
import json

apiToken = [YOUR DISCORD API TOKEN]

channelToClear = '364507837550034956'

def getMessages(channelId, headers):
  # Pull message history from channel
  # max for bulk delete is 100 messages
  url = 'https://discordapp.com/api/channels/' + channelId + '/messages?limit=100'
  r = requests.get(url, headers=headers)
  messages = r.json()
  messageArray = []
  for message in messages:
    messageArray.append(message['id'])
  return messageArray

def clearChannel(channelId):
  headers = {'Accept':'application/json','Authorization':'Bot ' + apiToken}
  messageArray = getMessages(channelId, headers)
  while len(messageArray) > 0:
    url = 'https://discordapp.com/api/channels/' + channelId + '/messages/bulk-delete'
    payload = {'messages': messageArray}
    r = requests.post(url, json=payload, headers=headers)
    if r.status_code == 400:
      print('Bulk delete failed. Switching to individual delete.')
      clearMessage(messageArray, channelId, headers)
    messageArray = getMessages(channelId, headers)

def clearMessage(messageArray, channelId, headers):
  for messageId in messageArray:
    url = 'https://discordapp.com/api/channels/' + channelId + '/messages/' + messageId
    r = requests.delete(url, headers=headers)
    if r.status_code != 204:
      if r.status_code == 429:
        print(' - Too many requests. Taking a break.')
        time.sleep(120)
        print('Retrying...')
        r = requests.delete(url, headers=headers)
      else:
        print(r.status_code)
    time.sleep(3.5)

if __name__ == '__main__':
  print('Go')
  clearChannel(channelToClear)
