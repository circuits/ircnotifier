# Module:   webapi
# Date:     10th March 2013
# Author:   James Mills, prologic at shortcircuit dot net dot au

"""Web API

This module implements the RESTful Web API.
"""


from json import loads

from circuits.web import JSONController
from circuits.net.protocols.irc import PRIVMSG


BB_UPDATE_TPL = """\
{name:s}: 8{user:s} 12{node:s} {message:s} ({files:s})"""


class WebAPI(JSONController):

    channel = "/api"

    def index(self, *args, **kwargs):
        from pprint import pprint
        pprint(args)
        pprint(kwargs)
        return {"success": True}

    def postcommit(self, *args, **kwargs):
        from pprint import pprint
        pprint(args)
        pprint(kwargs)

        channel = args[0] if args else "#circuits"
        payload = loads(kwargs.get("payload", "{}"))

        name = payload.get("repository", {}).get("name", "Unknown")
        user = payload.get("user", "Anonymous")
        commits = payload.get("commits", [])
        commit = commits and commits[0]
        message = commit.get("message", "")
        node = commit.get("node", "")
        files = commit.get("files", [])
        files = [file["file"] for file in files]

        data = {
            "name": name,
            "user": user,
            "node": node,
            "files": files,
            "message": message
        }

        pprint(data)

        self.fire(PRIVMSG(channel, BB_UPDATE_TPL.format(**data)), "bot")
        return {"success": True}

"""
{u'canon_url': u'https://bitbucket.org',
 u'commits': [{u'author': u'prologic',
               u'branch': u'default',
               u'files': [{u'file': u'hello.txt', u'type': u'added'}],
               u'message': u'Initial Commit',
               u'node': u'e8ce5979e129',
               u'parents': [],
               u'raw_author': u'prologic',
               u'raw_node': u'e8ce5979e129cdbfa1f3c40f4547b8bfa8203261',
               u'revision': 0,
               u'size': -1,
               u'timestamp': u'2013-03-09 15:56:08',
               u'utctimestamp': u'2013-03-09 14:56:08+00:00'}],
 u'repository': {u'absolute_url': u'/prologic/test/',
                 u'fork': False,
                 u'is_private': False,
                 u'name': u'test',
                 u'owner': u'prologic',
                 u'scm': u'hg',
                 u'slug': u'test',
                 u'website': u''},
 u'truncated': False,
 u'user': u'prologic'}
"""
