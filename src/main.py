import StringIO
import json
import logging
import random
import urllib
import urllib2

from PIL import Image
import multipart

from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

TOKEN = ''

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

perle_file = open("res/perle.txt", "r")
perle = map(lambda s: s.strip(), list(perle_file))

actions_file = open("res/ricette/actions.txt", "r")
actions = map(lambda s: s.strip(), list(actions_file))
adjectives_file = open("res/ricette/adjectives.txt", "r")
adjectives = map(lambda s: s.strip(), list(adjectives_file))
destinations_file = open("res/ricette/destinations.txt", "r")
destinations = map(lambda s: s.strip(), list(destinations_file))
ingredients_file = open("res/ricette/ingredients.txt", "r")
ingredients = map(lambda s: s.strip(), list(ingredients_file))
plateactions_file = open("res/ricette/plateactions.txt", "r")
plateactions = map(lambda s: s.strip(), list(plateactions_file))
cookware_file = open("res/ricette/cookware.txt", "r")
cookware = map(lambda s: s.strip(), list(cookware_file))
utensils_file = open("res/ricette/utensils.txt", "r")
utensils = map(lambda s: s.strip(), list(utensils_file))

class EnableStatus(ndb.Model):
    enabled = ndb.BooleanProperty(indexed=False, default=False)

def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))

class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))

class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))

class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        update_id = body['update_id']
        message = body['message']
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']

        if not text:
            logging.info('no text')
            return

        def reply(msg=None, img=None):
            if msg:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                    'reply_to_message_id': str(message_id),
                })).read()
            elif img:
                resp = multipart.post_multipart(BASE_URL + 'sendPhoto', [
                    ('chat_id', str(chat_id)),
                    ('reply_to_message_id', str(message_id)),
                ], [
                    ('photo', 'image.jpg', img),
                ])
            else:
                logging.error('no msg or img specified')
                resp = None

            logging.info('send response:')
            logging.info(resp)

        if text.startswith('/'):
            if text == '/start':
                reply('Bot enabled')
                setEnabled(chat_id, True)
            elif text == '/stop':
                reply('Bot disabled')
                setEnabled(chat_id, False)
            elif text == '/image':
                img = Image.new('RGB', (512, 512))
                base = random.randint(0, 16777216)
                pixels = [base+i*j for i in range(512) for j in range(512)]  # generate sample image
                img.putdata(pixels)
                output = StringIO.StringIO()
                img.save(output, 'JPEG')
                reply(img=output.getvalue())
            elif text == "/listperle":
                perle_f = open("res/perle.txt", "r")
                perle_contents = perle_f.read()
                reply("c:"+perle_contents) 
        elif 'perla' in text:
            reply(random.choice(perle))
        elif 'ricetta' in text:
            compose = random.choice(actions) + " " + random.choice(ingredients) + " con " + random.choice(utensils) + " poi " + random.choice(actions) + " " + random.choice(ingredients) + " " + random.choice(cookware) + " e infine " + random.choice(actions) + " " + random.choice(ingredients) + ", " + random.choice(plateactions) + " " + random.choice(adjectives) + " in " + random.choice(destinations)
            reply(compose)
            
app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
