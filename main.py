import discord
import yt_dlp
from datetime import datetime
from discord.ext import commands
# import urllib.request
import pytube
import os
import re
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)


queue = []


#mandar para configs.py depois
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
pl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'default_search': 'auto',
            'noplaylist': False,
            'flat_playlist': True,
            'verbose': True
}





playlist_search = yt_dlp.YoutubeDL(pl_opts)

yt_search = yt_dlp.YoutubeDL(yt_opts)

bot.play_status = False

queue = []       
        
@bot.command()
async def join(ctx):
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if not voice_client:
            if ctx.author.voice:
                voice_channel = ctx.author.voice.channel
                voice_client = await voice_channel.connect()
            else:
                await ctx.send('tu não ta no voice chat nengue.')
                return
        

@bot.command(name='play')
async def play(ctx, *, search_query):
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if not voice_client:
            await join(ctx)
          
          
          
          
        #need to fix this     
        if '/playlist?' in search_query:
            data = playlist_search.extract_info(url=search_query, download=False)
            if 'entries' in data:
                data1 =[[entry['title'], entry['url']] for entry in data['entries']]
     
            data = data1.copy()
                   
            if data:
                print(data)
                
            if bot.play_status or len(queue) > 0:
                queue.append(data)
                await ctx.send('adicionado a fila')
                
            else:
                queue.extend(data)
                play_song = queue[0]
                await play_now(ctx, url=play_song[1])
                queue.pop(0)
                    
            if data:
                    print(data)
                    
        elif '/watch?' in search_query and not '/playlist?' in search_query:
            data = yt_search.extract_info(url=search_query, download=False)  
            if 'entries' in data:
                data = data['entries'][0]
                
            data = [data['title'], data['url']]
            if data:
                print(data)
                
            if bot.play_status or len(queue) > 0:
                queue.append(data)
                await ctx.send('adicionado a fila')
            else:
                queue.append(data)
                play_song = queue[0]
                await play_now(ctx, url=play_song[1])
                await ctx.send(f'now playing: {play_song[0]}, queue is: {queue}')
                queue.pop(0)

        else:
            data = yt_search.extract_info(f'ytsearch:{search_query}', download=False) 
            if 'entries' in data:
                data = data['entries'][0]
                
            data = [data['title'], data['url']]

            if bot.play_status or len(queue) > 0:
                queue.append(data)
                await ctx.send('adicionado a fila')
            else:
                queue.append(data)
                play_song = queue.pop(0)
                await play_now(ctx, url=play_song[1])
                

            
               
async def play_now(ctx, url):
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        bot.is_playing = True
        
        ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        def after(error):
            if error:
                print(error)
        
            if len(queue) > 0 and not voice_client.is_playing():
                next_song = queue[0]
                voice_client.play(discord.FFmpegPCMAudio(next_song[1], **ffmpeg_options), after=lambda e: after(e))    
                queue.pop(0)
            else:
                bot.is_playing = False
                
            
        voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_options), after=lambda e: after(e))
        
        
        
async def play_next(ctx):
    if len(queue) > 0:
        play_song = queue.pop(0)
        await play_now(ctx, url=play_song[1])
        
        
        await ctx.send(embed=discord.Embed(
            title="Now Playing",
            description=f"**{play_song[0]}**",
            color=0x6b30d9
        ).set_author(name="Tocador"))
    
    else:
        bot.is_playing = False

                



# @bot.command(name='pause') #done
# async def pause(ctx):
#         global paused_at, filename
        
#         voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        
#         if voice_client.is_playing():
#             voice_client.pause()
#             paused_at = datetime.now()
#             await ctx.send('audio pausado')
#             return
#         else:
#             await ctx.send('nenhum audio tocando no momento')
#             return

      
        
# @bot.command(name='continue') #done
# async def Continue(ctx):
#         global paused_at, filename, play_task, should_stop
        
#         voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        
#         if (voice_client.is_paused() and (datetime.now() - paused_at).total_seconds() < 600):
#                 voice_client.resume()
#                 paused_at = datetime.now()
#                 should_stop = True
#                 await ctx.send('resumindo audio')
#                 return
                
#         if (paused_at is not None and (datetime.now() - paused_at).total_seconds() > 600):
#             voice_client.stop()
#             await asyncio.sleep(0.5)
#             if filename is not None:
#                 try:
#                     os.remove(filename)
#                     await ctx.send('nenhum audio pausado no momento') 
#                     return
#                 except FileNotFoundError:
#                     pass
#                 except PermissionError as e:
#                     await ctx.send(f'error: unable to delete file>    {e}  ')
        
#         if play_task is not None and not play_task.done():
#             await ctx.send('audio já está tocando')

#         else:
#             await ctx.send('nenhum audio pausado no momento')

        
        
        
# @bot.command(name='next') #works
# async def next(ctx):

            
#             voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)


            
            
            
# @bot.command(name='stop')
# async def stop(ctx):
#     voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)



    # Run the bot with your token
bot.run('MTE5Njg5NzgzMzAzMTMwMzMzOA.GKQTh_.f_l0vYlLYEvfe-sErC4L-9IhYdjubxlipusuzY')