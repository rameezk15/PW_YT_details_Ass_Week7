#run cmnd "pip install -r requirments.txt" before run app.py file
#Required libraries
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS,cross_origin
from googleapiclient.discovery import build
from bs4 import BeautifulSoup as bs
import requests
import pymongo
import logging

#Create a logging file
logging.basicConfig(filename="application.log", level=logging.INFO)

#Setup API key, Channel ID
api_key = "Paste_API_Key_Here"

#Create api service
youtube = build('youtube','v3', developerKey= api_key)

#setup a flask
app = Flask(__name__)


#All functions
#Function to extract Channel_ID With BeautifulSoup
def channel_id(input_link):
    response = requests.get(input_link)
    html = bs(response.text, 'html.parser')
    channel_link = html.find_all('meta', {'property':"og:url"})[0]['content']
    channel_ID = channel_link.split('/')[-1]
    return channel_ID

#Function to extract playlist_ID With Youtube API
def get_playlist_ID(youtube, channel_ID):
    request = youtube.channels().list(
        part="contentDetails,statistics",
        id= channel_ID)
    response = request.execute()
    playlist_id = response['items'][0]["contentDetails"]["relatedPlaylists"]['uploads']
    return playlist_id

# Function for extract video_ID of first 5 videos With Youtube API
def get_video_ids(youtube, playlist_id):
    request = youtube.playlistItems().list(
        part = 'contentDetails',
        playlistId = playlist_id)
    response = request.execute()
    video_ids = []
    for video in response['items']:
        video_id = video['contentDetails']['videoId']
        video_ids.append(video_id)
    return video_ids

#Function for extract videos details With Youtube API
def get_video_details(youtube, video_ids):
    request = youtube.videos().list(
        part = 'snippet,contentDetails,statistics',
        id = ",".join(video_ids))            
    response = request.execute()
    video_details =[]
    for video in response['items']:
        data = dict(Title = video["snippet"]["title"],
                Video_Link = "https://www.youtube.com/watch?v=" + video["id"], 
                Video_Thumbnails = video["snippet"]["thumbnails"]["standard"]["url"],
                Views= video["statistics"]["viewCount"],
                Posting_date= video["snippet"]["publishedAt"].split("T")[0])
        video_details.append(data)
    return video_details

#Function to Upload data on mogoDB
def uplod_mongo(data):
    client= pymongo.MongoClient("Paste_Mongo_DB_Link_Here")
    db = client['Youtube_Channel_Details']
    collection = db['Channel_Videos_Details']
    collection.insert_many(data)

#Create a the homepage
@app.route('/', methods = ['GET'])
@cross_origin()
def home_page():
    return render_template('index.html')

#extract details and show on result.html page
@app.route('/details', methods = ['GET','POST'])
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            #Get link input from user
            input_link = request.form['content']
            
            #Extract Channel ID
            channel_ID = channel_id(input_link)

            try:
                #Extract Playlist ID
                playlist_id = get_playlist_ID(youtube, channel_ID)
            except Exception as e:
                logging.info(e)
                print("Please Check Your api_key")
           
            #Extract Video ID
            video_ids = get_video_ids(youtube, playlist_id)
              
            #Get Video details
            video_details = get_video_details(youtube, video_ids)
            
            try:
                #Uplod on MongoDB
                uplod_mongo(video_details)
            except Exception as e:
                logging.info(e)
                return print('''Please check your mongoDB client Link in "uplod_mongo" function
                             If you still geting and error just comment out "uplod_mongo(video_details)"
                             with try and except code''')
            
            #Showing Result on Web Page
            return render_template('result.html', details = video_details) 
        
        except Exception as e:
            logging.info(e)
            return "Somthing Went Wrong. Only Work With Youtube Channel Link"
    
    else:
        return render_template('index.html')
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port="5004")