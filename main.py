# echo.py
# Example:
# randomuser - "!echo example string"
# echo_bot - "example string"
from asyncio import sleep
import nio
import simplematrixbotlib as botlib
from atro_args import InputArgs, Arg

from my_bot import openai_helper
from my_bot.ai_types import ChatCompletion, ChatCompletionMessage

input_args = InputArgs(
    prefix="MATRIX_BOT_CGPT", 
    args=[
        Arg(name = "HOME"),
        Arg(name = "USERNAME"),
        Arg(name = "PASSWORD"),
        Arg(name = "CREDPATH", required = False, default = "./secrets/session.txt"),
        Arg(name = "CGPT_TOKEN"),
    ]
)
args = input_args.get_dict()

home_url: str = args["HOME"]
creds = botlib.Creds(home_url, args["USERNAME"], args["PASSWORD"], session_stored_file=args["CREDPATH"])
bot = botlib.Bot(creds)
PREFIX = '!'
llm = openai_helper.DummyLlm(args["CGPT_TOKEN"])

@bot.listener.on_message_event
async def echo(room: nio.rooms.MatrixRoom, message: nio.RoomMessageText):
    print(f"on_message [{room}] -> {message}")
    if(message.sender == creds.username): return # self detection
    match = botlib.MessageMatch(room, message, bot, PREFIX)

    await bot.api.async_client.room_typing(room.room_id)
    print("sleeping for 3 seconds")
    await sleep(3)
    # await bot.api._send_room(
    #     room.room_id, 
    #     {
    #     "body": "thinks this emote",
    #     "format": "org.matrix.custom.html",
    #     "formatted_body": "thinks <b>this</b> is an example emote",
    #     "msgtype": "m.emote"
    #     }
    # )
    print("sleeping done 3 seconds")
    history: nio.RoomMessagesResponse | nio.RoomMessagesError = await bot.api.async_client.room_messages(
        room.room_id, 
        start="", 
        limit=10, 
        direction=nio.MessageDirection.back
    )
    if not isinstance(history, nio.RoomMessagesError):
        for x in history.chunk: print(x)

    if match.is_not_from_this_bot() and match.prefix() and match.command("echo"):
        await bot.api.send_text_message(
            room.room_id, " ".join(arg for arg in match.args())
        )
    await bot.api.async_client.room_typing(room.room_id, False)

@bot.listener.on_message_event
async def cgpt(room: nio.rooms.MatrixRoom, message: nio.RoomMessageText):
    print(f"on_message [{room}] -> {message}")
    if(message.sender == creds.username): return # self detection
    match = botlib.MessageMatch(room, message, bot, PREFIX)

    await bot.api.async_client.room_typing(room.room_id)
    if match.is_not_from_this_bot() and match.prefix() and match.command("cgpt"):
        completion: ChatCompletion = llm.create_chat_completion(
            [
                ChatCompletionMessage(
                    role="user",
                    content = message.body
                )
            ]
        ) # type: ignore
        print(completion)
        await bot.api.send_text_message(
            room.room_id, completion["choices"][0]["message"]["content"]
        )
    await bot.api.async_client.room_typing(room.room_id, False)

bot.run()