# echo.py
# Example:
# randomuser - "!echo example string"
# echo_bot - "example string"
from asyncio import sleep
import asyncio
import nio
import simplematrixbotlib as botlib
from atro_args import InputArgs, Arg

from my_bot import matrix_helper, openai_helper
from my_bot import ai_types
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
llm: ai_types.AsyncOpenLlm = openai_helper.LocalLlama(args["CGPT_TOKEN"], "http://localhost:8000")

@bot.listener.on_message_event
async def cmd_exit(room: nio.rooms.MatrixRoom, message: nio.RoomMessageText):
    if(message.sender == creds.username): return
    if(message.body.startswith("!exit")):
        await bot.api.send_text_message(room.room_id, "Exiting...")
        exit()

def cli_help(bot: botlib.Bot, room: nio.rooms.MatrixRoom):
    return bot.api.send_text_message(
        room.room_id,
        """
    Commands:
    !exit - exits the program
    !cgpt - runs the cgpt command
    !help - shows this help message
        """
    )

@bot.listener.on_message_event
async def cmd_help(room: nio.rooms.MatrixRoom, message: nio.RoomMessageText):
    if(message.sender == creds.username): return
    if(message.body.startswith("!help")):
        await cli_help(bot, room)

def clean_message(message: str) -> str:
    if not message.startswith("!cgpt"): return message
    return " ".join(message.split(" ")[2:])

async def cli_message(bot: botlib.Bot, room: nio.rooms.MatrixRoom, args: list[str]):
    await bot.api.async_client.room_typing(room.room_id) # start typing indicator

    history: list[ChatCompletionMessage] = []
    async for x in matrix_helper.recursive_message(bot, room, 10, 10):
        if x[0] is not None: break
        if not isinstance(x[1], nio.RoomMessageText): continue
        if x[1].sender == creds.username:
            history.append(ChatCompletionMessage(role="assistant", content=clean_message(x[1].body)))
            continue
        if not x[1].body.startswith("!cgpt"): continue
        __args = x[1].body.split(" ")[1:]
        if __args[0] == "clear": break
        if not __args[0] == "message": continue
        history.append(ChatCompletionMessage(role="user", content=clean_message(x[1].body)))
    history.reverse()

    completion: ChatCompletion = await llm.acreate_chat_completion(
            history
        ) # type: ignore

    # completion: ChatCompletion = llm.create_chat_completion(
    #         history
    #     ) # type: ignore
    await bot.api.send_text_message(
            room.room_id, completion["choices"][0]["message"]["content"]
        )
    await bot.api.async_client.room_typing(room.room_id, False) # start typing indicator

@bot.listener.on_message_event
async def cmd_completion(room: nio.rooms.MatrixRoom, message: nio.RoomMessageText):
    if(message.sender == creds.username): return
    if(not message.body.startswith("!cgpt")): return

    # check for commands
    args = message.body.split(" ")[1:]
    if(len(args) == 0):
        await cli_help(bot, room)
        return
    match args[0]:
        case "help":
            return await cli_help(bot, room)
        case "exit":
            await bot.api.send_text_message(room.room_id, "Exiting...")
            exit()
        case "message":
            return await cli_message(bot, room, args[2:])
        case _:
            return

loop = asyncio.get_event_loop()
loop.run_until_complete(bot.main())
# bot.run()