#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))

import webapp2
import jinja2
import urllib
import urllib2
import json


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

APIKEY = '81ae602f16f34cbc9fe2643c7691f3d3'
ENTITY_SEARCH_URL = 'http://transparencydata.com/api/1.0/entities.json?apikey=%s&search=' % APIKEY


def pol_search(text):
    r = urllib2.urlopen(ENTITY_SEARCH_URL + text).read()
    return json.loads(r)

def pol_contributors(pol_id, limit, cycle, APIKEY):
    CONTRIB_URL = 'http://transparencydata.com/api/1.0/aggregates/pol/%s/contributors.json?apikey=%s&limit=%s&cycle=%s' % (pol_id, APIKEY, limit, cycle)
    r = urllib2.urlopen(CONTRIB_URL).read()
    return json.loads(r)

def org_recipients(org_id, APIKEY):
    ORG_RECIPIENTS_URL = 'http://transparencydata.com/api/1.0/aggregates/org/%s/recipients.json?apikey=%s&limit=5&cycle=2012' % (org_id, APIKEY)
    r = urllib.urlopen(ORG_RECIPIENTS_URL).read()
    return json.loads(r) 




class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)
    

class MainHandler(Handler):
    def get(self):
        self.render('main.html')    
        
    def post(self):
        self.candidate_text = self.request.get('candidate_text')
        self.candidate_id = str(self.request.get('candidate_id'))
        self.contrib_data = None
        
        params = {'error':'', 'recipients':[]}
        
        if self.candidate_text:
            self.candidate_choices = pol_search(urllib.quote_plus(self.candidate_text))
            params['candidate_text'] = self.candidate_text
            params['candidate_choices'] = self.candidate_choices
            
        if self.candidate_id:
            self.contrib_data = pol_contributors(self.candidate_id, 20, 2012, APIKEY)
            params['candidate_id'] = self.candidate_id
            params['contrib_data'] = self.contrib_data
            params['candidate_info'] = [c for c in self.candidate_choices if c['id'] == self.candidate_id]
            params['candidate_name'] = params['candidate_info'][0]['name']

        if self.contrib_data:
            for i in self.contrib_data:
                i['total_amount'] = int(float(i['total_amount']))
                i['recipients'] = [] 
                try:               
                    for j in org_recipients(i['id'], APIKEY):
                        i['recipients'].append([j['name'], int(float(j['total_amount']))])
                except:
                    i['recipients'].append([params['candidate_info'][0]['name'], i['total_amount']])
                if params['candidate_name'] not in [tup[0] for tup in i['recipients']]:
                    i['recipients'].append([params['candidate_info'][0]['name'], i['total_amount']])
                    
            self.contributions = []
            for i in self.contrib_data:
                for j in i['recipients']:
                    self.contributions.append(j[1])
            self.max_contrib = max(self.contributions)
            params['candidate_choices'] = None
            params['contrib_data'] = self.contrib_data
            params['max_contrib'] = self.max_contrib

             
        else:
            params['error'] = 'No data available'



        self.render('main.html', **params)



app = webapp2.WSGIApplication([('/', MainHandler)],
                              debug=True)
