#!/usr/bin/env python

from datetime import datetime, date

import endpoints
from protorpc import message_types
from protorpc import remote
from google.appengine.ext import ndb
from models import Profile
from models import ProfileMiniForm
from models import ProfileForm
from models import TeeShirtSize
from models import Conference
from models import ConferenceForm
from models import Session
from models import SessionForm
from models import SessionForms
from models import ConferenceForms
from models import ConferenceQueryForms
from models import BooleanMessage
from models import ConflictException
from utils import getUserId
from settings import WEB_CLIENT_ID
from protorpc import messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from models import StringMessage
from models import Wishlist

MEMCACHE_ANNOUNCEMENTS_KEY = "RECENT_ANNOUNCEMENTS"
MEMCACHE_FEATURED_KEY = "FEATURED_SPEAKERS"
ANNOUNCEMENT_TPL = ('Last chance to attend! The following conferences '
                    'are nearly sold out: %s')

DEFAULTS = {
    "city": "Default City",
    "maxAttendees": 0,
    "seatsAvailable": 0,
    "topics": ["Default", "Topic"],
}

OPERATORS = {
    'EQ': '=',
    'GT': '>',
    'GTEQ': '>=',
    'LT': '<',
    'LTEQ': '<=',
    'NE': '!='
}

FIELDS = {
    'CITY': 'city',
    'TOPIC': 'topics',
    'MONTH': 'month',
    'MAX_ATTENDEES': 'maxAttendees',
}

SESSION_CREATE_REQUEST = endpoints.ResourceContainer(
    SessionForm,
    websafeConferenceKey=messages.StringField(1),
)

SESSION_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
)

SESSION_GET_BY_SPEAKER_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    speaker=messages.StringField(1),
)

SESSION_GET_BY_TYPE = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
    typeOfSession=messages.StringField(2)
)

SESSION_GET_BY_HIGHLIGHT = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
    topicOfSession=messages.StringField(2)
)

SESSION_GET_UPCOMING = endpoints.ResourceContainer(
    message_types.VoidMessage,
    year=messages.IntegerField(1),
    month=messages.IntegerField(2),
    day=messages.IntegerField(3),
)

WISHLIST_ADD_POST_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSessionKey=messages.StringField(1),
)

CONF_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
)

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@endpoints.api(name='conference',
               version='v1',
               allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
               scopes=[EMAIL_SCOPE])
class ConferenceApi(remote.Service):
    """Conference API v0.1"""

    # - - - @Profiles - - - - - - - - - - - - - - - - - - - -

    def _copyProfileToForm(self, prof):
        """Copy relevant fields from Profile to ProfileForm."""
        # copy relevant fields from Profile to ProfileForm
        pf = ProfileForm()
        for field in pf.all_fields():
            if hasattr(prof, field.name):
                # convert t-shirt string to Enum; just copy others
                if field.name == 'teeShirtSize':
                    setattr(pf, field.name,
                            getattr(TeeShirtSize, getattr(prof, field.name)))
                else:
                    setattr(pf, field.name,
                            getattr(prof, field.name))
        pf.check_initialized()
        return pf

    def _getProfileFromUser(self):
        """Return user Profile from datastore.
        Create new one if non-existent."""
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # get Profile from datastore
        user_id = getUserId(user)
        p_key = ndb.Key(Profile, user_id)
        profile = p_key.get()
        # create new Profile if not there
        if not profile:
            profile = Profile(
                key=p_key,
                displayName=user.nickname(),
                mainEmail=user.email(),
                teeShirtSize=str(TeeShirtSize.NOT_SPECIFIED),
            )
            profile.put()

        return profile  # return Profile

    def _doProfile(self, save_request=None):
        """Get user Profile and return to user, possibly updating it first."""
        # get user Profile
        prof = self._getProfileFromUser()

        # if saveProfile(), process user-modifyable fields
        if save_request:
            for field in ('displayName', 'teeShirtSize'):
                if hasattr(save_request, field):
                    val = getattr(save_request, field)
                    if val:
                        setattr(prof, field, str(val))
            prof.put()

        # return ProfileForm
        return self._copyProfileToForm(prof)

    @endpoints.method(message_types.VoidMessage, ProfileForm,
                      path='profile', http_method='GET', name='getProfile')
    def getProfile(self, request):
        """Return user profile."""
        return self._doProfile()

    @endpoints.method(ProfileMiniForm, ProfileForm,
                      path='profile', http_method='POST', name='saveProfile')
    def saveProfile(self, request):
        """Update & return user profile."""
        return self._doProfile(request)

    # - - - @Conferences - - - - - - - - - - - - - - - - - - - -

    def _copyConferenceToForm(self, conf, displayName):
        """Copy relevant fields from Conference to ConferenceForm."""
        cf = ConferenceForm()
        for field in cf.all_fields():
            if hasattr(conf, field.name):
                # convert Date to date string; just copy others
                if field.name.endswith('Date'):
                    setattr(cf, field.name, str(getattr(conf, field.name)))
                else:
                    setattr(cf, field.name, getattr(conf, field.name))
            elif field.name == "websafeKey":
                setattr(cf, field.name, conf.key.urlsafe())
        if displayName:
            setattr(cf, 'organizerDisplayName', displayName)
        cf.check_initialized()
        return cf

    def _createConferenceObject(self, request):
        """Create or update Conference object,
        returning ConferenceForm/request."""

        # preload necessary data items
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        if not request.name:
            raise endpoints.BadRequestException("Conference 'name'"
                                                " field required")

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name)
                for field in request.all_fields()}
        del data['websafeKey']
        del data['organizerDisplayName']

        # add default values for those missing
        # (both data model & outbound Message)
        for df in DEFAULTS:
            if data[df] in (None, []):
                data[df] = DEFAULTS[df]
                setattr(request, df, DEFAULTS[df])

        # convert dates from strings to Date objects;
        # set month based on start_date
        if data['startDate']:
            data['startDate'] = datetime.strptime(
                data['startDate'][:10], "%Y-%m-%d").date()
            data['month'] = data['startDate'].month
        else:
            data['month'] = 0
        if data['endDate']:
            data['endDate'] = datetime.strptime(
                data['endDate'][:10], "%Y-%m-%d").date()

        # set seatsAvailable to be same as maxAttendees on creation
        # both for data model & outbound Message
        if data["maxAttendees"] > 0:
            data["seatsAvailable"] = data["maxAttendees"]
            setattr(request, "seatsAvailable", data["maxAttendees"])

        # make Profile Key from user ID
        p_key = ndb.Key(Profile, user_id)
        # allocate new Conference ID with Profile key as parent
        c_id = Conference.allocate_ids(size=1, parent=p_key)[0]
        # make Conference key from ID
        c_key = ndb.Key(Conference, c_id, parent=p_key)
        data['key'] = c_key
        data['organizerUserId'] = request.organizerUserId = user_id

        # create Conference, send email to organizer confirming
        # creation of Conference & return (modified) ConferenceForm
        Conference(**data).put()
        taskqueue.add(params={'email': user.email(),
                              'conferenceInfo': repr(request)},
                      url='/tasks/send_confirmation_email'
                      )

        return request

    @endpoints.method(ConferenceForm, ConferenceForm, path='conference',
                      http_method='POST', name='createConference')
    def createConference(self, request):
        """Create new conference."""
        return self._createConferenceObject(request)

    @endpoints.method(ConferenceQueryForms, ConferenceForms,
                      path='queryConferences',
                      http_method='POST',
                      name='queryConferences')
    def queryConferences(self, request):
        """Query for conferences."""

        # return individual ConferenceForm object per Conference
        conferences = self._getQuery(request)
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, "")
                   for conf in conferences]
        )

    # - - - @Sessions - - - - - - - - - - - - - - - - - - - -

    @endpoints.method(SESSION_CREATE_REQUEST, SessionForm,
                      path='conference/{websafeConferenceKey}/session',
                      http_method='POST', name='createSession')
    def createSession(self, request):
        """Create new session."""
        return self._createSessionObject(request)

    @endpoints.method(WISHLIST_ADD_POST_REQUEST, BooleanMessage,
                      path='wishlist/add/{websafeSessionKey}',
                      http_method='POST', name='addSessionToWishlist')
    def addSessionToWishlist(self, request):
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        p_key = ndb.Key(Profile, user_id)

        # see if there is a wishlist already
        query = Wishlist.query(ancestor=p_key)
        session_key = ndb.Key(urlsafe=request.websafeSessionKey)
        if query.count():
            wishlist = query.get()
            wishlist.sessions.append(session_key)
            wishlist.put()
        else:
            w_id = Wishlist.allocate_ids(size=1, parent=p_key)[0]
            w_key = ndb.Key(Wishlist, w_id, parent=p_key)
            data = {}
            data['key'] = w_key
            data['sessions'] = []
            data['sessions'].append(session_key)
            w_key = Wishlist(**data).put()
            print(w_key)
        return BooleanMessage(data=True)

    def _copySessionToForm(self, session, displayName):
        """Copy relevant fields from Session to SessionForm."""
        sf = SessionForm()
        print(sf.all_fields())
        for field in sf.all_fields():
            if hasattr(session, field.name):
                print(field.name, getattr(session, field.name))
                # convert Date to date string; just copy others
                if field.name.endswith('date'):
                    setattr(sf, field.name,
                            str(getattr(session, field.name)))
                elif field.name == "speaker":
                    setattr(sf, field.name,
                            str(getattr(session, field.name).urlsafe()))
                else:
                    setattr(sf, field.name,
                            getattr(session, field.name))
            elif field.name == "websafeKey":
                setattr(sf, field.name, session.key.urlsafe())
        if displayName:
            setattr(sf, 'organizerDisplayName', displayName)
        sf.check_initialized()
        return sf

    @endpoints.method(message_types.VoidMessage, SessionForms,
                      path='getSessionsInWishlist',
                      http_method='GET', name='getSessionsInWishlist')
    def getSessionsInWishlist(self, request):
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        p_key = ndb.Key(Profile, user_id)

        # see if there is a wishlist already
        wishlist = Wishlist.query(ancestor=p_key).get()
        print(wishlist)
        sessions = ndb.get_multi(wishlist.sessions)

        return SessionForms(
            items=[self._copySessionToForm(session, "")
                   for session in sessions]
        )

    def _createSessionObject(self, request):
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        if not request.name:
            raise endpoints.BadRequestException(
                "Session 'name' field required")

        # copy SessionForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name)
                for field in request.all_fields()}
        del data['websafeKey']
        del data['organizerDisplayName']
        del data['websafeConferenceKey']

        if data['date']:
            data['date'] = datetime.strptime(
                data['date'][:10], "%Y-%m-%d").date()

        ndb.Key(Profile, user_id)

        wsck = request.websafeConferenceKey
        conf_key = ndb.Key(urlsafe=wsck)
        conference = conf_key.get()

        if user_id != conference.organizerUserId:
            raise endpoints.UnauthorizedException(
                'Sessions can only be added by the conference organizer!')

        session_id = Session.allocate_ids(size=1,
                                          parent=conf_key)[0]
        s_key = ndb.Key(Session, session_id,
                        parent=conf_key)
        data['key'] = s_key
        speaker = ndb.Key(urlsafe=data['speaker']).get()
        data['speaker'] = speaker.key

        s_key = Session(**data).put()
        session = s_key.get()

        taskqueue.add(params={'speaker_key': speaker.key.urlsafe()},
                      url='/tasks/set_featured_speaker'
                      )

        return self._copySessionToForm(session, speaker.displayName)

    @endpoints.method(SESSION_GET_REQUEST, SessionForms,
                      path='conference/sessions/{websafeConferenceKey}',
                      http_method='GET', name='getConferenceSessions')
    def getConferenceSessions(self, request):
        """Query for sessions."""
        wsck = request.websafeConferenceKey
        conf_key = ndb.Key(urlsafe=wsck)
        sessions = Session.query(ancestor=conf_key)
        return SessionForms(
            items=[self._copySessionToForm(session, "")
                   for session in sessions]
        )

    @endpoints.method(SESSION_GET_BY_TYPE, SessionForms,
                      path='conference/sessions/by_type/'
                           '{websafeConferenceKey}/{typeOfSession}',
                      http_method='GET', name='getConferenceSessionByType')
    def getConferenceSessionByType(self, request):
        """Query for sessions."""
        wsck = request.websafeConferenceKey
        conf_key = ndb.Key(urlsafe=wsck)
        query = Session.query(ancestor=conf_key)
        sessions = query.filter(Session.type == request.typeOfSession)
        return SessionForms(
            items=[self._copySessionToForm(session, "")
                   for session in sessions]
        )

    @endpoints.method(SESSION_GET_BY_HIGHLIGHT, SessionForms,
                      path='conference/sessions/by_highlights/'
                           '{websafeConferenceKey}/{topicOfSession}',
                      http_method='GET',
                      name='getConferenceSessionByHighlight')
    def getConferenceSessionByHighlight(self, request):
        """Query for sessions."""
        wsck = request.websafeConferenceKey
        conf_key = ndb.Key(urlsafe=wsck)
        query = Session.query(ancestor=conf_key)
        sessions = query.filter(Session.highlights == request.topicOfSession)
        print(sessions)
        return SessionForms(
            items=[self._copySessionToForm(session, "")
                   for session in sessions]
        )

    # BadRequestError: Only one inequality filter per query is supported.
    # Encountered both type and startTime
    @endpoints.method(message_types.VoidMessage, SessionForms,
                      path='getConferenceSessionsQueryProblem',
                      http_method='GET',
                      name='getConferenceSessionsQueryProblem')
    def getConferenceSessionsQueryProblem(self, request):
        """Query for sessions."""
        query = Session.query()
        query = query.filter(Session.type != "workshop")
        sessions = query.filter(Session.startTime.IN(list(range(1, 19))))
        return SessionForms(
            items=[self._copySessionToForm(session, "")
                   for session in sessions]
        )

    @endpoints.method(SESSION_GET_BY_SPEAKER_REQUEST, SessionForms,
                      path='speaker/sessions/{speaker}',
                      http_method='GET', name='getSessionsBySpeaker')
    def getSessionsBySpeaker(self, request):
        """Query for sessions."""
        speaker_key = ndb.Key(urlsafe=request.speaker)
        query = Session.query()
        filter = ndb.query.FilterNode("speaker", "=", speaker_key)
        sessions = query.filter(filter)
        return SessionForms(
            items=[self._copySessionToForm(session, "")
                   for session in sessions]
        )

    @endpoints.method(SESSION_GET_UPCOMING, SessionForms,
                      path='sessions/upcoming/{year}/{month}/{day}',
                      http_method='GET', name='getUpcomingSessions')
    def getUpcomingSessions(self, request):
        """Query for sessions."""
        prof = self._getProfileFromUser()  # get user Profile
        conf_keys = [ndb.Key(urlsafe=wsck)
                     for wsck in prof.conferenceKeysToAttend]

        input_date = date(request.year, request.month, request.day)

        # loop through all sessions in all registered for conferences
        # to get list of upcoming sessions for a given date
        sessions = []
        for conf_key in conf_keys:
            new_sessions = Session.query(ancestor=conf_key)
            filter = ndb.query.FilterNode("date", "=", input_date)
            new_sessions = new_sessions.filter(filter)
            sessions.append(new_sessions)

        return SessionForms(
            items=[self._copySessionToForm(session, "")
                   for session in sessions]
        )

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='getConferencesCreated',
                      http_method='POST', name='getConferencesCreated')
    def getConferencesCreated(self, request):
        """Return conferences created by user."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # make profile key
        p_key = ndb.Key(Profile, getUserId(user))
        # create ancestor query for this user
        conferences = Conference.query(ancestor=p_key)
        # get the user profile and display name
        prof = p_key.get()
        displayName = getattr(prof, 'displayName')
        # return set of ConferenceForm objects per Conference
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, displayName)
                   for conf in conferences]
        )

    # - - - @ConferenceFilters - - - - - - - - - - - - - - - - - - - -

    def _getQuery(self, request):
        """Return formatted query from the submitted filters."""
        q = Conference.query()
        inequality_filter, filters = self._formatFilters(request.filters)

        # If exists, sort on inequality filter first
        if not inequality_filter:
            q = q.order(Conference.name)
        else:
            q = q.order(ndb.GenericProperty(inequality_filter))
            q = q.order(Conference.name)

        for filtr in filters:
            if filtr["field"] in ["month", "maxAttendees"]:
                filtr["value"] = int(filtr["value"])
            formatted_query = ndb.query.FilterNode(filtr["field"],
                                                   filtr["operator"],
                                                   filtr["value"])
            q = q.filter(formatted_query)
        return q

    def _formatFilters(self, filters):
        """Parse, check validity and format user supplied filters."""
        formatted_filters = []
        inequality_field = None

        for f in filters:
            filtr = {field.name: getattr(f, field.name)
                     for field in f.all_fields()}

            try:
                filtr["field"] = FIELDS[filtr["field"]]
                filtr["operator"] = OPERATORS[filtr["operator"]]
            except KeyError:
                raise endpoints.BadRequestException(
                    "Filter contains invalid field or operator.")

            # Every operation except "=" is an inequality
            if filtr["operator"] != "=":
                # check if inequality operation has been used in
                # previous filters. disallow the filter if inequality
                # was performed on a different field before. track the field
                # on which the inequality operation is performed
                if inequality_field and inequality_field != filtr["field"]:
                    raise endpoints.BadRequestException(
                        "Inequality filter is allowed on only one field.")
                else:
                    inequality_field = filtr["field"]

            formatted_filters.append(filtr)
        return (inequality_field, formatted_filters)

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='filterTest',
                      http_method='GET', name='filterTest')
    def filterTest(self, request):
        q = Conference.query()
        q = q.filter(Conference.city == "London")
        q = q.filter(Conference.topics == "Medical Innovations")
        q = q.order(Conference.name)
        q = q.filter(Conference.maxAttendees > 6)

        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, "") for conf in q]
        )

    # - - -  @Registration - - - - - - - - - - - - - - - - - - - -

    @ndb.transactional(xg=True)
    def _conferenceRegistration(self, request, reg=True):
        """Register or unregister user for selected conference."""
        retval = None
        prof = self._getProfileFromUser()  # get user Profile

        # check if conf exists given websafeConfKey
        # get conference; check that it exists
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % wsck)

        # register
        if reg:
            # check if user already registered otherwise add
            if wsck in prof.conferenceKeysToAttend:
                raise ConflictException(
                    "You have already registered for this conference")

            # check if seats avail
            if conf.seatsAvailable <= 0:
                raise ConflictException(
                    "There are no seats available.")

            # register user, take away one seat
            prof.conferenceKeysToAttend.append(wsck)
            conf.seatsAvailable -= 1
            retval = True

        # unregister
        else:
            # check if user already registered
            if wsck in prof.conferenceKeysToAttend:

                # unregister user, add back one seat
                prof.conferenceKeysToAttend.remove(wsck)
                conf.seatsAvailable += 1
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        prof.put()
        conf.put()
        return BooleanMessage(data=retval)

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='conferences/attending',
                      http_method='GET', name='getConferencesToAttend')
    def getConferencesToAttend(self, request):
        """Get list of conferences that user has registered for."""
        prof = self._getProfileFromUser()  # get user Profile
        conf_keys = [ndb.Key(urlsafe=wsck)
                     for wsck in prof.conferenceKeysToAttend]
        conferences = ndb.get_multi(conf_keys)

        # get organizers
        organisers = [ndb.Key(Profile, conf.organizerUserId)
                      for conf in conferences]
        profiles = ndb.get_multi(organisers)

        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName

        # return set of ConferenceForm objects per Conference
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf,
                                              names[conf.organizerUserId])
                   for conf in conferences]
        )

    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
                      path='conference/{websafeConferenceKey}',
                      http_method='POST', name='registerForConference')
    def registerForConference(self, request):
        """Register user for selected conference."""
        return self._conferenceRegistration(request)

    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
                      path='conference/{websafeConferenceKey}',
                      http_method='DELETE', name='unregisterFromConference')
    def unregisterFromConference(self, request):
        """Unregister user for selected conference."""
        return self._conferenceRegistration(request, reg=False)

    # - - - @Speaker - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _setFeatured(speaker_key):
        key = ndb.Key(urlsafe=speaker_key)
        speaker = key.get()
        query = Session.query()
        filter = ndb.query.FilterNode("speaker", "=", key)
        sessions = query.filter(filter)
        if sessions.count() > 1:
            announcement = 'Current featured speaker is %s, %s %s' % (
                speaker.displayName,
                'giving the following talks:\n',
                '\n '.join(session.name for session in sessions))
            memcache.set(MEMCACHE_FEATURED_KEY, announcement)

    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path='speakers/featured/get',
                      http_method='GET', name='getFeaturedSpeaker')
    def getFeaturedSpeaker(self, request):
        """Return Featured Speakers from memcache."""
        return StringMessage(data=memcache.get(MEMCACHE_FEATURED_KEY) or "")

    # - - - @Announcements - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _cacheAnnouncement():
        """Create Announcement & assign to memcache; used by
        memcache cron job & putAnnouncement().
        """
        confs = Conference.query(ndb.AND(
            Conference.seatsAvailable <= 5,
            Conference.seatsAvailable > 0)
        ).fetch(projection=[Conference.name])

        if confs:
            # If there are almost sold out conferences,
            # format announcement and set it in memcache
            announcement = '%s %s' % (
                'Last chance to attend! The following conferences '
                'are nearly sold out:',
                ', '.join(conf.name for conf in confs))
            memcache.set(MEMCACHE_ANNOUNCEMENTS_KEY, announcement)
        else:
            # If there are no sold out conferences,
            # delete the memcache announcements entry
            announcement = ""
            memcache.delete(MEMCACHE_ANNOUNCEMENTS_KEY)

        return announcement

    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path='conference/announcement/get',
                      http_method='GET', name='getAnnouncement')
    def getAnnouncement(self, request):
        """Return Announcement from memcache."""
        return StringMessage(
            data=memcache.get(MEMCACHE_ANNOUNCEMENTS_KEY) or "")


# registers API
api = endpoints.api_server([ConferenceApi])
