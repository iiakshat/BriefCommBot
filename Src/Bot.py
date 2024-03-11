import os
import Logger
import random
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import Downloader, Speech_to_Text, Summarizer

log = logging.getLogger(__name__)

BOT_TOKEN = '6917486394:AAEtNxNZyvdI9rcrAt6DI4Q5mcNQsYSDuTo'
BOT_USERNAME = "@BriefcommBot"
user = ''
summary = 'UNAVAILABLE. Please share a text, an audio or a video file to get started.'
transcript = ''
video_title = ''

# COMMANDS :
async def start(update, context):
    global user
    user = update.effective_user
    await update.message.reply_text(f"Hello {user.first_name}! Welcome to BriefCommBot. "
                                  "I will help you summarize contents."
                                  "Please Share a text, an audio or a video file to get started.")
    
async def help(update, context):

    tip = random.choice(["You can use me to dig your ex's call recording and remind them about their promises. ;)",
                       "Bunk your classes without missing out, I can summarize the lectures for you.",
                       "Need an excuse to skip that boring meeting? Let me summarize it for you, so you can pretend you were there!",
                       "Want to impress your crush with your knowledge? Let me summarize that TED talk for you. Just share the youtube url & ALL SETT!! ",
                       "Too tired to cook? Let me summarize that recipe for you. Who needs details anyway?",
                       "Why waste time arguing with your friends? Let me summarize both sides of the debate and settle it once and for all.",
                       ])
    
    await update.message.reply_text("Welcome to BriefCommBot!\n\n"
                    "You can use the following commands:\n\n"
                    "/start - Start a conversation with the bot.\n"
                    "/help - View this help message.\n"
                    "/about - Learn more about BriefCommBot.\n"
                    "/file - To receive last summarised content in a text file.\n\n"

                    f"Tip : {tip}")
    
async def about(update, context):

    about_message = ('''
                    Introducing BriefComm - your virtual audio assistant developed with love by Akshat Sanghvi and Kanika Dogra! 🚀
                    Ever wished you had someone who could summarize any text, video, or audio content effortlessly?
                    Well, say hello to BriefComm!✨\n Here's how it works: Simply send us any audio file - whether it's a lecture,
                    interview, podcast, or even your grandma's legendary storytelling session -
                    and we'll provide you with a crisp summary, saving you time and effort! 💬✨
                    But wait, there's more! With BriefComm, you can also extract key insights from lengthy meetings,
                    breeze through lengthy emails, and even catch up on missed class lectures without breaking a sweat! 📚🔍
                    So, why waste precious time listening to hours of audio when BriefComm can do it for you in minutes? 
                    Get ready to revolutionize the way you consume content - one summarized audio at a time! 🌟
                    
                    Write us at jakshat569@gmail.com or kanika2005dogra@gmail.com 💌
                    '''
                    "\n\n\nDeveloped by Akshat Sanghvi & Kanika Dogra with ❤️\n"
                    "GitHub Repository: https://github.com/iiakshat/BriefComm")
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=about_message)

async def file(update, context):
    global user
    user = update.effective_user

    with open(f'Transcripts/{user}.txt', 'w') as f:
        f.write(summary)
    
    document = open(f'Transcripts/{user}.txt', 'rb')

    await update.message.reply_text("Got it.👍")
    await context.bot.send_document(update.effective_chat.id, document)
    os.remove(f'Transcripts/{user}.txt')

# RESPONSES :

def extractUrl(text):
    import re

    pattern = r'((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?'
    matches = re.findall(pattern, text)

    video_ids = [match[5]+match[6] for match in matches]
    
    url = [f'https://www.youtube.com/watch?v={video_id}' for video_id in video_ids]

    return url[0] if url else None


# If user sends a text other than a link:
def handle_response(text):
    return Summarizer.summarize_text(text)

# If user sends a link :
async def handle_youtube(update, context, url):
    global video_title

    await update.message.reply_text('Downloading...')
    status = Downloader.download(url)
    video_title = Downloader.title
    await context.bot.send_message(chat_id=update.effective_chat.id, text=status)

    await context.bot.send_message(chat_id=update.effective_chat.id, text='Listening...')
    transcript = await transcribe(update, context, video_title)

    lang = Speech_to_Text.detected_lang
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Language : ' + lang)
    summary = await summarise(update, context, transcript)

    return summary

async def transcribe(update, context,video_title):
    global transcript

    await context.bot.send_message(chat_id=update.effective_chat.id, text='Generating Transcripts...')
    transcript = Speech_to_Text.generate_transcript(video_title + '.mp3')
    return transcript

async def summarise(update, context,transcript):
    global summary

    await context.bot.send_message(chat_id=update.effective_chat.id, text='Understanding Context...')
    summary = Summarizer.summarize_text(transcript, category='youtube')

    return summary

# If msg is an audio:
async def audio_handler(update, context):

    audio_file = update.message.audio
    if audio_file:
        file_id = audio_file.file_id

        file = await context.bot.get_file(file_id)
        filename = file.file_path.split('/')[-1]

        file_path = f"Src/Recordings/{filename}"

        log.info('Downloading Began')
        await update.message.reply_text("Audio Recieved. Downloading...")
        await file.download_to_drive(file_path)

        await update.message.reply_text("Audio file saved successfully.")
        await update.message.reply_text("Generating transcript...")
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Listening...')
        transcript = await transcribe(update, context, filename[:-4])

        lang = Speech_to_Text.detected_lang
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Language : ' + lang)
        summary = await summarise(update, context, transcript)

        return await update.message.reply_text(summary)

    else:
        await update.message.reply_text("Please upload an audio file first.")

# Main function
async def handle_message(update, context):

    message_type = update.message.chat.type
    text = update.message.text

    log.debug(f'User {update.message.chat.id} | Message: "{text[:10]}.." | Type: {message_type}')

    # Group Chat :
    if message_type == 'group' and BOT_USERNAME in text:
        text = text.replace(BOT_USERNAME, '').strip()
    
    elif message_type == 'group':
        return

    url = extractUrl(text)

    if url:
        response = await handle_youtube(update, context, url)

    else:

        response = handle_response(text)
    
    print('\n\nBOT:', response, '\n')
    await update.message.reply_text(response)


async def error(update, context):

    await context.bot.send_message(chat_id=update.effective_chat.id, text='Some Error Occured - ' + context.error)
    log.error(context.error)

if __name__ == '__main__':
    print('Bot started...')
    app = Application.builder().token(BOT_TOKEN).build()


    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help))
    app.add_handler(CommandHandler('about', about))
    app.add_handler(CommandHandler('file', file))

    app.add_handler(MessageHandler(filters.AUDIO, audio_handler))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.add_error_handler(error)

    print('Polling...')
    log.debug('Polling...')
    app.run_polling(poll_interval=2)

