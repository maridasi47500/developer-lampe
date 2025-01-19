import json
from alexa.skills.smarthome import AlexaResponse
import requests
import colorsys
import logging
import urllib.request
import urllib.parse
from urllib.error import HTTPError
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

aws_dynamodb = {}
#          North America: https://api.amazonalexa.com/v3/events
#Europe and India: https://api.eu.amazonalexa.com/v3/events
#Far East and Australia: https://api.fe.amazonalexa.com/v3/events
#
client_id = "xxx"
# TODO: Update with your Client Secret for calling the LWA API.
client_secret = "xx"

# TODO: Update with your Endpoint Id.
endpoint_id = "xxx"
access_token_from_amazon='xx'

gateway_endpoint = 'https://api.amazonalexa.com'
malampe =  {"couleur":{
"hue": 350.5,
"saturation": 0.7138,
"brightness": 0.6524
},
"brightness":80,
"temperature":6500,
"power":"OFF",
"endpoint_id":endpoint_id,
"connectivity":{"value": "OK"}
}


def handle_accept_grant(alexa_request):
    auth_code = alexa_request["directive"]["payload"]["grant"]["code"]
    message_id = alexa_request["directive"]["header"]["messageId"]

    # The Login With Amazon API for getting access and refresh tokens from an auth code.
    lwa_token_url = "https://api.amazon.com/auth/o2/token"

    data = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": client_id,
            "client_secret": client_secret
        }
    ).encode("utf-8")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }

    url_request = urllib.request.Request(lwa_token_url, data, headers, "POST")

    try:
        with urllib.request.urlopen(url_request) as response:
            """
            Response will contain the following:
            - access_token: Used in the ChangeReports you send to the Alexa Event Gateway.
            - refresh_token: Used to obtain a new access_token from LWA when this one expires.
            - token_type: Expected token type is Bearer.
            - expires_in: Number of seconds until access_token expires (expected to be 3600, or one hour).
            """
            lwa_tokens = json.loads(response.read().decode("utf-8"))

            # TODO: Save the LWA tokens in a secure location, such as AWS Secrets Manager.
            logger.info("Success!")
            logger.info(f"access_token: {lwa_tokens['access_token']}")
            logger.info(f"refresh_token: {lwa_tokens['refresh_token']}")
            logger.info(f"token_type: {lwa_tokens['token_type']}")
            logger.info(f"expires_in: {lwa_tokens['expires_in']}")
    except HTTPError as http_error:
        logger.error(f"An error occurred: {http_error.read().decode('utf-8')}")

        # Build the failure response to send to Alexa
        response = {
            "event": {
                "header": {
                    "messageId": message_id,
                    "namespace": "Alexa.Authorization",
                    "name": "ErrorResponse",
                    "payloadVersion": "3"
                },
                "payload": {
                    "type": "ACCEPT_GRANT_FAILED",
                    "message": "Failed to retrieve the LWA tokens from the user's auth code."
                }
            }
        }
    else:
        # Build the success response to send to Alexa
        response = {
            "event": {
                "header": {
                    "namespace": "Alexa.Authorization",
                    "name": "AcceptGrant.Response",
                    "messageId": message_id,
                    "payloadVersion": "3"
                },
                "payload": {}
            }
        }

    logger.info(f"accept grant response: {json.dumps(response)}")

    return response


def lambda_handler(event, context):

    # Dump the event for logging - check the CloudWatch logs
    print('lambda_handler event  -----')
    print(json.dumps(event))

    if context is not None:
        print('lambda_handler context  -----')
        print(context)

    # Validate we have an Alexa directive

    if 'request' in event:  # Handle Alexa Custom Skill requests 
        if event['request']['type'] == "LaunchRequest": 
            try: 
                return build_response("Salut ! Dis-moi une couleur.") 
            except Exception as e: 
                print(e) 
                return build_response("Oh là là ! il y a eu une erreur pour lancer la skill.") 
        elif event['request']['type'] == "IntentRequest": 
            return on_intent(event)
    elif 'directive' not in event:
        aer = AlexaResponse(
            name='ErrorResponse',
            payload={'type': 'INVALID_DIRECTIVE',
                     'message': 'Missing key: directive, Is the request a valid Alexa Directive?'})
        return send_response(aer.get())

    # Check the payload version
    payload_version = event['directive']['header']['payloadVersion']
    if payload_version != '3':
        aer = AlexaResponse(
            name='ErrorResponse',
            payload={'type': 'INTERNAL_ERROR',
                     'message': 'This skill only supports Smart Home API version 3'})
        return send_response(aer.get())

    # Crack open the request and see what is being requested
    name = event['directive']['header']['name']
    namespace = event['directive']['header']['namespace']

    # Handle the incoming request from Alexa based on the namespace

    if namespace == 'Alexa.Authorization':
        if name == 'AcceptGrant':
            # Note: This sample accepts any grant request
            # In your implementation you would use the code and token to get and store access tokens
            return handle_accept_grant(event)


    if namespace == 'Alexa.Discovery':
        if name == 'Discover':
            adr = AlexaResponse(namespace='Alexa.Discovery', name='Discover.Response')
            capability_alexa = adr.create_payload_endpoint_capability()
            capability_alexa_powercontroller = adr.create_payload_endpoint_capability(
                interface='Alexa.PowerController',
                proactivelyReported=True,
                retrievable=True,
                supported=[{'name': 'powerState'}])
            capability_alexa_colorcontroller = adr.create_payload_endpoint_capability(
                interface='Alexa.ColorController',
                proactivelyReported=True,
                retrievable=True,
                supported=[{'name': 'color'}])
            c1 = adr.create_payload_endpoint_capability(
                interface='Alexa.ColorTemperatureController',
                proactivelyReported=True,
                retrievable=True,
                supported=[{'name': 'colorTemperatureInKelvin'}])
            c2= adr.create_payload_endpoint_capability(
                interface='Alexa.BrightnessController',
                proactivelyReported=True,
                retrievable=True,
                supported=[{'name': 'brightness'}])
            c3 = adr.create_payload_endpoint_capability(
                interface='Alexa.EndpointHealth',
                proactivelyReported=True,
                retrievable=True,
                supported=[{'name': 'connectivity'}])
            adr.add_payload_endpoint(
                friendly_name='Ampoule7889',
                endpoint_id=malampe["endpoint_id"],
                capabilities=[capability_alexa, capability_alexa_powercontroller,capability_alexa_colorcontroller,c2,c3,c1])
            return send_response(adr.get())

    if namespace == 'Alexa':
        if name == "ReportState":
            # Note: This sample always returns a success response for either a request to TurnOff or TurnOn
            endpoint_id = event['directive']['endpoint']['endpointId']
            correlation_token = event['directive']['header']['correlationToken']
            apcr = AlexaResponse(namespace='Alexa', name='StateReport',correlation_token=correlation_token,endpoint_id=malampe["endpoint_id"],token="surplifetoken")
            apcr.add_context_property(namespace='Alexa.ColorController', name='color', value=malampe["couleur"])
            apcr.add_context_property(namespace='Alexa.ColorTemperatureController', name='colorTemperatureInKelvin', value=malampe["temperature"])
            apcr.add_context_property(namespace='Alexa.PowerController', name='powerState',value=malampe["power"])
            apcr.add_context_property(namespace='Alexa.EndpointHealth', name='connectivity', value={"value": "OK"})
            apcr.add_context_property(namespace='Alexa.BrightnessController', name='brightness', value=malampe["brightness"])

            return send_response(apcr.get())
    if namespace == "Alexa.BrightnessController":
        if name == "SetBrightness":
            endpoint_id = event['directive']['endpoint']['endpointId']
            correlation_token = event['directive']['header']['correlationToken']
            brightness = event['directive']['payload']['brightness']
            malampe["brightness"]=brightness
            payload= {
                "change": {
                    "cause": {
                        "type": "PHYSICAL_INTERACTION"
                    },
                    "properties": [{
                        "namespace": "Alexa.BrightnessController",
                        "name": "brightness",
                        "value": brightness,
                        "timeOfSample": "2022-02-03T08:10:00.10Z",
                        "uncertaintyInMilliseconds": 0
                    }]
                }
            }

            apcr = AlexaResponse(namespace='Alexa', name='ChangeReport', correlation_token=correlation_token, endpoint_id=malampe["endpoint_id"], token="surplifetoken")
            apcr.add_context_property(namespace='Alexa.ColorController', name='color', value=malampe["couleur"])
            apcr.add_context_property(namespace='Alexa.ColorTemperatureController', name='colorTemperatureInKelvin', value=malampe["temperature"])
            apcr.add_context_property(namespace='Alexa.PowerController', name='powerState',value=malampe["power"])
            apcr.add_context_property(namespace='Alexa.EndpointHealth', name='connectivity',value={"value":"ok"})
            #asynchronous request to https://api.amazonalexa.com/v3/events puis
            # Replace these with your actual values
            
            headers = {
                'Authorization': f'Bearer {access_token_from_amazon}',
                'Content-Type': 'application/json'
            }
            data=apcr.get()
            
            response = requests.post(f'{gateway_endpoint}/v3/events', headers=headers, data=json.dumps(data))
            
            # Check the response
            if response.status_code == 200:
                print('Success:', response.json())
            else:
                print('Error:', response.status_code, response.text)
            apcr1 = AlexaResponse(namespace='Alexa', endpoint_id=endpoint_id, name='Response',correlation_token=correlation_token)
            apcr1.add_context_property(
                namespace='Alexa.BrightnessController',
                name='brightness', 
                value=brightness,
                timeOfSample="2019-07-03T16:20:50Z",
                uncertaintyInMilliseconds=500
            )
            
            return send_response(apcr1.get())
    if namespace == 'Alexa.PowerController':
        # Note: This sample always returns a success response for either a request to TurnOff or TurnOn
        endpoint_id = event['directive']['endpoint']['endpointId']
        power_state_value = 'OFF' if name == 'TurnOff' else 'ON'
        correlation_token = event['directive']['header']['correlationToken']
        malampe["power"]=power_state_value

        payload= {
            "change": {
                "cause": {
                    "type": "VOICE_INTERACTION"
                },
                "properties": [{
                    "namespace": "Alexa.PowerController",
                    "name": "powerState",
                    "value": power_state_value,
                    "timeOfSample": "2022-02-03T08:10:00.10Z",
                    "uncertaintyInMilliseconds": 0
                }]
            }
        }

        apcr = AlexaResponse(namespace='Alexa', name='ChangeReport', correlation_token=correlation_token, endpoint_id=malampe["endpoint_id"], token="surplifetoken")
        apcr.add_context_property(namespace='Alexa.ColorController', name='color',value=malampe["couleur"])
        apcr.add_context_property(namespace='Alexa.BrightnessController', name='brightness',value=malampe["brightness"])
        apcr.add_context_property(namespace='Alexa.ColorTemperatureController', name='colorTemperatureInKelvin', value=malampe["temperature"])
        apcr.add_context_property(namespace='Alexa.EndpointHealth', name='connectivity',value={"value":"ok"})
        #asynchronous request to https://api.amazonalexa.com/v3/events puis
        # Replace these with your actual values
        
        headers = {
            'Authorization': f'Bearer {access_token_from_amazon}',
            'Content-Type': 'application/json'
        }
        data=apcr.get()
        
        response = requests.post(f'{gateway_endpoint}/v3/events', headers=headers, data=json.dumps(data))
        
        # Check the response
        if response.status_code == 200:
            print('Success:', response.json())
        else:
            print('Error:', response.status_code, response.text)
        apcr1 = AlexaResponse(namespace='Alexa', endpoint_id=endpoint_id, name='Response',correlation_token=correlation_token)
        apcr1.add_context_property(
            namespace='Alexa.PowerController',
            name='powerState', 
            value=power_state_value,
            timeOfSample="2019-07-03T16:20:50Z",
            uncertaintyInMilliseconds=500
        )
        
        return send_response(apcr1.get())

    if namespace == 'Alexa.ColorController':
        if name == "SetColor":
            # Extract endpoint ID and color values from the request
            endpoint_id = event['directive']['endpoint']['endpointId']
            color = event['directive']['payload']['color']
            hue = color['hue']
            saturation = color['saturation']
            brightness = color['brightness']
            correlation_token = event['directive']['header']['correlationToken']
            # Set the color state in the database
            malampe["couleur"]={
            "hue": hue,
            "saturation": saturation,
            "brightness": brightness}
            # Convert HSB/HSV to RGB
            rgb = colorsys.hsv_to_rgb(hue / 360.0, saturation / 100.0, brightness / 100.0)
            r = int(rgb[0] * 255)
            g = int(rgb[1] * 255)
            b = int(rgb[2] * 255)
            rgb_value = (r, g, b)
            # Convertir RGB en HEX
            hex_value = '#{:02x}{:02x}{:02x}'.format(r, g, b)
            # Create the AlexaResponse with the context property
            payload= {
            "change": {
                "cause": {
                    "type": "PHYSICAL_INTERACTION"
                },
                "properties": [{
                    "namespace": "Alexa.ColorController",
                    "name": "color",
                    "value": {'hue': hue, 'saturation': saturation, 'brightness': brightness},
                    "timeOfSample": "2022-02-03T08:10:00.10Z",
                    "uncertaintyInMilliseconds": 0
                }]
            }
            }
            apcr = AlexaResponse(namespace='Alexa',payload=payload, endpoint_id=endpoint_id, name='ChangeReport', correlation_token=correlation_token)
            apcr.add_context_property(
                namespace='Alexa.BrightnessController',
                name='brightness',
                value=malampe["brightness"],
                timeOfSample="2019-07-03T16:20:50Z",
                uncertaintyInMilliseconds=500
            )
            apcr.add_context_property(namespace='Alexa.PowerController', name='powerState',value=malampe["power"])
            apcr.add_context_property(namespace='Alexa.ColorTemperatureController', name='colorTemperatureInKelvin', value=malampe["temperature"])
            apcr.add_context_property(namespace='Alexa.EndpointHealth', name='connectivity',value={"value":"ok"})
            #asynchronous request to https://api.amazonalexa.com/v3/events puis
            # Replace these with your actual values
            
            headers = {
                'Authorization': f'Bearer {access_token_from_amazon}',
                'Content-Type': 'application/json'
            }
            data=apcr.get()
            
            response = requests.post(f'{gateway_endpoint}/v3/events', headers=headers, data=json.dumps(data))
            
            # Check the response
            if response.status_code == 200:
                print('Success:', response.json())
            else:
                print('Error:', response.status_code, response.text)
            apcr1 = AlexaResponse(namespace='Alexa', endpoint_id=endpoint_id, name='Response',correlation_token=correlation_token)
            apcr1.add_context_property(
                namespace='Alexa.ColorController',
                name='color', 
                value={'hue': hue, 'saturation': saturation, 'brightness': brightness},
                timeOfSample="2019-07-03T16:20:50Z",
                uncertaintyInMilliseconds=500
            )
            
            return send_response(apcr1.get())
    if namespace == 'Alexa.ColorTemperatureController':
        if name == "SetColorTemperature":
            # Extract endpoint ID and color values from the request
            endpoint_id = event['directive']['endpoint']['endpointId']
            colortemperature = event['directive']['payload']['colorTemperatureInKelvin']
            correlation_token = event['directive']['header']['correlationToken']
            malampe["temperature"]=colortemperature
            # Set the color state in the database #blanc
            malampe["couleur"]={"hue": 350.5, "saturation": 0, "brightness": 100}
            hue=malampe["couleur"]["hue"]
            saturation=malampe["couleur"]["saturation"]
            brightness=malampe["couleur"]["brightness"]
            # Convert HSB/HSV to RGB
            rgb = colorsys.hsv_to_rgb(hue / 360.0, saturation / 100.0, brightness / 100.0)
            r = int(rgb[0] * 255)
            g = int(rgb[1] * 255)
            b = int(rgb[2] * 255)
            rgb_value = (r, g, b)
            # Convertir RGB en HEX
            hex_value = '#{:02x}{:02x}{:02x}'.format(r, g, b)
            # Create the AlexaResponse with the context property
            payload= {
            "change": {
                "cause": {
                    "type": "PHYSICAL_INTERACTION"
                },
                "properties": [
                    {
                    "namespace": "Alexa.ColorController",
                    "name": "color",
                    "value": {'hue': hue, 'saturation': saturation, 'brightness': brightness},
                    "timeOfSample": "2022-02-03T08:10:00.10Z",
                    "uncertaintyInMilliseconds": 0
                },
                    {
                    "namespace": "Alexa.ColorTemperatureController",
                    "name": "colorTemperatureInKelvin",
                    "value": colortemperature,
                    "timeOfSample": "2022-02-03T08:10:00.10Z",
                    "uncertaintyInMilliseconds": 0
                }

                ]
            }
            }
            apcr = AlexaResponse(namespace='Alexa',payload=payload, endpoint_id=endpoint_id, name='ChangeReport', correlation_token=correlation_token)
            apcr.add_context_property(
                namespace='Alexa.BrightnessController',
                name='brightness',
                value=malampe["brightness"],
                timeOfSample="2019-07-03T16:20:50Z",
                uncertaintyInMilliseconds=500
            )
            apcr.add_context_property(namespace='Alexa.PowerController', name='powerState',value=malampe["power"])
            apcr.add_context_property(namespace='Alexa.ColorController', name='color', value=malampe["couleur"])
            apcr.add_context_property(namespace='Alexa.EndpointHealth', name='connectivity',value={"value":"ok"})
            #asynchronous request to https://api.amazonalexa.com/v3/events puis
            # Replace these with your actual values
            
            headers = {
                'Authorization': f'Bearer {access_token_from_amazon}',
                'Content-Type': 'application/json'
            }
            data=apcr.get()
            
            response = requests.post(f'{gateway_endpoint}/v3/events', headers=headers, data=json.dumps(data))
            
            # Check the response
            if response.status_code == 200:
                print('Success:', response.json())
            else:
                print('Error:', response.status_code, response.text)
            apcr1 = AlexaResponse(namespace='Alexa', endpoint_id=endpoint_id, name='Response',correlation_token=correlation_token)
            apcr1.add_context_property(
                namespace='Alexa.ColorController',
                name='color', 
                value={'hue': hue, 'saturation': saturation, 'brightness': brightness},
                timeOfSample="2019-07-03T16:20:50Z",
                uncertaintyInMilliseconds=500
            )
            apcr1.add_context_property(
                namespace='Alexa.ColorTemperatureController',
                name='colorTemperatureInKelvin', 
                value=colortemperature,
                timeOfSample="2019-07-03T16:20:50Z",
                uncertaintyInMilliseconds=500
            )
            
            return send_response(apcr1.get())

    return build_response("Demande non reconnue.")


def send_response(response):
    # TODO Validate the response
    print('lambda_handler response -----')
    print(json.dumps(response))
    return response


def set_device_state(endpoint_id, state, value):
    attribute_key = state + 'Value'
    aws_dynamodb.setdefault('SampleSmartHome', {})
    aws_dynamodb['SampleSmartHome'].setdefault(endpoint_id, {})
    aws_dynamodb['SampleSmartHome'][endpoint_id] = {attribute_key: {'Action': 'PUT', 'Value': {'S': value}}}
    sample_smart_home = {
        endpoint_id: {
            attribute_key: {'Action': 'PUT', 'Value': {'S': value}}
        }
    }
    url = 'https://example.com/api/set_device_state'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=sample_smart_home, headers=headers)
    print(response.json())
    if response.status_code == 200:
        return True
    else:
        return False


def on_intent(event):
    intent_name = event['request']['intent']['name']

    if intent_name == "HelloWorldIntent":
        return build_response("Hello!")
    elif intent_name in ["AMAZON.CancelIntent", "AMAZON.StopIntent"]:
        return build_response("Salut !", True)
    elif intent_name == "AMAZON.HelpIntent":
        return build_response("Comment puis-je vous aider ?")
    elif intent_name == "couleurIntent":
        return handle_couleur_intent(event)
    else:
        return build_response("Je ne comprends pas cette commande.")


def handle_couleur_intent(event):
    # Extract the color slot value
    try:
        color = event['request']['intent']['slots']['color']['value']
        return build_response(f"Vous avez dit la couleur {color}. Voulez-vous changer l'appareil à cette couleur ?")
    except KeyError:
        return build_response("Je n'ai pas compris la couleur. Pouvez-vous répéter ?")


def build_response(speech_text, should_end_session=False):
    return {
        'version': '1.0',
        'response': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': speech_text,
            },
            'shouldEndSession': should_end_session
        }
    }


