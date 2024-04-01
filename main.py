import requests
import json
import mimetypes
from bs4 import BeautifulSoup
import requests
import telebot
import logging
import os
from datetime import datetime, timedelta
import random
import binascii
import re
from urllib.parse import urlparse, parse_qs
import boto3, secrets
#from webserver import keep_alive

# Replace 'YOUR_TOKEN' with the token you received from BotFather
TOKEN = 'YOUR_TOKEN'
bot = telebot.TeleBot(TOKEN)

# ADMIN ID
sudos = [2110818173]

# Configure logging to save errors to a file
logging.basicConfig(filename='error.log', level=logging.ERROR)

# POINT FOLDER
directories = ["points", "messagstore", "photos"]

for directory in directories:
    if not os.path.exists(directory):
        os.mkdir(directory)
    else:
        print(f"Directory {directory} already exists.")


# ADDED POINT & CHECK POINT FUNCTION
def get_2_point_2_days(user):
    try:
        file_path = f"./points/{user}.txt"

        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                exc = file.read().split("||")
                if int(exc[0]) < 1 or datetime.strptime(exc[1], "%Y-%m-%d") < datetime.today():
                    os.remove(file_path)
                    return [0, 0]
                else:
                    earlier = datetime.now()
                    later = datetime.strptime(exc[1], "%Y-%m-%d")
                    abs_diff = (later - earlier).days
                    return [int(exc[0]), abs_diff + 1]
        else:
            return [0, 0]
    except Exception as e:
        print(f"Error: {e}")
        logging.exception(f"Error on {user}: {e}")

# ADDED POINT FUNCTION
def add_2_point_2_days(user, points, days):
    try:
        file_path = f"./points/{user}.txt"

        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                exc = file.read().split("||")

                if datetime.strptime(exc[1], "%Y-%m-%d") >= datetime.today():
                    earlier = datetime.now()
                    later = datetime.strptime(exc[1], "%Y-%m-%d")
                    abs_diff = (later - earlier).days
                    adays = days + abs_diff + 1
                    apoints = points + int(exc[0])
                else:
                    adays = days
                    apoints = points
        else:
            adays = days
            apoints = points

        dt = datetime.now().strftime("%Y-%m-%d")
        txt = f"{apoints}||{datetime.strftime(datetime.strptime(dt, '%Y-%m-%d') + timedelta(days=adays), '%Y-%m-%d')}"

        with open(file_path, 'w') as file:
            file.write(txt)

        return [apoints, adays]
    except Exception as e:
        print(f"Error: {e}")
        logging.exception(f"Error on {user}: {e}")   

# ADDED DEDUCT POINT FUNCTION
def deduct_point(user):
    try:
        file_path = f"./points/{user}.txt"

        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                exc = file.read().split("||")

                if datetime.strptime(exc[1], "%Y-%m-%d") >= datetime.today():
                    earlier = datetime.now()
                    later = datetime.strptime(exc[1], "%Y-%m-%d")
                    abs_diff = (later - earlier).days
                    adays = abs_diff + 1

                    if int(exc[0]) > 0:
                        apoints = int(exc[0]) - 1
                    else:
                        apoints = 0
                else:
                    adays = 0
                    apoints = 0

                dt = datetime.now().strftime("%Y-%m-%d")
                txt = f"{apoints}||{datetime.strftime(datetime.strptime(dt, '%Y-%m-%d') + timedelta(days=adays), '%Y-%m-%d')}"

                with open(file_path, 'w') as file:
                    file.write(txt)

                return [apoints, adays]
        else:
            return [0, 0]

    except Exception as e:
        print(f"Error: {e}")
        logging.exception(f"Error on {user}: {e}")

#check point  & send message        
def check_points(message):
  user_id = message.from_user.id 
  chat_id = message.chat.id
  user = message.from_user.first_name
  pi = get_2_point_2_days(user_id)
  if pi[0] < 1 or pi[1] < 1:
    text22 = f"Hey {user}, Points must be purchased to get the solution.... to buy!"
    reply_markup = telebot.types.InlineKeyboardMarkup()
    reply_markup.add(telebot.types.InlineKeyboardButton(text='Contact Here 💚', url='t.me/spacenx1'))
    bot.send_message(chat_id, text22, reply_markup=reply_markup) 
    print("User does not have enough points.")
    exit()
  else:
    return 

# TOKEN GENERATE
def generate_unique_token(existing_tokens):
  while True:
    gen_token = binascii.hexlify(os.urandom(8)).decode(
        'utf-8')  # 8 bytes = 16 characters in hex
    if gen_token not in existing_tokens:
      return gen_token


# UPLOAD TO AWS S3
def upload_to_s3(file_answer):
  s3 = boto3.client(
      's3',
      region_name='us-east-1',
      aws_access_key_id='AKIAWU5JKPD6RSRHV3J4',
      aws_secret_access_key='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',
      config=boto3.session.Config(signature_version='s3v4'))

  bucket_name = 'supernova558866'
  s3.upload_file(file_answer, 'supernova558866', file_answer)
  link = s3.generate_presigned_url('get_object',
                                   Params={
                                       'Bucket': 'AWSBucketName',
                                       'Key': file_answer
                                   },
                                   ExpiresIn=100000)
  print("\033[92mlink\033[0m")
  existing_tokens = set()  # Assume you're keeping track of generated tokens
  GenToken = generate_unique_token(existing_tokens)
  s3.upload_file(file_answer,
                 bucket_name,
                 f'{GenToken}.html',
                 ExtraArgs={'ContentType': 'text/html'})
  url3 = s3.generate_presigned_url(
      ClientMethod='get_object',
      Params={
          'Bucket': bucket_name,
          'Key': f'{GenToken}.html'
      },
      ExpiresIn=86400  # 1 Day
  )
  return url3


# TELEGRAM COMMAND HANDLERS
@bot.message_handler(commands=['get'])
def get_points(message):
  try:
    user_id = message.from_user.id
    aa = get_2_point_2_days(message.from_user.id)
    directory = "./points"
    files = os.listdir(directory)
    num_files = len(files)
    bot.reply_to(message,f"Your points: {aa[0]}\nYour points expire after: {aa[1]} days\nNumber VIP: {num_files}")
  except Exception as e:
    print(f"Error: {e}")
    logging.exception(f"Error on {user_id}: {e}")


@bot.message_handler(commands=['give'])
def give_points(message):
  try:
    user_id = message.from_user.id
    if message.from_user.id in sudos:
      matches = re.findall(r'\d+', message.text)
      if len(matches) >= 3:
        tr = add_2_point_2_days(int(matches[2]), int(matches[0]),
                                int(matches[1]))
        bot.send_message(int(matches[2]),f"Points added!✅\nYour points: {tr[0]}\nYour points expire after: {tr[1]} days\n\nFor More Point Contact owner: @spacenx1")
        bot.reply_to(
            message,
            f"Your points: {tr[0]}\nYour points expire after: {tr[1]} days")
      else:
        bot.reply_to(
            message,
            'Invalid /give command format. Please use /give {user_id} {points}'
        )
  except Exception as e:
    print(f"Error: {e}")
    logging.exception(f"Error on {user_id}: {e}")


# deletd pont
@bot.message_handler(commands=['del'])
def delete_points(message):
  try:
    user_id = message.from_user.id
    if re.match(r'^\/del (\d+)',
                message.text) and message.from_user.id in sudos:
      reply_id = int(re.search(r'\d+', message.text).group(0))
      file_path = f"./points/{reply_id}.txt"

      if os.path.exists(file_path):
        os.remove(file_path)
        bot.reply_to(message, f"Deleted file: {reply_id}.txt")
      else:
        bot.reply_to(message, f"File not found: {reply_id}.txt")
  except Exception as e:
    print(f"Error: {e}")
    logging.exception(f"Error on {user_id}: {e}")

# LOG
@bot.message_handler(commands=['log'])
def send_error_log(message):
  try:
    user_id = message.from_user.id
    if message.from_user.id in sudos:
      error_file_path = './error.log'
      if os.path.exists(error_file_path):
        with open(error_file_path, 'rb') as error_file:
          bot.send_document(message.chat.id,
                            error_file,
                            caption='Here is the error log file:')
      else:
        bot.reply_to(message, 'Error log file not found.')
  except Exception as e:
    print(f"Error: {e}")
    logging.exception(f"Error on {user_id}: {e}")

# START
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
  try:
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    profile_link = f'<a href="https://t.me/{username}">{first_name}</a>'
    reply_message = f"✨✨Welcome {profile_link}! to VIP Get Answer Bot✨✨\nWe provide Unsolved solutions!"
    reply_message2 = f"Plans for Indians are as follows\n\n🔅UPI ID : @spacenx1\n🔅PayTM link : @spacenx1\n\nRules:-\n\nSend the payment screenshot to @spacenx1 within 5 minutes after the transaction\n\n--> Late payment screenshot will not be accepted; you have to send it within 5 minutes\n\n--> If the transaction failed or is under processing, inform admin\n\n--> Don't send the same payment screenshot from multiple accounts\n\n--> Don't delete bot and admin chats\n\nThank you ❤️\n\nHow to check the remaining balance in the bot\n\nType this command 👉🏽 /get to see your active balance\n\nType this command 👉🏽 /payment to see your payment ID\n\nYour ID: <code>{user_id}</code>\nContact US\n\nSend your queries to @spacenx1"
    reply_message3 = f"Free For All just send  photo get answer!"
    reply_message4 ='''
    🌟 Get Answers Fast! 🚀 

    🤖 BOT:
     @GETANSWERNXBOT

    Looking for solutions to your unsolved questions? You're in the right place! 🧠💡

    ✨ How it Works:
    1. 📸 Capture: Snap a clear picture of your math or science problem.
    2. 🚀 Submit: Send the image to our dedicated Get Answer bot.
    3. 🧐 Receive: Get a prompt response with the solution to your question.

    🌐 Demo: 

    Unlock the door to instant answers! 🗝🔍 Simply follow the steps above and let our Get Answer bot work its magic. Your solution is just a click away! 🌟

    📧 Contact Us:
    Send your queries to @spacenx1.
    '''
    bot.send_message(message.chat.id, reply_message, parse_mode='HTML')
    bot.send_message(message.chat.id, reply_message4, parse_mode='HTML')
    bot.send_message(
        -1001636291714,
        f"✅Status: Ok\nQuestion: {message.text}\nUser Id: {user_id}\nProfile Link: {profile_link}",
        parse_mode='HTML')
  except Exception as e:
    print(f"Error: {e}")
    logging.exception(f"Error on {user_id}: {e}")

# PAYMENT
@bot.message_handler(commands=['payment'])
def send_payment(message):
  try:
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    profile_link = f'<a href="https://t.me/{username}">{first_name}</a>'
    bot.send_message(
        message.chat.id,
        f"✨✨Hey, {profile_link}!\n\nYour ID:  <code>{user_id}</code>\nContact US\n\nSend your ID to @spacenx1",
        parse_mode='HTML')
    bot.send_message(
        -1001636291714,
        f"✅Status: Ok\nQuestion: {message.text}\nUser Id: {user_id}\nProfile Link: {profile_link}",
        parse_mode='HTML')
  except Exception as e:
    print(f"Error: {e}")
    logging.exception(f"Error on {user_id}: {e}")

# DEVICE ID
def device_id():
    try:
        url = 'https://api.szl.ai/users/register_device'
        headers = {
            'authority': 'api.szl.ai',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'dnt': '1',
            'origin': 'https://web.szl.ai',
            'referer': 'https://web.szl.ai/',
            'rid': 'anti-csrf',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'st-auth-mode': 'header',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        }

        payload = '{"signed_token":"eyJ0aW1lc3RhbXAiOjE3MDI3MzIyNDUuMTUyfQ==.2f45d09b034aa2f7615a906415be9e75079aef98419ecbb2a5c7a5bdf30b6007"}'

        response = requests.post(url, headers=headers, data=payload)

        try:
            return response.json()['device_id']
        except ValueError as e:
            print(f"Error decoding JSON: {e}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        logging.exception(f"Error on : {e}")

def ocrmathtext(file_photo,device_id_value):
    try:
        url = f"https://api.szl.ai/steps/ocr_image?device_id={device_id_value}"

        payload = {}
        files=[
        ('file',('file',open(file_photo,'rb'),'application/octet-stream'))
        ]
        headers = {
        'authority': 'api.szl.ai',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
        #'cookie': '_ga=GA1.1.1345243718.1703341827; _gcl_au=1.1.570312565.1703341827; _ga_D3T6T1E0YW=GS1.1.1703417055.2.1.1703417076.0.0.0; SL_C_23361dd035530_SID={"73187e6a1cb9e4df06ea420c2a200e94b8f10fa8":{"sessionId":"a42fsuRYWu0JLqUAhq97x","visitorId":"ZDHQVAeP-rpisy-igYg91"}}',
        'dnt': '1',
        'origin': 'https://web.szl.ai',
        'referer': 'https://web.szl.ai/',
        'rid': 'anti-csrf',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'st-auth-mode': 'header',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        try:
            data = json.loads(response.text)
            if 'error' in data:
                print(f"Error found in response: {data['ocr_text']}")
            else:
                print(data['ocr_text'])
                return data['ocr_text']
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    except Exception as e:
        print(f"Error: {e}")
        logging.exception(f"Error on : {e}")    

def  upload_problem_text(ocr_text,device_id_value):
    try:
        url = f"https://api.szl.ai/steps/upload_problem_text?device_id={device_id_value}"

        payload = json.dumps({"problem_text":f"{ocr_text}"})
        headers = {
        'authority': 'api.szl.ai',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
        'content-type': 'application/json',
        #'cookie': '_ga=GA1.1.1345243718.1703341827; _gcl_au=1.1.570312565.1703341827; _ga_D3T6T1E0YW=GS1.1.1703417055.2.1.1703417076.0.0.0; SL_C_23361dd035530_SID={"73187e6a1cb9e4df06ea420c2a200e94b8f10fa8":{"sessionId":"a42fsuRYWu0JLqUAhq97x","visitorId":"ZDHQVAeP-rpisy-igYg91"}}',
        'dnt': '1',
        'origin': 'https://web.szl.ai',
        'referer': 'https://web.szl.ai/',
        'rid': 'anti-csrf',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'st-auth-mode': 'header',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'x-application-name': 'sizzle-web',
        'x-sent-at-timestamp': '1703417189.962'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        try:
            data = json.loads(response.text)
            if 'error' in data:
                print(f"Error found in response: {data['work_session_id']}")
            else:
                print(data['work_session_id'])
                return data['work_session_id']
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    except Exception as e:
        print(f"Error: {e}")
        logging.exception(f"Error on : {e}")

def generate_steps(work_session_id_value,device_id_value):
    try: 
        url = f"https://api.szl.ai/steps/generate_steps?work_session_id={work_session_id_value}&device_id={device_id_value}"

        headers = {
            'authority': 'api.szl.ai',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
            #'cookie': '_ga=GA1.1.1672837489.1702725997; _gcl_au=1.1.1728332260.1702725997; _ga_D3T6T1E0YW=GS1.1.1702733570.2.1.1702734307.0.0.0; SL_C_23361dd035530_SID={"73187e6a1cb9e4df06ea420c2a200e94b8f10fa8":{"sessionId":"jfxdWaxdVhUFKMezN7PE9","visitorId":"HOuRuJD8J50vX49bEGb_J"}}',
            'dnt': '1',
            'origin': 'https://web.szl.ai',
            'referer': 'https://web.szl.ai/',
            'rid': 'anti-csrf',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'st-auth-mode': 'header',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        }

        response = requests.get(url, headers=headers)

        try:
            print(response.json()['work_session_id'])
            return response.json()['work_session_id']
        except ValueError as e:
            print(f"Error decoding JSON: {e}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        logging.exception(f"Error on : {e}")
'''
def reveal_answer(work_session_id_value, device_id_value):
    max_step_number = 10
    for step_number in range(0, max_step_number + 1):
        print(f"Step:{step_number}")
        url = f"https://api.szl.ai/steps/reveal_answer?work_session_id={work_session_id_value}&step_number={step_number}&device_id={device_id_value}"

        payload = {}
        headers = {
            'authority': 'api.szl.ai',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
            'dnt': '1',
            'origin': 'https://web.szl.ai',
            'referer': 'https://web.szl.ai/',
            'rid': 'anti-csrf',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'st-auth-mode': 'header',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        if response.status_code == 404:
            response_json = {"detail": f"Step number {step_number} not found"}
            print(response_json)
        else:
            try:
                response_json = response.json()
                print(response_json['answer']['answer'])
                return response_json['answer']['answer']
            except ValueError as e:
                print(f"Error decoding JSON: {e}")
                return None
'''  
#SEND MESSAGE TO USER  
def send_documnet_file(message,ocr_text,answer):
    try:
        user_id = message.from_user.id 
        chat_id = message.chat.id
        user = message.from_user.first_name
        '''
        pi=check_points(message)
        pi = get_2_point_2_days(user_id)
        '''
        answerhtml =str("""<!DOCTYPE html><html><head> <meta charset="utf-8"/> <meta name="viewport" content="width=device-width, initial-scale=1"/> <title>NX pro</title> <meta name="description" content=""/> <link rel="shortcut icon" href="assets/img/favicon.ico" type="image/x-icon"/> <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bulma/0.9.3/css/bulma.min.css"/> <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.min.js"></script></head><body> <div class="container" id="app"> <div class="box"> <div class="content"><div class="answer"><h4>Question</h4>"""+str(ocr_text)+"""<br><br><!-- Your answer content goes here --><h4>Answer</h4>"""+str(answer)+"""</div> </div> </div> </div> </div> <script type="text/x-mathjax-config"> MathJax.Hub.Config({ config: ["MMLorHTML.js"], jax: ["input/TeX", "input/MathML", "output/HTML-CSS", "output/NativeMML"], extensions: ["tex2jax.js", "mml2jax.js", "MathMenu.js", "MathZoom.js"], TeX: { extensions: ["AMSmath.js", "AMSsymbols.js", "noErrors.js", "noUndefined.js"] } }); </script> <script type="text/javascript" src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script> <script id="MathJax-script" async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.js"></script></body></html>""")
        file_prefix="answer_"
        folder_name = "UserHtmlfile"
        folder_path = os.path.join(os.path.dirname(__file__), folder_name)

        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)

        existing_tokens = []
        gen_token = generate_unique_token(existing_tokens)
        file_name = f"{file_prefix}{gen_token}.html"

        with open(os.path.join(folder_path, file_name), 'w') as file:
            file.write(str(answerhtml))

        mime_type, _ = mimetypes.guess_type(os.path.join(folder_path, file_name))
        mime_type = mime_type or 'application/octet-stream'

        caption = ''
        bot.send_document(chat_id, open(os.path.join(folder_path, file_name), 'rb'), caption=caption)
        '''
        pd = deduct_point(user_id)
        #Deduct the points after a successful request.
        '''
        aurl = upload_to_s3(os.path.join(folder_path, file_name))
        reply_markup = telebot.types.InlineKeyboardMarkup()
        reply_markup.add(telebot.types.InlineKeyboardButton(text='📚Answer link', url=aurl))
        bot.send_message(chat_id, f"Hey {user}\nYour Answer Given Below", reply_markup=reply_markup)
        bot.send_message(-1001636291714, f"✅Status: Ok\n=\n\nUser Id: {user}")
    except Exception as e:
        print(f"Error: {e}")
        logging.exception(f"Error on :{user_id} {e}")

#PHOTO ISSET
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        user_id = message.from_user.id 
        chat_id = message.chat.id
        user = message.from_user.first_name
        file_photo = message.photo[-1].file_id
        file_path = f"photos/{user_id}.png"
        file_info = bot.get_file(file_photo)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            bot.send_message(chat_id, "Thank you for sharing your photo.")
            '''
            pi=check_points(message)
            pi = get_2_point_2_days(user_id)
            '''
            device_id_value = device_id()
            ocr_text = ocrmathtext(file_path,device_id_value)   
            work_session_id_value=upload_problem_text(ocr_text,device_id_value)
            generate_step=generate_steps(work_session_id_value,device_id_value)
            if generate_step is not None:
                max_step_number = 20
                all_answers = []
                for step_number in range(0, max_step_number + 1):
                    print(f"Step:{step_number}")
                    url = f"https://api.szl.ai/steps/reveal_answer?work_session_id={work_session_id_value}&step_number={step_number}&device_id={device_id_value}"

                    payload = {}
                    headers = {
                        'authority': 'api.szl.ai',
                        'accept': '*/*',
                        'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
                        'dnt': '1',
                        'origin': 'https://web.szl.ai',
                        'referer': 'https://web.szl.ai/',
                        'rid': 'anti-csrf',
                        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Linux"',
                        'sec-fetch-dest': 'empty',
                        'sec-fetch-mode': 'cors',
                        'sec-fetch-site': 'same-site',
                        'st-auth-mode': 'header',
                        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }

                    response = requests.request("GET", url, headers=headers, data=payload)
                    try:
                        if response.status_code == 200:
                            response_json = response.json()
                            if response_json == {"detail": f"Step number {step_number} not found"}:
                                break
                            else:
                                if 'answer' in response_json:
                                    answertext = response_json['answer']['answer']
                                    all_answers.append(answertext)
                                    combined_answers = '<br>'.join(all_answers)
                                    answer = '<p>' +str(combined_answers) + '</p>'
                                else:
                                    print('No More Step')
                                    break
                    except ValueError as e:
                       print(f"Error decoding JSON: {e}")
                send_documnet_file(message,ocr_text,answer)               
            else:
                print(f"answer getting error")
                bot.send_message(message.chat.id, "answer getting error", parse_mode='HTML')
    except Exception as e:
        print(f"Error: {e}")
        logging.exception(f"Error on :{user_id} {e}")


#solve hand text question          
@bot.message_handler(commands=['solve'])
def handle_solve(message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        user = message.from_user.first_name
        ocr_text = message.text.replace('/solve', '').strip()
        print(ocr_text)
        #checking whether the user is authorized or not
        device_id_value = device_id()
        work_session_id_value=upload_problem_text(ocr_text,device_id_value)
        generate_step=generate_steps(work_session_id_value,device_id_value)
        if generate_step is not None:
            max_step_number = 20
            all_answers = []
            for step_number in range(0, max_step_number + 1):
                print(f"Step:{step_number}")
                url = f"https://api.szl.ai/steps/reveal_answer?work_session_id={work_session_id_value}&step_number={step_number}&device_id={device_id_value}"

                payload = {}
                headers = {
                    'authority': 'api.szl.ai',
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
                    'dnt': '1',
                    'origin': 'https://web.szl.ai',
                    'referer': 'https://web.szl.ai/',
                    'rid': 'anti-csrf',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Linux"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'st-auth-mode': 'header',
                    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }

                response = requests.request("GET", url, headers=headers, data=payload)
                try:
                    if response.status_code == 200:
                        response_json = response.json()
                        if response_json == {"detail": f"Step number {step_number} not found"}:
                            break
                        else:
                            if 'answer' in response_json:
                                answertext = response_json['answer']['answer']
                                all_answers.append(answertext)
                                combined_answers = '<br>'.join(all_answers)
                                answer = '<p>' +str(combined_answers) + '</p>'
                            else:
                                print('No More Step')
                                break
                except ValueError as e:
                    print(f"Error decoding JSON: {e}")
            send_documnet_file(message,ocr_text,answer)               
        else:
            print(f"answer getting error")
            bot.send_message(message.chat.id, "answer getting error", parse_mode='HTML')
    except Exception as e:
        print(f"Error: {e}")
        logging.exception(f"Error on :{user_id} {e}")

if __name__ == "__main__":
  try:
    print("\033[92mBot is online!")
    bot.send_message(-1001636291714, f"Bot is online!") 
    bot.polling(none_stop=True)
  except Exception as e:
    print(f"Error: {e}")
    logging.error(f"Error: {e}")    
