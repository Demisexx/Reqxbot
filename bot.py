#!/usr/bin/env python3


"""Importing"""
# Importing External Packages
from pyrogram import (
    Client,
    filters
)
from pyrogram.types import (
    Update,
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from pyrogram.errors.exceptions.bad_request_400 import (
    PeerIdInvalid,
    UserNotParticipant,
    ChannelPrivate,
    ChatIdInvalid,
    ChannelInvalid
)
from pymongo import MongoClient

# Importing Credentials & Required Data
try:
    from testexp.config import *
except ModuleNotFoundError:
    from config import *

# Importing built-in module
from re import match, search


"""Connecting to Bot"""
app = Client(
    session_name = "RequestTrackerBot",
    api_id = Config.API_ID,
    api_hash = Config.API_HASH,
    bot_token = Config.BOT_TOKEN
)


'''Connecting To Database'''
mongo_client = MongoClient(Config.MONGO_STR)
db_bot = mongo_client['RequestTrackerBot']
collection_ID = db_bot['channelGroupID']


# Regular Expression for #request
requestRegex = "#[rR][eE][qQ][uU][eE][sS][tT] "


"""Handlers"""

# Start & Help Handler
@app.on_message(filters.private & filters.command(["start", "help"]))
async def startHandler(bot:Update, msg:Message):
    botInfo = await bot.get_me()
    await msg.reply_text(
        "<b>Hey There,this is [@GDriveIt] Request Bot 🤖.\n\nThe requests can be registered by typing ( #request ) .\n\nMovies & shows & anime will be uploaded in UPLOADS CHANNEL only.\n\nRest of the things will be handled by Admins itself to access All Links Join Our Google Group.</b>",
        parse_mode = "html",
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📤UPLOADS CHANNEL📤",
                        url = f"https://t.me/GDriveIt"
                    )
                    
                ]
            ]
        )
    )
    return

# return group id when bot is added to group
@app.on_message(filters.new_chat_members)
async def chatHandler(bot:Update, msg:Message):
    if msg.new_chat_members[0].is_self: # If bot is added
        await msg.reply_text(
            f"<b>Hey😁, Your Group ID is <code>{msg.chat.id}</code></b>",
            parse_mode = "html"
        )
    return

# return channel id when message/post from channel is forwarded
@app.on_message(filters.forwarded & filters.private)
async def forwardedHandler(bot:Update, msg:Message):
    forwardInfo = msg.forward_from_chat
    if forwardInfo.type == "channel":   # If message forwarded from channel
        await msg.reply_text(
            f"<b>Hey😁, Your Channel ID is <code>{forwardInfo.id}</code>\n\n</b>",
            parse_mode = "html"
        )
    return

# /add handler to add group id & channel id with database
@app.on_message(filters.private & filters.command("add"))
async def groupChannelIDHandler(bot:Update, msg:Message):
    message = msg.text.split(" ")
    if len(message) == 3:   # If command is valid
        _, groupID, channelID = message
        try:
            int(groupID)
            int(channelID)
        except ValueError:  # If Ids are not integer type
            await msg.reply_text(
                "<b>Group ID & Channel ID should be integer type😒.</b>",
                parse_mode = "html"
            )
        else:   # If Ids are integer type
            documents = collection_ID.find()
            for document in documents:
                try:
                    document[groupID]
                except KeyError:
                    pass
                else:   # If group id found in database
                    await msg.reply_text(
                    "<b>Your Group ID already Added.</b>",
                    parse_mode = "html"
                    )
                    break
                for record in document:
                    if record == "_id":
                        continue
                    else:
                        if document[record][0] == channelID:    #If channel id found in database
                            await msg.reply_text(
                                "<b>Your Channel ID already Added.</b>",
                                parse_mode = "html"
                            )
                            break
            else:   # If group id & channel not found in db
                try:
                    botSelfGroup = await bot.get_chat_member(int(groupID), 'me')
                except (PeerIdInvalid, ValueError):   # If given group id is invalid
                    await msg.reply_text(
                        "<b>😒Group ID is wrong.\n</b>",
                        parse_mode = "html"
                    )
                except UserNotParticipant:  # If bot is not in group
                    await msg.reply_text(
                        "<b>😁Add me in group and make me admin, then use /add.\n</b>",
                        parse_mode = "html"
                    )
                else:
                    if botSelfGroup.status != "administrator":  # If bot is not admin in group
                        await msg.reply_text(
                            "<b>🥲Make me admin in Group, Then add use /add.\n\n</b>",
                            parse_mode = "html"
                        )
                    else:   # If bot is admin in group
                        try:
                            botSelfChannel = await bot.get_chat_member(int(channelID), 'me')
                        except (UserNotParticipant, ChannelPrivate):    # If bot not in channel
                            await msg.reply_text(
                                "<b>😁Add me in Channel and make me admin, then use /add.</b>",
                                parse_mode = "html"
                            )
                        except (ChatIdInvalid, ChannelInvalid): # If given channel id is invalid
                            await msg.reply_text(
                                "<b>😒Channel ID is wrong.\n\n</b>",
                                parse_mode = "html"
                            )
                        else:
                            if not (botSelfChannel.can_post_messages and botSelfChannel.can_edit_messages and botSelfChannel.can_delete_messages):  # If bot has not enough permissions
                                await msg.reply_text(
                                    "<b>🥲Make sure to give Permissions like Post Messages, Edit Messages & Delete Messages.</b>",
                                    parse_mode = "html"
                                )
                            else:   # Adding Group ID, Channel ID & User ID in group
                                collection_ID.insert_one(
                                    {
                                        groupID : [channelID, msg.chat.id]
                                    }
                                )
                                await msg.reply_text(
                                    "<b>Your Group and Channel has now been added SuccessFully🥳.\n\</b>",
                                    parse_mode = "html"
                                )
    else:   # If command is invalid
        await msg.reply_text(
            "<b>Invalid Format😒\nSend Group ID & Channel ID in this format <code>/add GroupID ChannelID</code>.\n</b>",
            parse_mode = "html"
        )
    return

# /remove handler to remove group id & channel id from database
@app.on_message(filters.private & filters.command("remove"))
async def channelgroupRemover(bot:Update, msg:Message):
    message = msg.text.split(" ")
    if len(message) == 2:   # If command is valid
        _, groupID = message
        try:
            int(groupID)
        except ValueError:  # If group id not integer type
            await msg.reply_text(
                "<b>Group ID should be integer type😒.</b>",
                parse_mode = "html"
            )
        else:   # If group id is integer type
            documents = collection_ID.find()
            for document in documents:
                try:
                    document[groupID]
                except KeyError:
                    continue
                else:   # If group id found in database
                    if document[groupID][1] == msg.chat.id: # If group id, channel id is removing by one who added
                        collection_ID.delete_one(document)
                        await msg.reply_text(
                            "<b>Your Channel ID & Group ID has now been Deleted😢 from our Database.\nYou can add them again by using <code>/add GroupID ChannelID</code>.</b>",
                            parse_mode = "html"
                        )
                    else:   # If group id, channel id is not removing by one who added
                        await msg.reply_text(
                            "<b>😒You are not the one who added this Channel ID & Group ID.</b>",
                            parse_mode = "html"
                        )
                    break
            else:   # If group id not found in database
                await msg.reply_text(
                    "<b>Given Group ID is not found in our Database🤔.\n</b>",
                    parse_mode = "html"
                )
    else:   # If command is invalid
        await msg.reply_text(
            "<b>Invalid Command😒\nUse <code>/remove GroupID</code></b>.",
            parse_mode = "html"
        )
    return

# #request handler
@app.on_message(filters.group & filters.regex(requestRegex + "(.*)"))
async def requestHandler(bot:Update, msg:Message):
    groupID = str(msg.chat.id)

    documents = collection_ID.find()
    for document in documents:
        try:
            document[groupID]
        except KeyError:
            continue
        else:   # If group id found in database
            channelID = document[groupID][0]
            fromUser = msg.from_user
            mentionUser = f"<a href='tg://user?id={fromUser.id}'>{fromUser.first_name}</a>"
            requestText = f"<b>Request by {mentionUser}\n\n{msg.text}</b>"
            originalMSG = msg.text
            findRegexStr = match(requestRegex, originalMSG)
            requestString = findRegexStr.group()
            contentRequested = originalMSG.split(requestString)[1]
            
            try:
                groupIDPro = groupID.removeprefix(str(-100))
                channelIDPro = channelID.removeprefix(str(-100))
            except AttributeError:
                groupIDPro = groupID[4:]
                channelIDPro = channelID[4:]

            # Sending request in channel
            requestMSG = await bot.send_message(
                int(channelID),
                requestText,
                reply_markup = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Requested Message",
                                url = f"https://t.me/c/{groupIDPro}/{msg.message_id}"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "🚫Reject",
                                "reject"
                            ),
                            InlineKeyboardButton(
                                "Done✅",
                                "done"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "⚠️Unavailable⚠️",
                                "unavailable"
                            )
                        ]
                    ]
                )
            )
            replyText = f"<b>👋 Hello {mentionUser} !!\n\n📍 Your Request for {contentRequested} has been submitted to the admins.\n\n🚀 Your Request Will Be Uploaded soon.\n\n 📌 Note :- If You Didn't Follow The Request Format Your Request Will be Rejected \n\n 📄 See Request Format by Sending #format \n\n📌 Please Note that Admins might be busy. So, this may take more time.\n\n 🔖Join [@GDriveIt] to Get Updates \n\n👇 See Your Request Status Here </b>"
            
            # Sending message for user in group
            await msg.reply_text(
                replyText,
                parse_mode = "html",
                reply_to_message_id = msg.message_id,
                reply_markup = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⏳Request Status⏳",
                                url = f"https://t.me/c/{channelIDPro}/{requestMSG.message_id}"
                            )
                        ]
                    ]
                )
            )
            break
    return
        
# callback buttons handler
@app.on_callback_query()
async def callBackButton(bot:Update, callback_query:CallbackQuery):
    channelID = str(callback_query.message.chat.id)

    documents = collection_ID.find()
    for document in documents:
        for key in document:
            if key == "_id":
                continue
            else:
                if document[key][0] != channelID:
                    continue
                else:   # If channel id found in database
                    groupID = key

                    data = callback_query.data  # Callback Data
                    if data == "rejected":
                        return await callback_query.answer(
                            "This request is rejected💔...\nSearch in channel and request again",
                            show_alert = True
                        )
                    elif data == "completed":
                        return await callback_query.answer(
                            "This request Is Completed🥳...\nCheckout in Channel😊",
                            show_alert = True
                        )
                    user = await bot.get_chat_member(int(channelID), callback_query.from_user.id)
                    if user.status not in ("administrator", "creator"): # If accepting, rejecting request tried to be done by neither admin nor owner
                        await callback_query.answer(
                            "Wait.....??\nYour are not Admin😒.",
                            show_alert = True
                        )
                    else:   # If accepting, rejecting request tried to be done by either admin or owner
                        if data == "reject":
                            result = "REJECTED"
                            groupResult = "has been Rejected💔."
                            button = InlineKeyboardButton("Request Rejected🚫", "request again")
                        elif data == "done":
                            result = "COMPLETED"
                            groupResult = "is Completed🥳."
                            button = InlineKeyboardButton("Request Completed✅", "completed")
                        elif data == "unavailable":
                            result = "UNAVAILABLE"
                            groupResult = "has been rejected💔 due to Unavailablity🥲."
                            button = InlineKeyboardButton("Request Rejected🚫", "request again")

                        msg = callback_query.message
                        userid = 12345678
                        for m in msg.entities:
                            if m.type == "text_mention":
                                userid = m.user.id
                        originalMsg = msg.text
                        findRegexStr = search(requestRegex, originalMsg)
                        requestString = findRegexStr.group()
                        contentRequested = originalMsg.split(requestString)[1]
                        requestedBy = originalMsg.removeprefix("Request by ").split('\n\n')[0]
                        mentionUser = f"<a href='tg://user?id={userid}'>{requestedBy}</a>"
                        originalMsgMod = originalMsg.replace(requestedBy, mentionUser)
                        originalMsgMod = f"<s>{originalMsgMod}</s>"

                        newMsg = f"<b>{result}</b>\n\n{originalMsgMod}"

                        # Editing reqeust message in channel
                        await callback_query.edit_message_text(
                            newMsg,
                            parse_mode = "html",
                            reply_markup = InlineKeyboardMarkup(
                                [
                                    [
                                        button
                                    ]
                                ]
                            )
                        )

                        # Result of request sent to group
                        replyText = f"<b>Dear {mentionUser}🧑\nYour request for {contentRequested} has Been {groupResult} \n\n<b> ☣️ Follow For More - @GDriveIt </b></b>"
                        await bot.send_message(
                            int(groupID),
                            replyText,
                            parse_mode = "html",
                            reply_markup = InlineKeyboardMarkup(
                                [
                                    [
                                        InlineKeyboardButton(
                                            "📤UPLOAD CHANNEL📤",
                                            url = f"https://t.me/GDriveIt"
                                        )
                                    ]
                                ]
                            )
                        )
                    return
    return


"""Bot is Started"""
print("Bot has been Started!!!")
app.run()
