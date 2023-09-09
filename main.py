# echo.py
# Example:
# randomuser - "!echo example string"
# echo_bot - "example string"
import markdown2
import logging
import asyncio
from dataclasses import dataclass
import re
import nio
import simplematrixbotlib as botlib
from atro_args import InputArgs, Arg, arg_source

from my_bot import matrix_helper, openai_helper
from my_bot import ai_types
from my_bot.ai_types import ChatCompletion, ChatCompletionMessage

def get_args(x: str) -> list[str]:
    return [y.strip('"') for y in re.findall(r'(?:[^\s"]+|"[^"]*")', x)]

input_args = InputArgs(
    prefix="MATRIX_BOT_CGPT", 
    args=[
        Arg(name = "HOME"),
        Arg(name = "USERNAME"),
        Arg(name = "PASSWORD"),
        Arg(name = "CGPT_TOKEN"),
        Arg(name = "CREDPATH", required = False, default = "./secrets/session.txt"),
    ]
)
input_args_parsed = input_args.get_dict()

home_url: str = input_args_parsed["HOME"]
creds = botlib.Creds(home_url, input_args_parsed["USERNAME"], input_args_parsed["PASSWORD"], session_stored_file=input_args_parsed["CREDPATH"])
bot = botlib.Bot(creds)
PREFIX = '!'
llm: ai_types.AsyncOpenLlm = openai_helper.LocalLlama(input_args_parsed["CGPT_TOKEN"], "http://localhost:8000")

@dataclass
class CgptArgs:
    message: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.9
    max_tokens: int = -1
    top_p: float = 1
    frequency_penalty: float = 0
    presence_penalty: float = 0
    n: int = 1
    user: str = "user"
    run: bool = True

atro_parser = InputArgs(
    args = [
        Arg(name = "message", other_names=["m"], arg_type = str, required = True),
        Arg(name = "model", other_names=["ml"], arg_type = str, required = False, default="gpt-3.5-turbo"),
        Arg(name = "temperature", other_names=["t"], arg_type = float, required = False, default=0.9),
        Arg(name = "max_tokens", other_names=["mt"], arg_type = int, required = False, default=-1),
        Arg(name = "top_p", other_names=["p"], arg_type = float, required = False, default=1),
        Arg(name = "frequency_penalty", other_names=["fp"], arg_type = float, required = False, default=0),
        Arg(name = "presence_penalty", other_names=["pp"], arg_type = float, required = False, default=0),
        Arg(name = "n", other_names=["n"], required = False, arg_type = int, default=1),
        Arg(name = "user", other_names=["u"], required = False, arg_type = str, default="user"),
        Arg(name = "run", other_names=["r"], required = False, arg_type = bool, default=True)
    ],
    sources = [
        arg_source.ArgSource.cli_args
    ]
)

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
    !clear - clear message history
    !help - shows this help message
        """
    )

@bot.listener.on_message_event
async def cmd_help(room: nio.rooms.MatrixRoom, message: nio.RoomMessageText):
    if(message.sender == creds.username): return
    if(message.body.startswith(f"{PREFIX}help")):
        await cli_help(bot, room)

@bot.listener.on_message_event
async def cmd_clear(room: nio.rooms.MatrixRoom, message: nio.RoomMessageText):
    if(message.sender == creds.username): return

async def cli_message2(bot: botlib.Bot, room: nio.rooms.MatrixRoom, args: CgptArgs):
    await bot.api.async_client.room_typing(room.room_id, timeout=1000 * 120) # start typing indicator
    history: list[ChatCompletionMessage] = []
    
    async for result in matrix_helper.recursive_message(bot, room, 100, 10):
        if result[0] is not None: break
        if len(history) >= 10: break

        msg = result[1]
        if not isinstance(msg, nio.RoomMessageText): continue
        if msg.body.startswith(f"{PREFIX}ERROR"): continue
        if msg.body.startswith(f"{PREFIX}DEBUG"): continue

        # message from cgpt
        if msg.sender == creds.username:
            history.append(ChatCompletionMessage(role="assistant", content=msg.body))
            continue
        # not a cgpt request
        if msg.body.startswith(f"{PREFIX}clear"): break
        if not msg.body.startswith(f"{PREFIX}cgpt"): continue

        # we have cgpt request
        input_str = " ".join(msg.body.split(" ")[1:])
        split_args: list[str] = get_args(input_str)
        try:
            __cargs = CgptArgs(**atro_parser.get_dict(split_args))
        except Exception as e:
            logging.error(f"!ERROR\nIgnoring message due to parsing error:\n{e}\n\nMessage:\n{msg.body}")
            continue
        logging.debug(f"!DEBUG\nParsed args:\n{__cargs}")
        history.append(ChatCompletionMessage(role="user", content=__cargs.message))
    history.reverse()

    logging.debug(f"!DEBUG\nHistory:\n{history}")
    completion: ChatCompletion = await llm.acreate_chat_completion(
            history
        ) # type: ignore
    logging.debug(f"!DEBUG\nCompletion:\n{completion}")
    msg = completion["choices"][0]["message"]["content"]
    await bot.api._send_room(
        room.room_id,
        {
            "msgtype": "m.text",
            "body": msg,
            "format": "org.matrix.custom.html",
            "formatted_body": markdown2.markdown(msg)
        }
    )
    await bot.api.async_client.room_typing(room.room_id, False) # start typing indicator

@bot.listener.on_message_event
async def cmd_completion(room: nio.rooms.MatrixRoom, message: nio.RoomMessageText):
    if(message.sender == creds.username): return
    if(not message.body.startswith(f"{PREFIX}cgpt")): return

    # check for commands
    tmp = message.body.split(" ")[1:]
    if(len(tmp) == 0):
        await cli_help(bot, room)
        return
    
    ## Running cgpt
    input_str = " ".join(tmp)
    split_args: list[str] = get_args(input_str)
    logging.debug(f"!DEBUG\nRaw args:\n{split_args}")
    try:
        __dict = atro_parser.get_dict(split_args)
    except Exception as e:
        logging.debug(f"!DEBUG\nIgnoring message due to parsing error:\n{e}\n\nMessage:\n{message.body}")
        return
    __arg = CgptArgs(**__dict)
    if __arg.user != "user":
        return
    if not __arg.run:
        return
    logging.debug(f"{PREFIX}DEBUG:\nRunning cgpt... with atro args with dataclass:\n{__arg}")
    return await cli_message2(bot, room, __arg)

loop = asyncio.get_event_loop()
loop.run_until_complete(bot.main())