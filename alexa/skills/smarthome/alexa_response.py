# -*- coding: utf-8 -*-

# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file except in
# compliance with the License. A copy of the License is located at
#
#    http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import random
import uuid

from .alexa_utils import get_utc_timestamp


class AlexaResponse:

    def __init__(self, **kwargs):

        self.context_properties = []
        self.payload_endpoints = []

        # Set up the response structure
        self.context = {}
        self.event = {
            'header': {
                'namespace': kwargs.get('namespace', 'Alexa'),
                'name': kwargs.get('name', 'Response'),
                'messageId': str(uuid.uuid4()),
                'payloadVersion': kwargs.get('payload_version', '3')
                # 'correlation_token': kwargs.get('correlation_token', 'INVALID')
            },
            'endpoint': {
                "scope": {
                    "type": "BearerToken",
                    "token": kwargs.get('token', 'INVALID')
                },
                "endpointId": kwargs.get('endpoint_id', 'INVALID')
            },
            'payload': kwargs.get('payload', {})
        }

        if 'correlation_token' in kwargs:
            self.event['header']['correlation_token'] = kwargs.get('correlation_token', 'INVALID')

        if 'cookie' in kwargs:
            self.event['endpoint']['cookie'] = kwargs.get('cookie', '{}')

        # No endpoint in an AcceptGrant or Discover request
        if self.event['header']['name'] == 'AcceptGrant.Response' or self.event['header']['name'] == 'Discover.Response':
            self.event.pop('endpoint')

    def add_context_property(self, **kwargs):
        self.context_properties.append(self.create_context_property(**kwargs))

    def add_cookie(self, key, value):

        if "cookies" in self is None:
            self.cookies = {}

        self.cookies[key] = value

    def add_payload_endpoint(self, **kwargs):
        self.payload_endpoints.append(self.create_payload_endpoint(**kwargs))

    def create_context_property(self, **kwargs):
        return {
            'namespace': kwargs.get('namespace', 'Alexa.EndpointHealth'),
            'name': kwargs.get('name', 'connectivity'),
            'value': kwargs.get('value', {'value': 'OK'}),
            'timeOfSample': get_utc_timestamp(),
            'uncertaintyInMilliseconds': kwargs.get('uncertainty_in_milliseconds', 0)
        }

    def create_payload_endpoint(self, **kwargs):
        #    'endpointId': kwargs.get('endpoint_id', 'endpoint_' + "%0.6d" % random.randint(0, 999999)),
        # Return the proper structure expected for the endpoint
            #'endpointId': kwargs.get('endpoint_id', "1846221150263353346"),
        endpoint = {
            'capabilities': kwargs.get('capabilities', []),
            'description': kwargs.get('description', 'WiFi Bulb (353346) connected via Surplife'),
            'displayCategories': kwargs.get('display_categories', ['LIGHT']),
            'endpointId': kwargs.get('endpoint_id', "1846221150263353346"),
            'friendlyName': kwargs.get('friendly_name', 'Ampoule7889'),
              "additionalAttributes":  {
            "manufacturer": "Surplife",
            "firmwareVersion" : "WF.50.35.212.0,V10_ZG-BK2-BP101"
          },
                                  "connections": [
                        {
                          "type": "TCP_IP",
                          "macAddress": "08:65:F0:5A:78:89"
                        }],
            'manufacturerName': kwargs.get('manufacturer_name', 'Surplife')
        }

        if 'cookie' in kwargs:
            endpoint['cookie'] = kwargs.get('cookie', {})

        return endpoint

    def create_payload_endpoint_capability(self, **kwargs):
        capability = {
            'type': kwargs.get('type', 'AlexaInterface'),
            'interface': kwargs.get('interface', 'Alexa'),
            'version': kwargs.get('version', '3')
        }
        supported = kwargs.get('supported', None)
        if supported:
            capability['properties'] = {}
            capability['properties']['supported'] = supported
            capability['properties']['proactivelyReported'] = kwargs.get('proactively_reported', False)
            capability['properties']['retrievable'] = kwargs.get('retrievable', False)
        return capability

    def get(self, remove_empty=True):

        response = {
            'context': self.context,
            'event': self.event
        }

        if len(self.context_properties) > 0:
            response['context']['properties'] = self.context_properties

        if len(self.payload_endpoints) > 0:
            response['event']['payload']['endpoints'] = self.payload_endpoints

        if remove_empty:
            if len(response['context']) < 1:
                response.pop('context')

        return response

    def set_payload(self, payload):
        self.event['payload'] = payload

    def set_payload_endpoint(self, payload_endpoints):
        self.payload_endpoints = payload_endpoints

    def set_payload_endpoints(self, payload_endpoints):
        if 'endpoints' not in self.event['payload']:
            self.event['payload']['endpoints'] = []

        self.event['payload']['endpoints'] = payload_endpoints
