# Module:   webapi
# Date:     10th March 2013
# Author:   James Mills, prologic at shortcircuit dot net dot au

"""Web API

This module implements the RESTful Web API.
"""


from json import loads

from circuits.web import JSONController
from circuits.net.protocols.irc import PRIVMSG


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

        channel = "#{0:s}".format(args[0]) if args else "#circuits"
        payload = loads(kwargs.get("payload", "{}"))

        name = payload.get("repository", {}).get("name", "Unknown")
        commits = payload.get("commits", [])

        self.fire(
            PRIVMSG(
                channel,
                "{0:d} commit(s) pushed to {1:s}".format(
                    len(commits), name
                )
            ),
            "bot"
        )

        for commit in commits:
            self.fire(PRIVMSG(channel, "{0:s} by {1:s}: {2:s}".format(
                commit["node"], commit["author"], commit["message"])), "bot")

        return {"success": True}
