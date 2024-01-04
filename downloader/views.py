from django.shortcuts import render,redirect
from django.conf import settings
import requests
from pytube import *
import os
from isodate import parse_duration
from moviepy.video.io.VideoFileClip import VideoFileClip


def home(request):
    videos =[]
    flag = 0
    allItem = []
    print(request)
    search_url ='https://www.googleapis.com/youtube/v3/search'
    video_url = 'https://www.googleapis.com/youtube/v3/videos'
    if request.method =='POST':
        try:
            print('X')
            searchParameter = {
                'part' : 'snippet',
                'q' :request.POST['topic'],
                'key' : settings.YOUTUBE_API_KEY,
                'maxResults' : request.POST['maxResults'],
                'type' : request.POST['type'],
                'regionCode' : request.POST['regionCode'],
                'relevanceLanguage' : request.POST['relevanceLanguage']

            }
            idList = []
            req = requests.get(search_url, params =searchParameter)
            print('Y')
            items = req.json()['items']
            print(items)
            for item in items:
                idList.append(item['id']['videoId'])
            print('Y')
            print(idList)
            #Search end , now times to videos
            videoParameter = {
                'part' : 'snippet, contentDetails',
                'key' : settings.YOUTUBE_API_KEY,
                'id' :','.join(idList),
                'maxResults':6
            }
            req = requests.get(video_url, params = videoParameter)
            print('Z')
            print('one')
            items = req.json()['items'] # ['contentDetails']
            for item in items:
                title = item['snippet']['title']
                if len(title) > 65:
                    title = title[:65] + '....'
                watchUrl = f'https://www.youtube.com/watch?v={item["id"]}'
                try:
                    obj = YouTube(watchUrl)
                    allItem = obj.streams.filter(file_extension='mp4')
                except:
                    pass 
                itag = []
                vformat = []
                for Item in allItem:
                    try:
                        if Item.resolution and int(Item.resolution[:-1]) not in vformat:
                            itag.append(Item.itag)
                            vformat.append(int(Item.resolution[:-1]))
                    except:
                        print(e)
                        pass
                vformat.sort(reverse=True) 
                myList = zip(itag, vformat)
                video = {
                    'title' : title,
                    'id' : item['id'],
                    'url': f'https://www.youtube.com/watch?v={item["id"]}',
                    'duration' : int(parse_duration(item['contentDetails']['duration']).total_seconds() // 60),
                    'thumbnail' : item['snippet']['thumbnails']['high']['url'],
                    'mylist': myList

                }
                videos.append(video)
        except Exception as e :
             flag = 1
             print(e)
    context = {'videos':videos,'flag':flag}
    return render(request,'downloader/home.html',context)


def download(request,id):
    if request.method == 'POST':
        choice = request.POST['choice']
        watchUrl  = f'https://www.youtube.com/watch?v={id}'
        obj = YouTube(watchUrl).streams.get_by_itag(choice).download('C:/Users/lovebhatia/Videos/Captures')
    return redirect('home')

def playlist(request):
    return render(request, 'downloader/playlist.html', context={})

def playlistDownload(request):
    url = request.POST['searchField']
    playListr = Playlist(url)
    for video in playListr:
        video.streams.get_highest_resolution().download('')
    return redirect('playlist')

def trimClip(fileName):
    clip = VideoFileClip('C:/Users/lovebhatia/Videos/Captures' + fileName);
    trimmed_clip = clip.subclip(20,40)
    

    