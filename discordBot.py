# import torch
# from model import chatBot
import re, io, os, json, argparse, requests
import discord
from discord.ext import commands
from utility import *

# init
with open('./setting/key.bin', 'rb') as f:
    key = f.read().decode('utf-8')
with open('./setting/config.json', 'r') as f:
    config = json.load(f)

# config['device'] = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
# bot = chatBot(config)

bert = commands.Bot(command_prefix='$')

#調用 event 函式庫
@bert.event
async def on_ready():
    print('目前登入身份：', bert.user)
    
#當有訊息時
@bert.event
async def on_message(message):
    #排除自己的訊息，避免陷入無限循環
    if message.author == bert.user:
        return
    if bert.user.mentioned_in(message):
        print(message.content)
        await message.channel.send('tagged')
    await bert.process_commands(message)
    
@bert.command()
async def introduce(ctx):
    await ctx.send(f'<@{ctx.message.author.id}>，tag我，就會回覆用BERT seq2seq產生的回答')

@bert.command()
async def register(ctx):
    result = registerUser(ctx.message.author)
    await ctx.send(f'<@{ctx.message.author.id}>，{result}')

@bert.command()
async def memo(ctx, *, message):
    try:
        ap = argparse.ArgumentParser()
        ap.add_argument("msg", type=str, help='message you want to save')
        ap.add_argument("-d", "--duration", type=int, default=7, help='duration of the saved message')
        args = ap.parse_args(message.split())
    except SystemExit as e:
        help_msg = '輸入你要儲存的訊息(訊息中不要有空格)\n只接受 -d 參數當訊息儲存天數(整數)\nEX: !memo 儲存訊息 -d 30'
        await ctx.send(f'<@{ctx.message.author.id}>\n{help_msg}')
        return
    
    succ, response = addMemo(ctx.message.author.id, args.msg, args.duration)
    await ctx.send(f'<@{ctx.message.author.id}>，{response}')

@bert.command()
async def remind(ctx):
    succ, response = getMemo(ctx.message.author.id)
    status = {'ID': [], 'start time': [], 'response': []}
    if succ and response:
        for MID, content, start_time in response:
            status = appendDict(status, MID, start_time, content)
        await ctx.send(f'<@{ctx.message.author.id}>\n```{tableMsg(status)}```')
    else:
        await ctx.send(f'<@{ctx.message.author.id}>，{response}')
        
@bert.command()
async def done(ctx, *, message):
    try:
        ap = argparse.ArgumentParser()
        ap.add_argument("id", type=int, nargs="+", help='del msg by MID')
        args = ap.parse_args(message.split())
    except SystemExit as e:
        help_msg = '輸入要刪除的儲存資料ID\nEX: !done 1 2 3 5'
        await ctx.send(f'<@{ctx.message.author.id}>\n{help_msg}')
        return
    
    status = {'id': [], 'response': []}
    for MID in args.id:
        succ, response = delMemo(ctx.message.author.id, MID)
        corr = 'delete成功' if succ else f'delete失敗，{response}'
        status = appendDict(status, MID, corr)
    await ctx.send(f'<@{ctx.message.author.id}>\n```{tableMsg(status)}```')

@bert.command()
async def addimg(ctx, *, message):
    if not ctx.message.attachments:
        await ctx.send(f'<@{ctx.message.author.id}>，這個指令要附上圖片')
        return
    status = {'insert': [], 'response': []}
    for attachment in ctx.message.attachments:
        url = attachment.url
        _, file_type = os.path.splitext(url)
        if file_type.lower() in ['.jpg', '.jpeg', '.gif', '.png']:
            img = requests.get(url).content
            succ, response = addImg(message, img, file_type[1:])
            corr = '成功' if succ else f'失敗'
            status = appendDict(status, corr, response)
        else:
            status = appendDict(status, '失敗', f'{url}的附檔名要為jpg jpeg png gif')
    await ctx.send(f'<@{ctx.message.author.id}>\n```{tableMsg(status)}```')

@bert.command()
@commands.is_owner()
async def delimg(ctx, *, message):
    succ, response = delImg(message)
    await ctx.send(f'<@{ctx.message.author.id}>\n```{response}```')

def encodeImg(name):
    img, img_type = getRandomImg(name)
    file = discord.File(io.BytesIO(img),filename=f'image.{img_type}')
    return file

@bert.event
async def on_command_error(ctx, error):
    command = ctx.invoked_with
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f'<@{ctx.message.author.id}>，這個指令需要在後面加上參數喔')
    elif isinstance(error, commands.errors.CommandNotFound):
        name, count = getImgName(command)
        if name:
            file = encodeImg(name)
            await ctx.send(f'從{count}張圖裡面隨機選出這張', file=file)
        else:
            await ctx.send(f'<@{ctx.message.author.id}>，沒有這個指令')
    else:
        await ctx.send(f'<@{ctx.message.author.id}>，怪怪的\n{str(error)}')
        
bert.run(key)