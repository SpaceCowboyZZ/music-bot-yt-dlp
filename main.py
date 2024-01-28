import discord
import yt_dlp
from discord.ext import commands
import asyncio
import logging
import sys
from concurrent.futures import ThreadPoolExecutor


logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

queue = []

actual_url = []

thumb_url = []

embed_msg = None

thumb = None

bot.play_status = False

bot.in_chat = None

executor = ThreadPoolExecutor(max_workers=5)


async def embeded(ctx, msg, thumbna):
    embed= discord.Embed(
        colour=discord.Colour.brand_green(),
        title='tocando agora:',
        description=f'{msg}'
            )      
    embed.set_author(name='Tocador') 
                
    embed.set_image(url=thumbna)
    
    await ctx.send(embed=embed)


async def search_video(ctx, urlq):  
    yt_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'default_search': 'auto',
                'noplaylist': True,
                'verbose': True
    }

    yt_search = yt_dlp.YoutubeDL(yt_opts)
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, lambda: yt_search.extract_info(url=urlq, download=False))
    if 'entries' in data:
        data = data['entries'][0]       
        data1 = [data['title'], data['url']]
        data2 = data['webpage_url']
        data3 = data['thumbnail']
    else:
        data1 = [data['title'], data['url']]
        data2 = [data['webpage_url']]
        data3 = [data['thumbnail']]
    return data1, data2, data3


async def playlist(ctx, urlq):
    pl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'default_search': 'auto',     
            'noplaylist': False,
            'ignoreerrors': True,
            'flat_playlist': True,
            'verbose': True
}
    playlist_search = yt_dlp.YoutubeDL(pl_opts)
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, lambda: playlist_search.extract_info(url=urlq, download=False))
    if 'entries' in data:
        data1 =[[entry['title'], entry['url']] for entry in data['entries']]
        data2 = [entry['webpage_url'] for entry in data['entries']]
        data3 = [entry['thumbnail'] for entry in data['entries']]
    return data1, data2, data3



@bot.listen()
async def on_voice_state_update(member, before, after):
    if not member.id == bot.user.id:
        return

    elif before.channel is None:
        voice = after.channel.guild.voice_client
        time = 0
        while True:
            await asyncio.sleep(1)
            time = time + 1
            if voice.is_playing() and not voice.is_paused():
                time = 0
            if time == 600:
                await voice.disconnect()
            if not voice.is_connected():
                break



@bot.command()
async def join(ctx):
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if not voice_client:
            if ctx.author.voice:
                voice_channel = ctx.author.voice.channel
                voice_client = await voice_channel.connect()
                bot.in_chat = voice_channel      

@bot.command(name='play')
@commands.cooldown(1, 2, commands.BucketType.user)
async def play(ctx, *, search_query):
    global queue, actual_url, thumb_url
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice_client:
        await join(ctx)
    elif ctx.author.voice.channel != bot.in_chat:
        await ctx.send("não estamos no mesmo voice chat seu baiano.")
        return
    elif not voice_client:
        await ctx.send('tu não ta no voice chat nengue.')
        return
    
    if '/playlist?' in search_query and not '/watch?' in search_query:
        await ctx.send('pegando informações da playlist, pode demorar um pouco, se vc usar "!play" novamente, a musica pode entrar na fila antes da playlist...')
        data1, url, tn = await playlist(ctx, search_query)
        
        data = data1.copy()
        actual_url.extend(url)
        thumb_url.extend(tn)
    
        if bot.play_status or len(queue) > 0:
            queue.extend(data)
            await ctx.send(f'adicionado a fila')      
        else:
            queue.extend(data)
            await play_now(ctx, url=queue.pop(0))     
                                       
    elif '/watch?' in search_query and not '/playlist?' in search_query:
        data1, url, tn = await search_video(ctx, search_query)
        
        data = data1.copy()
        actual_url.append(url)
        thumb_url.append(tn)
        
        if bot.play_status or len(queue) > 0:
            queue.append(data)
            await ctx.send(f'adicionado a fila')

        else:
            queue.append(data)
            await play_now(ctx, url=queue.pop(0))
    else:
        data1, url, tn = await search_video(ctx, search_query)
        
        data = data1.copy()
        actual_url.append(url)
        thumb_url.append(tn)

        if bot.play_status or len(queue) > 0:
            queue.append(data)
            await ctx.send(f'adicionado a fila')
        else:
            queue.append(data)
            await play_now(ctx, url=queue.pop(0))
        
        
        
async def play_now(ctx, url):
    global embed_msg, thumb
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        
    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    bot.play_status = True    
    print(bot.play_status)
    def after(error):
        if error:
            print(error)
                
        if bot.play_status and len(queue) > 0:
            next_song = queue.pop(0)
            embed_msg = f'{next_song[0]}  {actual_url.pop(0)}'
            thumb = f'{thumb_url.pop(0)}'
            asyncio.run_coroutine_threadsafe(embeded(ctx, embed_msg, thumb), bot.loop)
            voice_client.play(discord.FFmpegPCMAudio(next_song[1], **ffmpeg_options), after=lambda e: after(e))
        else:
            bot.play_status = False
            print(bot.play_status)
            
    embed_msg = f'{url[0]}  {actual_url.pop(0)}'
    thumb = f'{thumb_url.pop(0)}'
    await embeded(ctx, embed_msg, thumb)          
    voice_client.play(discord.FFmpegPCMAudio(url[1], **ffmpeg_options), after=lambda e: after(e))
        
 
        
@bot.command(name='next') #works
async def next(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.stop()

    else:
        embed = discord.Embed(title="END", description="No song is currently playing", color=0x6b30d9)
        embed.set_author(name="Prismo")
        await ctx.send(embed=embed)              
                

@bot.command(name='pause') #done
async def pause(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        
    if voice_client.is_playing():
        voice_client.pause()
        await ctx.send('audio pausado')
        return
    else:
        await ctx.send('nenhum audio tocando no momento')
        return

      
        
@bot.command(name='continue') #done
async def Continue(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        
    if voice_client.is_paused():
        voice_client.resume()
        await ctx.send('resumindo audio')
        return
    else:
        await ctx.send('nenhum audio pausado no momento')

        
            
@bot.command(name='stop')
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if bot.play_status or voice_client.is_paused():
        queue.clear()
        voice_client.stop()
        await ctx.send('todas as musicas foram removidas da fila')
    else:
        await ctx.send('não estou tocando nada')

    # Run the bot with your token
bot.run('MTE5Njg5NzgzMzAzMTMwMzMzOA.GKQTh_.f_l0vYlLYEvfe-sErC4L-9IhYdjubxlipusuzY')