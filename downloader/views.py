from django.shortcuts import render,redirect
from django.conf import settings
import requests
from pytube import *
import os
from isodate import parse_duration
from moviepy.editor import VideoFileClip, clips_array, concatenate_videoclips, vfx, CompositeVideoClip
from moviepy.editor import VideoFileClip
import numpy as np
import cv2
from vidgear.gears import WriteGear
import subprocess

extension = ".mp4"
thumbnail_name = "thumbnail.png"
downloadPath = "C:/Users/lovebhatia/Videos/Captures/"
output_thumbnail_path = "C:/Users/lovebhatia/Videos/Captures/thumbnail.png"
search_url ='https://www.googleapis.com/youtube/v3/search'
video_url = 'https://www.googleapis.com/youtube/v3/videos'

def home(request):
    videos =[]
    flag = 0
    allItem = []
    if request.method =='POST':
        try:
            searchParameter = {
                'part' : 'snippet',
                'q' :request.POST['topic'],
                'key' : settings.YOUTUBE_API_KEY,
                'maxResults' : request.POST['maxResults'],
                'type' : request.POST['type'],
                'regionCode' : request.POST['regionCode'],
                'relevanceLanguage' : request.POST['relevanceLanguage'],
                'videoDefinition' : 'high',
                'videoDuration' : 'medium',
                #'videoLicense' : 'creativeCommon',
                'order' : 'relevance'
            } 
             
            idList = []
            req = requests.get(search_url, params =searchParameter)
            items = req.json()['items']
            for item in items:
                idList.append(item['id']['videoId'])
            #Search end , now times to videos
            videoParameter = {
                'part' : 'snippet, contentDetails',
                'key' : settings.YOUTUBE_API_KEY,
                'id' :','.join(idList),
                'maxResults':6
            }
            req = requests.get(video_url, params = videoParameter)
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


def download_video(request):
    
    if request.method == 'POST':
        video_url = request.POST['video_url']
        sct = request.POST['sct']
        ect = request.POST['ect']
        print('video_url --> ' +video_url)
        obj = YouTube(video_url)
        video_stream = obj.streams.get_highest_resolution()
        video_name = obj.title[0:4].replace(" ","_")
        download_path_with_title = downloadPath+video_name
        folderPath = downloadPath+video_name +"_fold/"

        video_stream.download(folderPath)

        os.rename(os.path.join(folderPath, video_stream.default_filename),
              os.path.join(folderPath,video_name + extension))
        
        downloadedPath = folderPath + video_name + extension
        folder_video_path = folderPath + video_name
        print('video downloaded complete')
        createShortVideo(downloadedPath,folder_video_path, sct, ect)

        
    return render(request, 'downloader/home.html')

def textToSpeech():
    from gtts import gTTS

    text = "This is an example sentence to be converted to speech."
    tts = gTTS(text=text, lang='en', tld='com.au')
    tts.save('output_audio.mp3')


def tts(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        tts = gTTS(text=text, lang='en')
        tts.save('static/output_audio.mp3')  # Save the generated audio
        return render(request, 'tts.html', {'audio': True})
    return render(request, 'tts.html')



def download(request,id):
    print('In Video Downloading')    
    if request.method == 'POST':
        choice = request.POST['choice']
        sct = request.POST['sct']
        ect = request.POST['ect']
        watchUrl  = f'https://www.youtube.com/watch?v={id}'
        obj = YouTube(watchUrl)
        video_stream = obj.streams.get_highest_resolution()
        video_name = obj.title[0:4].replace(" ","_")

        download_path_with_title = downloadPath+video_name

        folderPath = downloadPath+video_name +"_fold/"

        video_stream.download(folderPath)

        os.rename(os.path.join(folderPath, video_stream.default_filename),
              os.path.join(folderPath,video_name + extension))
        
        downloadedPath = folderPath + video_name + extension
        folder_video_path = folderPath + video_name
        print('video downloaded complete')
        createShortVideo(downloadedPath,folder_video_path, sct, ect)
        

    return redirect('home')



def createShortVideo(downloadedVideoPath, folder_path, sct, ect) :
    print('Short Video Creation started')
    trim_output_path = folder_path + "_trim"+ extension
    print("trim output path --> ", trim_output_path)
    video = VideoFileClip(downloadedVideoPath)
    shorts_video = video.subclip(sct,ect)  
    # Replace this with your desired output path
    shorts_video.write_videofile(trim_output_path , codec='libx264', fps=30)
    print('Short Video Creation completed')

    moviePyConvertToShortsFormat(trim_output_path,folder_path)
    #convert_to_shorts_vid_gear(trim_output_path, folder_path, 60)
    openCVConvertToShortsFormat(trim_output_path,folder_path)
    #convert_to_shorts('C:/Users/lovebhatia/Videos/Captures/Ramp_fold/Ramp_trimp.mp4', 'C:/Users/lovebhatia/Videos/Captures/Ramp_fold/Ramp_trimp_ff.mp4')
    resize_and_focus_left(trim_output_path,folder_path)

    
def moviePyConvertToShortsFormat(trim_output_path, folder_path):

    print('creation you tube short started')
    ytShortsOutputPath = folder_path + '_yt_shorts' + ".mp4"
    video = VideoFileClip(trim_output_path)
    

    target_width = 1080
    target_height = 1920

    # Calculate the aspect ratio of the original video
    video_aspect_ratio = video.w / video.h

    # Calculate the new width and height to fit within the Shorts format
    new_width = target_width
    new_height = int(new_width / video_aspect_ratio)

    # Resize the video while maintaining the aspect ratio
    video_resized = video.resize(width=new_width, height=new_height)

    # Calculate the black background dimensions
    background = np.zeros((target_height, target_width, 3), dtype=np.uint8)

    # Calculate the position to center the video within the black background
    x_pos = (target_width - video_resized.w) // 2
    y_pos = (target_height - video_resized.h) // 2

    # Overlay the resized video onto the black background
    final_video_shorts = VideoFileClip(trim_output_path).resize(width=target_width, height=target_height).on_color(size=(target_width, target_height), color=(0, 0, 0)).set_pos((x_pos, y_pos))
    # Save the resized video
    final_video_shorts.write_videofile(ytShortsOutputPath, codec='libx264', fps=30)  # Adjust parameters as needed
    print('short video creation completed')
    create_thumbnail(trim_output_path,folder_path,0)



def resize_and_focus_left(trim_output_path, folder_path):
    video = VideoFileClip(trim_output_path)
    ytShortsOutputPath = folder_path + '_yt_resize_shorts' + ".mp4"

    # Calculate the 9:16 resolution from the original video's width
    target_width = int(video.w * 9 / 16)
    target_height = video.h
    
    # Resize the video to 9:16 aspect ratio
    resized_video = video.resize(width=target_width, height=target_height)
    
    # Focus on the left side by positioning the video
    left_focused = resized_video.crop(x1=0, y1=0, x2=video.w, y2=video.h)
    
    # Generate a black screen with the same size to fill the right side
    right_blank = left_focused.fx(vfx.painting, width=video.w, height=video.h)
    
    # Combine the left-focused video and the black screen
    final_video = CompositeVideoClip([left_focused, right_blank.set_position(('right', 0))])
    
    # Write the final video to a file
    final_video.write_videofile(ytShortsOutputPath, codec="libx264", fps=24)


def create_thumbnail(video_path, folderPath, at_time=0):
    clip = VideoFileClip(video_path)
    frame = clip.get_frame(at_time)  # Get frame at a specific time (default: start of the video)
    clip.save_frame(folderPath+thumbnail_name, t=at_time)  # Save the frame as a thumbnail




def convert_to_shorts(input_video, output_video):
    ffmpeg_path = "C:/Users/lovebhatia/Downloads/ffmpeg-6.1.1/ffmpeg-6.1.1"
    try:
        # FFmpeg command to convert video to YouTube Shorts format (720x1280 resolution, 60 seconds duration, H.264 video codec, AAC audio codec)
        ffmpeg_cmd = [
            ffmpeg_path,
            "-i", input_video,
            "-vf", "scale=720:1280",
            "-t", "60",  # Limit to 60 seconds (adjust as needed)
            "-c:v", "libx264",
            "-c:a", "aac",
            "-strict", "experimental",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_video
        ]
        subprocess.run([ffmpeg_path, "-i", "input.mp4", "output.mp4"])
        #subprocess.run(ffmpeg_cmd, capture_output=True, check=True)

        print("Conversion completed successfully!")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e.stderr.decode()}")






def convert_to_shorts_vid_gear(input_video, output_folder, duration):
    try:
        # Open video file
        stream = cv2.VideoCapture(input_video)

        # Initialize variables
        frames_per_second = stream.get(cv2.CAP_PROP_FPS)
        total_frames = int(stream.get(cv2.CAP_PROP_FRAME_COUNT))
        segment_duration = int(frames_per_second * duration)
        segment_number = 1

        # Read and write video segments
        while True:
            frames = []
            for _ in range(segment_duration):
                (grabbed, frame) = stream.read()
                if not grabbed:
                    break
                frames.append(frame)

            if len(frames) == 0:
                break

            output_path = f"{output_folder}/segment_{segment_number}.mp4"
            writer = WriteGear(output_path, logging=True)
            for frame in frames:
                writer.write(frame)
            writer.close()
            segment_number += 1

        # Release video stream
        stream.release()
        cv2.destroyAllWindows()
        print("Conversion completed successfully!")

    except Exception as e:
        print(f"Error occurred: {str(e)}")





















def playlist(request):
    return render(request, 'downloader/playlist.html', context={})

def playlistDownload(request):
    url = request.POST['searchField']
    playListr = Playlist(url)
    for video in playListr:
        video.streams.get_highest_resolution().download('')
    return redirect('playlist')

def openCVConvertToShortsFormat(ip,op):
    print('inOpenCV')
    input_path = ip
    output_path = 'C:/Users/lovebhatia/Videos/Captures/openCvShortanub.mp4'

    clip = VideoFileClip(input_path)
    audio = clip.audio
    audio.write_audiofile("extracted_audio.mp3")

    # Target dimensions for YouTube Shorts
    target_width = 1080
    target_height = 1920

    # Open the video file
    video_capture = cv2.VideoCapture(input_path)

    # Get video properties
    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(video_capture.get(cv2.CAP_PROP_FPS))

    # Calculate aspect ratio
    aspect_ratio = width / height

    # Calculate new dimensions to fit the target aspect ratio
    new_width = target_width
    new_height = int(new_width / aspect_ratio)

    # If the new height exceeds the target height, adjust the width to fit within the target height
    if new_height > target_height:
        new_height = target_height
        new_width = int(new_height * aspect_ratio)

    # Create a black background to fit the target size
    background = np.zeros((target_height, target_width, 3), dtype=np.uint8)

    # Calculate the position to center the video within the black background
    x_pos = (target_width - new_width) // 2
    y_pos = (target_height - new_height) // 2

    # Create VideoWriter object
    video_writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (target_width, target_height))

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
        
        # Resize frame while maintaining aspect ratio
        resized_frame = cv2.resize(frame, (new_width, new_height))
        
        # Place the resized frame onto the black background
        background[y_pos:y_pos+new_height, x_pos:x_pos+new_width] = resized_frame

        
        
        # Write the frame with black background to the output video
        video_writer.write(background)

    # Release video objects
    video_capture.release()
    video_writer.release()
    #clip = VideoFileClip(output_path)
    #final_clip = concatenate_videoclips([clip, audio])
    #final_clip.write_videofile(output_path)








