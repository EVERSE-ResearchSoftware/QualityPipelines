#!/usr/bin/env python3

import http.client
import os
from resqui.version import version


class APIClient:
    endpoint_url = "api.dashverse.cloud"

    def __init__(self, bearer_token=None):
        if bearer_token is None:
            bearer_token = os.environ.get("DASHVERSE_TOKEN")
        if bearer_token is None or bearer_token == "":
            raise ValueError("Missing authentication token")
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            # TODO: turn this into minimal in production
            "Prefer": "return=representation",
            "User-Agent": f"resqui/{version}",
        }

    def post(self, payload):
        conn = http.client.HTTPSConnection(self.endpoint_url)
        conn.request("POST", "/assessment", payload, self.headers)
        res = conn.getresponse()
        status = res.status
        reason = res.reason
        data = res.read().decode("utf-8")
        if not (200 <= status < 300):
            raise RuntimeError(f"Request failed with {status} {reason}: {data}")
