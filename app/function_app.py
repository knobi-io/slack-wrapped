import azure.functions as func
import logging
import json
from urllib.parse import parse_qs

from wrapped import get_wrapped

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="slack_command")
def slack_command(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Received Slack slash command request.')

    # Parse the application/x-www-form-urlencoded payload
    try:
        payload = parse_qs(req.get_body().decode("utf-8"))
    except Exception as e:
        logging.error(f"Error parsing request body: {e}")
        return func.HttpResponse("Invalid request payload", status_code=400)

    # Extract the user_id from the parsed payload
    user_id = payload.get("user_id", [""])[0]  # Extract 'user_id', fallback to empty string

    if user_id:
        #if user_id not in ['U02PXAJBJ0L','U04SERE52HL']:
        #    return func.HttpResponse(
        #        "Shh!! This isn't ready yet... Coming soon!",
        #        status_code=200
        #    )
        
        logging.info(f"Slash command invoked by user: {user_id}")
        wrapped = get_wrapped(user_id)
        if not wrapped:
            logging.warning(f"No data found for user: {user_id}")
            response_payload = {
                "response_type": "ephemeral",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Sorry, <@{user_id}>, we don't seem to have any data for you. :thinking_face: Maybe you weren't very active, or maybe we made a mistake somewhere."
                        }
                    }
                ]
            }
        else:
            response_payload = {
                "response_type": "ephemeral",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": wrapped
                        }
                    }
                ]
            }
        return func.HttpResponse(
            json.dumps(response_payload),
            status_code=200,
            mimetype="application/json"  # Important: Tell Slack you're sending JSON
        )
    else:
        logging.warning("user_id not found in the payload.")
        return func.HttpResponse(
            "Missing user_id in the Slack command payload.",
            status_code=400
        )
