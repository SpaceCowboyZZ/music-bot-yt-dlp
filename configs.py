import re
import asyncio
from pytube import Playlist
import yt_dlp



# def search(url):
#     yt_opts ={
#         'default_search': 'ytsearch',
#         'noplaylist': True, 
#     }

#     with yt_dlp.YoutubeDL(yt_opts) as ydl:
#         info_dict = ydl.extract_info(url, download=False)
#         if 'entries' in info_dict and 'id' in info_dict['entries'][0]:
#             yt_id = info_dict['entries'][0]['id']
#             return yt_id
#         elif 'id' in info_dict:
#             yt_id = info_dict['id']
#             return yt_id