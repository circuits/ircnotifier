# Module:   webapi
# Date:     10th March 2013
# Author:   James Mills, prologic at shortcircuit dot net dot au

"""Web API

This module implements the RESTful Web API.
"""


from circuits.web import JSONController


class WebAPI(JSONController):

    channel = "/api"

    def index(self, *args, **kwargs):
        from pprint import pprint
        pprint(args)
        pprint(kwargs)
        return {"success": True}
