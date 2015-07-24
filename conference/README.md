App Engine application for the Udacity training course.

## Products
- [App Engine][1]

## Language
- [Python][2]

## APIs
- [Google Cloud Endpoints][3]

## Setup Instructions
1. Update the value of `application` in `app.yaml` to the app ID you
   have registered in the App Engine admin console and would like to use to host
   your instance of this sample.
2. Update the values at the top of `settings.py` to
   reflect the respective client IDs you have registered in the
   [Developer Console][4].
3. Update the value of CLIENT_ID in `static/js/app.js` to the Web client ID
4. (Optional) Mark the configuration files as unchanged as follows:
   `$ git update-index --assume-unchanged app.yaml settings.py static/js/app.js`
5. Run the app with the devserver using `dev_appserver.py DIR`, and ensure it's running by visiting
   your local server's address (by default [localhost:8080][5].)
6. Generate your client library(ies) with [the endpoints tool][6].
7. Deploy your application.

## Project Modifications
The project was modified from the original one posted on https://github.com/udacity/ud858/tree/master/ConferenceCentral_Complete
to fullfill the requirements for the udacity nanodegree project 4. Below are the additional features added.

#### The conference API now supports sessions. The following session related functions are supported.

* getConferenceSessions(websafeConferenceKey) -- Given a conference, return all sessions

* getConferenceSessionsByType(websafeConferenceKey, typeOfSession) Given a conference, return all sessions of a specified type (eg lecture, keynote, workshop)

* getSessionsBySpeaker(speaker) -- Given a speaker, return all sessions given by this particular speaker, across all conferences

* createSession(SessionForm, websafeConferenceKey) -- open only to the organizer of the conference

Sessions contain the following data, where the model is below. One consideration in designing this was to re-use the existing model of Profile as the speaker as well.
This would allow the speaker to be registered with the same google+ profile as all attendees keeping the models simple. Sessions are created with the conference
as the ancestor allowing efficient queries for all sessions in a conference.

* Session name
* highlights
* speaker
* duration (in hours)
* typeOfSession
* date
* start time (in 24 hour notation so it can be ordered).

```python
class Session(ndb.Model):
    name = ndb.StringProperty()
    highlights = ndb.StringProperty(repeated=True)
    type = ndb.StringProperty()
    date = ndb.DateProperty()
    startTime = ndb.IntegerProperty()  # 24 hour notation
    duration = ndb.FloatProperty()  # hours
    speaker = ndb.KeyProperty(kind='Profile')
```

#### A user wishlist is now supported and backed by the following API methods.

* addSessionToWishlist(SessionKey) -- adds the session to the user's list of sessions they are interested in attending
A wishlist can contain any number of sessions. They do not have to be from the same conference.

* getSessionsInWishlist() -- query for all the sessions in a conference that the user is interested in

#### 2 Additional queries have been added

* getConferenceSessionByHighlight(websafeConferenceKey, highlight)
Allows for filtering of sessions on highlights for a given conference.

* getUpcomingSessions(day)
Get all upcoming sessions on the given day, or today if not specified. Useful for making a calendar of registered
sessions.

#### A method demonstrating the query issue of all non-workshop sessions before 7 pm has been added.

* getConferenceSessionsQueryProblem() - The problem here was that inequality operators are not allowed in combination and the most
instinctive way to do the query is to do type!="workshop" && startTime<19. However, this won't work in ndb. One way to go around it
is to replace the < operator with the IN operator. As we have a limited number of hours in a day(24) we can create a set of all the allowed
ones and use the IN operator to make the query functional and ndb compatible.

#### A task has been added to the creation function of sessions that detects if the speaker already has another sessions and adds the speaker to memcached
as a featured speaker. The following API method can be used to pull featured speakers at a given point.

* getFeaturedSpeaker()

#### Example app

An example app can be found running at stately-avatar-97018.appspot.com. 

[1]: https://developers.google.com/appengine
[2]: http://python.org
[3]: https://developers.google.com/appengine/docs/python/endpoints/
[4]: https://console.developers.google.com/
[5]: https://localhost:8080/
[6]: https://developers.google.com/appengine/docs/python/endpoints/endpoints_tool
