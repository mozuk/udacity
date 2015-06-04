from app import app, login_session
from flask import render_template, flash, redirect, url_for
import random
import string
from app import google, facebook


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    if 'username' in login_session:
        return redirect('/')
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# Disconnect based on provider
@app.route('/logout')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            google.gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            facebook.fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('show_categories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('show_categories'))
