from main.notify import send_email
from main.dice_roll import roll_dice
from google.genai import types


roll_dice_function = types.FunctionDeclaration(
    name="roll_dice",
    description="Start a dice rolling game between you (the assistant) and the user",
    parameters={"type": "object", "properties": {}},
)

send_email_function = types.FunctionDeclaration(
    name="send_email",
    description=(
        "This function sends an email to Person. Use this function ONLY when a "
        "user explicitly asks you to pass a specific written message to Person. "
        "If the visitor gives you more than one piece of information to relay, "
        "combine them into a single email with one consolidated message rather "
        "than using this function multiple times."
    ),
    parameters={
        "type": "object",
        "properties": {
            "subject": {
                "type": "string",
                "description": "A short, descriptive subject line summarizing the message.",
            },
            "body": {
                "type": "string",
                "description": "The full plain-text message to relay to Person.",
            },
        },
        "required": ["subject", "body"],
    },
)


tools = [types.Tool(function_declarations=[send_email_function, roll_dice_function])]

FUNCTION_MAP = {
    "send_email": send_email,
    "roll_dice": roll_dice,
}