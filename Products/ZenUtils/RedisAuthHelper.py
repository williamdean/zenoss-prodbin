##############################################################################
#
# Copyright (C) Zenoss, Inc. 2015, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
""" Class: RedisAuthHelper
"""
import time
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import default__class_init__ as InitializeClass

from zope.interface import Interface

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.PluggableAuthService.interfaces.plugins import \
        ILoginPasswordHostExtractionPlugin
from Products.PluggableAuthService.interfaces.plugins import \
        ICredentialsUpdatePlugin
from Products.PluggableAuthService.interfaces.plugins import \
        ICredentialsResetPlugin
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements
import redis


class IRedisAuthHelper(Interface):
    """ Marker interface.
    """
manage_addRedisAuthHelperForm = PageTemplateFile(
    'www/saAdd', globals(), __name__='manage_addSessionAuthHelperForm')


def manage_addRedisAuthHelper(dispatcher, id, title=None, REQUEST=None):
    """ Add a Session Auth Helper to a Pluggable Auth Service. """
    sp = RedisAuthHelper(id, title)
    dispatcher._setObject(sp.getId(), sp)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect( '%s/manage_workspace'
                                      '?manage_tabs_message='
                                      'SessionAuthHelper+added.'
                                    % dispatcher.absolute_url() )


class RedisAuthHelper(BasePlugin):
    """ Multi-plugin for managing details of Session Authentication. """
    meta_type = 'Redis Auth Helper'
    security = ClassSecurityInfo()
    deliminator = "|||||"
    cookieName = "ZOPE_SESSION_ID"
    expiresTime = 3600

    def __init__(self, id, title=None):
        self._setId(id)
        self.title = title
        self._v_connection = None

    def _getRedisConnection(self):
        if getattr(self, "_v_connection", None) is None:
            self._v_connection = redis.Redis()
        return self._v_connection

    def _getKey(self, request):
        if not request.cookies.get(self.cookieName):
            request.cookies[self.cookieName] = self.getPhysicalRoot().browser_id_manager.getBrowserId()
            expires = time.time() + (60 * 20)
            request.response.setCookie(self.cookieName, request.cookies[self.cookieName], expires=expires)
        return request.cookies.get(self.cookieName)

    security.declarePrivate('extractCredentials')
    def extractCredentials(self, request):
        """ Extract basic auth credentials from 'request'. """
        creds = {}
        key = self._getKey(request)

        # look in session for cached value first
        name = request.SESSION.get('__ac_name', '')
        password = request.SESSION.get('__ac_password', '')
        if name:
            creds[ 'login' ] = name
            creds[ 'password' ] = password
        else:
            # otherwise see if our token is in redis
            conn = self._getRedisConnection()
            token = conn.get(key)
            if token:
                creds[ 'login' ] = token.split(self.deliminator)[0]
                creds[ 'password' ] = token.split(self.deliminator)[1]
                request.SESSION.set('__ac_name', token.split(self.deliminator)[0])
                request.SESSION.set('__ac_password', token.split(self.deliminator)[1])
            else:
                # Look into the request now
                login_pw = request._authUserPW()

                if login_pw is not None:
                    name, password = login_pw
                    creds[ 'login' ] = name
                    creds[ 'password' ] = password
                    token = name + self.deliminator + password
                    # TODO: encrypt the password so it is in redis in plaintext
                    conn.setex(key, self.expiresTime, token)
                    request.SESSION.set('__ac_name', name)
                    request.SESSION.set('__ac_password', password)
        if creds:
            creds['remote_host'] = request.get('REMOTE_HOST', '')

            try:
                creds['remote_address'] = request.getClientAddr()
            except AttributeError:
                creds['remote_address'] = request.get('REMOTE_ADDR', '')

        return creds

    security.declarePrivate('updateCredentials')
    def updateCredentials(self, request, response, login, new_password):
        """ Respond to change of credentials. """
        token = login + self.deliminator + new_password
        conn = self._getRedisConnection()
        key = self._getKey(request)
        # TODO: encrypt the password so it is in redis in plaintext
        conn.setex(key, self.expiresTime, token)
        request.SESSION.set('__ac_name', login)
        request.SESSION.set('__ac_password', new_password)

    security.declarePrivate('resetCredentials')
    def resetCredentials(self, request, response):
        """ Empty out the currently-stored session values """
        conn = self._getRedisConnection()
        key = self._getKey(request)
        conn.delete(key)
        request.SESSION.set('__ac_name', '')
        request.SESSION.set('__ac_password', '')

classImplements( RedisAuthHelper, IRedisAuthHelper, ILoginPasswordHostExtractionPlugin, ICredentialsUpdatePlugin, ICredentialsResetPlugin)

InitializeClass(RedisAuthHelper)
