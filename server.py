#!/usr/bin/env python
from inspect import trace
import os
import json
import pytz
import re
import traceback

import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web

from mongo_db_controller import ZoomUserDB
from settings import Settings
from spark import Spark
from msft_functions import msftGET, msftRefresh
from zoom_functions import zoomGET, zoomRefresh
from handlers.base import BaseHandler
from handlers.oauth import AzureOAuthHandler, WebexOAuthHandler, ZoomOAuthHandler

from datetime import datetime, timedelta
from dateutil import parser
from pymongo import ASCENDING, DESCENDING
from tornado.options import define, options, parse_command_line
from tornado.httpclient import HTTPError
from uuid import uuid4

define("debug", default=False, help="run in debug mode")

class SimplifiedHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        try:
            print("SimplifiedHandler GET")
            self.load_page("simplified", zoom_token=False)
        except Exception as e:
            traceback.print_exc()

class FedRampHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        try:
            print("FedRampHandler GET")
            self.load_page("fedramp", zoom_token=False)
        except Exception as e:
            traceback.print_exc()


class MainHandler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        try:
            print("MainHandler GET")
            self.load_page()
        except Exception as e:
            traceback.print_exc()

class CommandHandler(BaseHandler):
    @tornado.gen.coroutine
    def post(self):
        jbody = json.loads(self.request.body)
        print("CommandHandler request.body:{0}".format(jbody))
        command = jbody.get('command')
        version = jbody.get('version')
        search_term = jbody.get('search_term')
        if version == "fedramp":
            person = self.get_fedramp_user()
        else:
            person = self.get_current_user()
        print("CommandHandler, person: {0}".format(person))
        result_object = {"reason":None, "code":200, "data":None}
        if not person:
            result_object['reason'] = 'Not Authenticated with Webex.'
            result_object['code'] = 401
        else:
            person = json.loads(person)
            zoom_user = self.application.settings['db'].get_user(person['id'], "zoom")
            msft_user = self.application.settings['db'].get_user(person['id'], "msft")
            if version in [None] and zoom_user == None:
                result_object['reason'] = 'Not Authenticated with Zoom.'
                result_object['code'] = 403
                result_object['data'] = "zoom"
            elif msft_user == None:
                result_object['reason'] = 'Not Authenticated with Microsoft.'
                result_object['code'] = 403
                result_object['data'] = "msft"
            elif command not in ['search', 'transfer']:
                result_object['reason'] = "{0} command not recognized.".format(command)
                result_object['code'] = 400
            else:
                if command == 'search':
                    result_object = yield self.search_command(result_object, zoom_user, msft_user, version, search_term)
                    ####
                    if version == None:
                        print('pmi(s) from msft calendar:')
                        leftover_meetings = []
                        for msft_pmi in result_object['data']['pmi']['meetings']:
                            print(msft_pmi)
                            msft_start_time = parser.parse(msft_pmi['start_msft']['dateTime'])
                            if(msft_start_time.tzname() == None):#this should always be True unless MSFT changes their datetime string format
                                msft_start_time = pytz.timezone('UTC').localize(msft_start_time)
                            print(msft_start_time)
                            found_meeting = False
                            for zoom_meeting_key in result_object['data']:
                                zoom_meeting = result_object['data'][zoom_meeting_key]
                                if zoom_meeting.get('pmi') != None and not zoom_meeting.get('msft_match'):
                                    print(zoom_meeting)
                                    zoom_start_time = parser.parse(zoom_meeting['start_time'])
                                    if(zoom_start_time.tzname() == None):#this should always be False unless Zoom changes their datetime string format
                                        zoom_start_time = pytz.timezone('UTC').localize(zoom_start_time)
                                    print(zoom_start_time)
                                    found_meeting = zoom_start_time == msft_start_time
                                    temp_msft_start_time = None
                                    temp_zoom_start_time = None
                                    if not found_meeting:
                                        try:
                                            temp_msft_start_time = msft_start_time.replace(tzinfo=pytz.timezone(msft_pmi['start_msft']['timeZone']))
                                            found_meeting = zoom_start_time == temp_msft_start_time
                                        except Exception as e:
                                            pass
                                        if not found_meeting:
                                            try:
                                                temp_zoom_start_time = zoom_start_time.replace(tzinfo=pytz.timezone(zoom_meeting['timezone']))
                                                found_meeting = temp_zoom_start_time == msft_start_time
                                            except Exception as e:
                                                pass
                                    if found_meeting:
                                        result_object['data'][zoom_meeting_key].update(msft_pmi)
                                        result_object['data'][zoom_meeting_key]['msft_match'] = True
                                        break
                            if not found_meeting:
                                start_time = msft_pmi["start_msft"]["dateTime"].rsplit(".",1)[0]
                                meeting_start = datetime.fromisoformat(start_time)
                                meeting_end = datetime.fromisoformat(msft_pmi["end_msft"]["dateTime"].rsplit(".",1)[0])
                                duration = int((meeting_end-meeting_start).total_seconds()/60)
                                msft_pmi["start_time"] = start_time + "Z"
                                msft_pmi["duration"] = duration
                                msft_pmi["topic"] = "/".join(msft_pmi["subjects"])
                                result = self.application.settings['db'].meetings.find_one({"person_id": person['id'], "source_meeting_id":msft_pmi["msft_id"]})
                                if result != None:
                                    msft_pmi.update({"webex_meeting_id":result['webex_meeting_id']})
                                leftover_meetings.append(msft_pmi)
                        result_object['data']['pmi']['meetings'] = leftover_meetings

                    for meeting_id in result_object['data']:
                        if meeting_id == "pmi":
                            continue
                        meeting = result_object['data'][meeting_id]
                        addTopic = ""
                        if meeting.get('subjects') and meeting.get('topic'):
                            for subject in meeting['subjects']:
                                if subject.lower() != meeting['topic'].lower():
                                    print(subject)
                                    if subject.startswith("Re:"):
                                        subject = subject.replace("Re:","", 1)
                                        print(subject)
                                    addTopic += "/" + subject.strip()
                            meeting.pop('subjects')
                            meeting['topic'] += addTopic
                        result = self.application.settings['db'].find_meeting(meeting_id, person['id'], meeting.get("msft_id"))
                        if result != None:
                            result_object['data'][meeting_id].update({"webex_meeting_id":result['webex_meeting_id']})
                elif command == 'transfer':
                    result_object = yield self.transfer_command(person, jbody.get('meetings'), result_object, msft_user, version)
        self.write(json.dumps(result_object))

    @tornado.gen.coroutine
    def search_zoom_meetings(self, zoom_user, result_object):
        found_meeting_ids = {}
        zoom_user_info = {"id":None, "pmi":None, 'pmurl':None, 'base_url':None}
        resp, zoom_user = yield zoomGET('/users/me', zoom_user)
        if zoom_user == None:
            result_object['reason'] = 'Not Authenticated with Zoom.'
            result_object['code'] = 403
            result_object['data'] = "zoom"
        else:
            #print(resp)
            zoom_user_info['id'] = resp.get('id')
            zoom_user_info['pmi'] = str(resp.get('pmi'))
            zoom_user_info['pmurl'] = resp.get('personal_meeting_url')
            zoom_user_info['base_url'] = zoom_user_info['pmurl'].replace(zoom_user_info['pmi'], "").split("?")[0]
            print('zoom_user_info:{0}'.format(zoom_user_info))
            resp, zoom_user = yield zoomGET('/users/me/meetings', zoom_user)
            for meeting in resp.get("meetings",[]):
                print("meeting:")
                print(meeting)
                meeting_id = meeting.pop('id')
                meeting.pop('uuid')
                meeting.pop('created_at')
                future_meeting = False
                if meeting.get('start_time'):
                    future_meeting = datetime.strptime(meeting['start_time'], '%Y-%m-%dT%H:%M:%SZ') > datetime.now()
                if meeting['type'] in [3,8] or future_meeting:
                    resp, zoom_user = yield zoomGET('/meetings/{0}'.format(meeting_id), zoom_user)
                    meeting.update({"recurrence":resp.get('recurrence')})
                    meeting.update({"settings":resp.get('settings')})
                    meeting.update({"agenda":resp.get('agenda','')})
                    found_meeting_ids.update({str(meeting_id): meeting})
            print('search_zoom_meetings, found_meeting_ids:')
            print(found_meeting_ids)
            print("*********************")
        print("zoom_user_info:{0}".format(zoom_user_info))
        raise tornado.gen.Return((found_meeting_ids, zoom_user_info, result_object))

    @tornado.gen.coroutine
    def get_next_msft_instance(self, id, msft_user):
        return_date = ""
        now = datetime.now()
        instance_start = now.isoformat()
        instance_end = (now + timedelta(days=365)).isoformat()
        get_instance_url = "https://graph.microsoft.com/v1.0/me/calendar/events/{0}/instances?"
        get_instance_url += "startDateTime={1}&endDateTime={2}&$select=subject,start&$top=1"
        get_instance_url = get_instance_url.format(id, instance_start, instance_end)
        print('get_instance_url:{0}'.format(get_instance_url))
        instance_resp, msft_user = yield msftGET(get_instance_url, msft_user)
        if len(instance_resp.get('value')) > 0:
            instance = instance_resp['value'][0]
            print('instance: {0}'.format(instance))
            return_date = instance.get('start', {}).get('dateTime',"")
        raise tornado.gen.Return((return_date, msft_user))

    @tornado.gen.coroutine
    def search_msft_calendar(self, msft_user, result_object, found_meeting_ids, search_term, search_pmi, version):
        resp, msft_user = yield msftGET('/me', msft_user)
        if msft_user == None:
            result_object['reason'] = 'Not Authenticated with Microsoft.'
            result_object['code'] = 403
            result_object['data'] = "msft"
        else:
            print('search_msft_calendar /me body:{0}'.format(resp))
            user_email = resp.get('userPrincipalName')
            self.application.settings['db'].update_user(msft_user['person_id'], {"email":user_email})
            counter = 0
            pmi_meetings = []
            since_day = datetime.now().strftime('%Y-%m-%dT%H:%M')
            #next_day = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT00:00')
            #$filter=sender/emailAddress/address+eq+'{0}'&$select=subject,body,toRecipients
            #get_events_url = "/me/calendar/events$filter=organizer/emailAddress/address+eq+'{0}'&$select=attendees,body,location,start,end,subject,hasAttachments,bodyPreview,id,transactionId,originalStartTimeZone,originalEndTimeZone,recurrence"
            #Additional $select parameters that may be worthwhile, are:
            #hasAttachments, bodyPreview, transactionId
            #get_events_url = "https://graph.microsoft.com/v1.0/me/calendar/events?$select=seriesMasterId,type,occurrenceId,attendees,body,location,start,end,subject,originalStartTimeZone,originalEndTimeZone,recurrence,isOrganizer&$filter=isOrganizer+eq+true"
            get_events_url = "https://graph.microsoft.com/v1.0/me/calendar/events?$select=type,attendees,body,location,start,end,subject,originalStartTimeZone,recurrence,isOrganizer"
            get_events_url += "&$filter=(isorganizer+eq+true)+and+((start/dateTime+ge+'{0}')+or+(type+eq+'seriesMaster'))&$orderby=start/dateTime".format(since_day)
            while get_events_url != None and counter < 20: #If meetings are missing, we can try increasing this counter
                print('get_events_url:{0}'.format(get_events_url))
                resp, msft_user = yield msftGET(get_events_url, msft_user)
                print("events found in this iteration:{0}".format(len(resp.get('value'))))
                counter = 1
                for value in resp.get('value'):
                    print(counter)
                    print("Subject:{0}".format(value['subject']))
                    print(value)
                    attendees = []
                    search_found_splits = None
                    msft_recur = value.get('recurrence')
                    if msft_recur:
                        if msft_recur.get('range') and msft_recur['range'].get('type') == 'endDate':
                            if msft_recur['range'].get('endDate') < since_day:
                                continue
                        if msft_recur.get('pattern') and msft_recur['pattern'].get('interval', 0) > 1:
                            next_time, msft_user = yield self.get_next_msft_instance(value['id'], msft_user)
                            if next_time != "":
                                msft_recur.update({'next':next_time})
                            
                    if search_term in value['location']['displayName']:
                        print('found {0} meeting in content location.'.format(search_term))
                        search_found_splits =  value['location']['displayName'].split(search_term)
                    elif search_term in value['body']['content']:
                        print('found {0} meeting in content body.'.format(search_term))
                        search_found_splits = value['body']['content'].split(search_term)
                    if search_found_splits != None:
                        for attendee in value['attendees']:
                            attendees.append(attendee['emailAddress']['address'])
                        start_msft = datetime.fromisoformat(value['start']['dateTime'][:23])
                        end_msft = datetime.fromisoformat(value['end']['dateTime'][:23])
                        duration_msft = int((end_msft - start_msft).seconds/60)

                        #TODO: for meeting series, I'm trying to figure out next occurrence of complex recurring meetings
                        # based on recurrence object in main.js.  I could just get the actual next occurrence instead with graph api
                        # ... not to mention some of my recurrence/next occurence calculations are wrong in main.js (like last friday of every month)
                        my_object = {"msft_id": value['id'],
                                     "subjects":[value['subject']],
                                     "attendees": attendees,
                                     "start_msft": value['start'],
                                     "end_msft": value['end'],
                                     "recurrence_msft": msft_recur,
                                     "start_tz_msft":value['originalStartTimeZone'],
                                     "duration_msft":duration_msft}

                        #This overwrites the zoom start_time with the one from mircosoft events.
                        #Reason is, zoom tends to provide last occurence in a series as the start_time - not helpful.
                        if my_object["start_msft"] not in [None,""] and my_object["start_msft"]["dateTime"]:
                            my_object["start_time"] = my_object["start_msft"]["dateTime"].rsplit(".",1)[0] + "Z"

                        temp_ids = []
                        if version != None:
                            temp_ids.append(value['id'])
                        else:
                            for split in search_found_splits[1:]:#start at index 1, because 0 will never be a meetingId
                                parts = re.split(r'(?:[@~+=<>?&()])', split, 1)#this splits at the first special character @~+= etc.
                                id_part = parts[0].strip('"\' ')
                                if id_part == search_pmi:
                                    pmi_meetings.append(my_object)
                                elif id_part not in temp_ids:
                                    temp_ids.append(id_part)
                        for temp_id in temp_ids:
                            if temp_id in found_meeting_ids:
                                my_object['subjects'] = list(set(found_meeting_ids[temp_id].get('subjects', [])).union([value['subject']]))
                                my_object['attendees'] = list(set(found_meeting_ids[temp_id].get('attendees', [])).union(attendees))
                                found_meeting_ids[temp_id].update(my_object)
                            else:
                                found_meeting_ids.update({temp_id: my_object})
                get_events_url = resp.get('@odata.nextLink')
                counter += 1
        raise tornado.gen.Return((found_meeting_ids, pmi_meetings, result_object))


    @tornado.gen.coroutine
    def search_command(self, result_object, zoom_user, msft_user, version, search_term):
        print('search_command version:{0}'.format(version))
        #search for webexavengers.zoom.us
        found_meeting_ids = {}
        search_pmi = None
        if version in [None]:
            found_meeting_ids, zoom_user_info, result_object = yield self.search_zoom_meetings(zoom_user, result_object)
            search_term = zoom_user_info['base_url']
            search_pmi = zoom_user_info['pmi']
        if found_meeting_ids != {} or version != None:
            found_meeting_ids, pmi_meetings, result_object = yield self.search_msft_calendar(msft_user, result_object, found_meeting_ids, search_term, search_pmi, version)
            if result_object['code'] == 200:
                #print("found_meeting_ids:{0}".format(found_meeting_ids))
                print("num found_meeting_ids:{0}".format(len(found_meeting_ids)))
                #print("pmi_meetings:{0}".format(pmi_meetings))
                print("num pmi_meetings:{0}".format(len(pmi_meetings)))
                found_meeting_ids.update({'pmi':{'id':search_pmi, 'meetings':pmi_meetings}})
                #print('final:')
                #print(json.dumps(found_meeting_ids))
                result_object['data'] = found_meeting_ids
        raise tornado.gen.Return(result_object)

    @tornado.gen.coroutine
    def transfer_command(self, person, meetings, result_object, msft_user, version):
        print('transfer_command')
        print("meetings:{0}".format(meetings))
        return_data = {}
        for meeting_id in meetings:
            try:
                meeting = meetings[meeting_id]
                result = self.application.settings['db'].find_meeting(meeting_id, person['id'], meeting.get('msft_id'))
                if result != None:
                    return_data.update({meeting_id:result["webex_meeting_id"]})
                else:
                    print("meeting_id:{0}".format(meeting_id))
                    topic = meeting.get('topic', meeting.get('subjects', [None])[0] )
                    zoom_index = topic.lower().find('zoom')
                    if zoom_index >= 0:
                        topic = topic[:zoom_index] + "Webex" + topic[zoom_index+4:]
                    start_time = None
                    try:
                        start_time = parser.parse(meeting['start_time'])
                    except Exception as e:
                        err_result = {'error_reason': 'Invalid StartTime', 'code':400}
                        return_data.update({meeting_id:err_result})
                    if start_time != None:
                        print(meeting['timezone'])
                        start_time = start_time.astimezone(pytz.timezone(meeting['timezone']))
                        print(start_time)
                        print(type(start_time))
                        print(dir(start_time))
                        if meeting.get('duration'):
                            end_time = start_time + timedelta(minutes=meeting['duration'])
                        else:
                            end_time = start_time + timedelta(minutes=meeting['duration_msft'])
                        api_data = {"title":topic,
                                    "start":start_time.isoformat(),
                                    "end":end_time.isoformat(),
                                    "enableAutoRecordMeeting":False,
                                    "sendEmail":True,
                                    "timezone":meeting['timezone']
                                    }
                        invitees = []
                        if(len(meeting.get('attendees', [])) > 0):
                            for attendee in meeting['attendees']:
                                invitees.append({"email":attendee, "coHost":False})
                        print(msft_user.get('email'))
                        print(person.get('emails')[0])
                        if(msft_user.get('email') not in [None, person.get('emails')[0]]):
                            invitees.append({"email":msft_user.get('email'), "coHost":False})#this is in case the user's Webex email address is not the same as their outlook email addr for some reason.
                        if len(invitees) > 0:
                            api_data.update({"invitees":invitees})
                        rrule = ""
                        interval = 1
                        if meeting.get('recurrence_msft') != None:
                            print('msft recurrence')
                            pattern = meeting['recurrence_msft']['pattern']
                            ms_range = meeting['recurrence_msft']['range']
                            interval = 'INTERVAL={0};'.format(pattern['interval'])
                            freq = pattern['type']
                            if freq in ["absoluteMonthly", "relativeMonthly"]:
                                freq = "monthly"
                            freq = 'FREQ={0};'.format(freq.upper())
                            wkst = 'WKST={0};'.format(pattern['firstDayOfWeek'][:2].upper()) #This will usually be sunday and result in SU, which is default RFC 5545, but doesn't hurt to add it
                            byday = ''
                            bymonthday = ''
                            bymonth = ''
                            until = ''
                            indexes = {"first":"1", "second":"2", "third":"3", "fourth":"4", "fifth":"5", "last":"-1"}
                            if pattern.get('daysOfWeek', []) != []:
                                for day in pattern['daysOfWeek']:
                                    byday += '{0}{1}'.format(indexes.get(pattern['index'], ''), day[:2].upper()) #first two letters of weekday, SU, MO, TU, etc
                                if byday != '':
                                    byday = 'BYDAY={0};'.format(byday)
                            elif pattern.get('dayOfMonth') not in [0, None]:
                                bymonthday = 'BYMONTHDAY={0};'.format(pattern['dayOfMonth'])
                            if pattern.get('month', 0) != 0:
                                bymonth = 'BYMONTH={0};'.format(pattern['month'])
                            if ms_range['type'] == 'endDate':
                                rrEndDate = datetime.strptime( ms_range['endDate'], '%Y-%m-%d')
                                rrEndDate = rrEndDate.strftime("%Y%m%d") + "T" + start_time.strftime('%H%M%SZ')
                                until = 'UNTIL={0};'.format(rrEndDate)
                            rrule = '{0}{1}{2}{3}{4}{5}{6}'.format(freq, interval, wkst, byday, bymonthday, bymonth, until)
                        elif meeting.get('recurrence') != None:
                            print('zoom recurrence')
                            weekdays = {1:"SU",2:"MO",3:"TU",4:"WE",5:"TH",6:"FR",7:"SA"}
                            recurrence = meeting['recurrence']

                            interval = 'INTERVAL={0};'.format(recurrence['repeat_interval'])
                            freq = ""
                            byday = ""
                            until = ""
                            count = ""
                            if recurrence.get('monthly_week') != None and recurrence.get('monthly_week_day') != None:
                                freq = 'FREQ=MONTHLY;'
                                byday = 'BYDAY={0}{1};'.format(recurrence.get('monthly_week'), weekdays[recurrence['monthly_week_day']])
                            elif recurrence.get('weekly_days') != None:
                                freq = 'FREQ=WEEKLY;'
                                byday = 'BYDAY={0};'.format(weekdays[int(recurrence['weekly_days'])])
                            elif len(recurrence.keys()) == 3:
                                freq = 'FREQ=DAILY;'
                            if recurrence.get('end_date_time') != None:
                                rrEndDate = datetime.strptime(recurrence['end_date_time'], '%Y-%m-%dT%H:%M:%SZ')
                                rrEndDate = rrEndDate.strftime("%Y%m%dT%H%M%SZ")
                                until = "UNTIL={0};".format(rrEndDate)
                            elif recurrence.get('end_times') != None:
                                count = "COUNT={0};".format(recurrence['end_times'])
                            rrule = '{0}{1}{2}{3}{4}'.format(freq, interval, byday, until, count)
                        print(rrule)
                        if rrule != "":
                            api_data.update({"recurrence":rrule})

                        print("api_data:{0}".format(api_data))
                        try:
                            if version == "fedramp":
                                api_url = 'https://api-usgov.webex.com/v1'
                            else:
                                api_url = 'https://webexapis.com/v1'
                            api_resp = yield Spark(person['token']).post('{0}/meetings'.format(api_url), api_data)
                            print("api_resp.body:{0}".format(api_resp.body))
                            webex_meeting_id = api_resp.body.get('id')
                            result = self.application.settings['db'].insert_meeting(person['id'], person.get('emails', [None])[0], meeting_id, webex_meeting_id, meeting.get('msft_id'))
                            return_data.update({meeting_id:webex_meeting_id})
                        except HTTPError as he:
                            print("transfer_command HTTPError:{0}".format(he))
                            try:
                                jbody = json.loads(he.response.body.decode('utf-8'))
                                print("jbody:{0}".format(jbody))
                                try:
                                    err_msg = jbody['errors'][0]['description']
                                except Exception as e:
                                    print('transfer_command create meeting exception:{0}'.format(e))
                                    err_msg = jbody["msg"]
                            except Exception as ex:
                                err_msg = "An unknown error occurred creating the meeting."
                            err_msg += " trackingId:{0}".format(uuid4().hex)
                            print("err_msg:{0}".format(err_msg))
                            err_result = {'error_reason': err_msg, 'code':he.code}
                            return_data.update({meeting_id:err_result})
            except Exception as e:
                traceback.print_exc()
                err_result = {'error_reason': 'Error:{0}'.format(e), 'code':400}
                return_data.update({meeting_id:err_result})
        if return_data != {}:
            result_object['data'] = return_data
        raise tornado.gen.Return(result_object)


@tornado.gen.coroutine
def main():
    try:
        parse_command_line()
        app = tornado.web.Application([
                (r"/", MainHandler),
                (r"/simplified", SimplifiedHandler),
                (r"/fedramp", FedRampHandler),

                (r"/command", CommandHandler),
                (r"/azure", AzureOAuthHandler),
                (r"/webex-oauth", WebexOAuthHandler),
                (r"/zoom-oauth", ZoomOAuthHandler)
              ],
            template_path=os.path.join(os.path.dirname(__file__), "html_templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret="asducneasciewmfbkohihweabez",
            xsrf_cookies=False,
            debug=options.debug,
            )
        db = ZoomUserDB.db
        app.settings['db'] = db
        #expireAfterSeconds:0 actually means that the document will expire at the datetime specified by expire_date
        db.msft_users.create_index("expire_date", expireAfterSeconds=0)
        db.zoom_users.create_index("expire_date", expireAfterSeconds=0)
        db.meetings.create_index([("person_id", ASCENDING), ("source_meeting_id", ASCENDING)], unique=True)
        server = tornado.httpserver.HTTPServer(app)
        server.bind(Settings.port)
        print("main - Serving... on port {0}".format(Settings.port))
        server.start()
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    main()
