import googleapiclient.discovery as gd
import psycopg2
import pandas as pd
import streamlit as st
import plotly.express as px


def Connect_Api():
    api_key = "AIzaSyBo3rriDNVeGfUjt_lhMXJMql3EosS8KDE"
    api_service_name = "youtube"
    api_version = "v3"

    youtube = gd.build(
    api_service_name, api_version, developerKey=api_key)

    return youtube

youtube = Connect_Api()

#Channel_information
def Channel_info(channel_id):
    Channel_details = []
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=channel_id
        )
    response = request.execute()
    for item in response['items']:
        data = dict(
            Channel_Name = item['snippet']['title'],
            Channel_id = item['id'],
            Channel_SubCount = item['statistics']['subscriberCount'],
            Channel_ViewCount = item['statistics']['viewCount'],
            Total_Videos=item["statistics"]["videoCount"],
            Channel_Desc = item['snippet']['description'],
            Channel_Playlist = item['contentDetails']['relatedPlaylists']['uploads']
            )
        Channel_details.append(data)
    return Channel_details

#Get_all_video_id's from the channel
def Get_videoId(channel_id):
    video_ids = []
    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
        ).execute()
    playlist_id=request['items'][0]['contentDetails']['relatedPlaylists']['uploads']  #'UUuI5XcJYynHa5k_lqDzAgwQ'
    next_page_token = None
    while True:
        request1 = youtube.playlistItems().list(
            part="snippet",
            playlistId= playlist_id,
            maxResults=50,
            pageToken=next_page_token).execute()
        for i in range(len(request1['items'])):
            video_ids.append(request1['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = request1.get('nextPageToken') 
        if next_page_token is None:
            break
    return video_ids

#Get_Video_Information
def Get_VideoDetails(GetVideoId):
    video_details = []
    for videoId in GetVideoId: 
        request = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id= videoId
        )
        response = request.execute()    
        for item in response['items']:
            data = dict(Channel_Name = item['snippet']['channelTitle'],
                        Video_ID = item['id'],
                        Video_Name = item['snippet']['title'],
                        Video_Description = item['snippet'].get('description'),
                        Tag = item['snippet'].get('tags'),
                        Published_date = item['snippet']['publishedAt'],
                        View_Count = item['statistics']['viewCount'],
                        Like_Count = item['statistics'].get('likeCount'),
                        Favorite_Count = item['statistics']['favoriteCount'],
                        Comment_Count = item['statistics'].get('commentCount'),
                        Vid_Duration = item['contentDetails']['duration'],
                        Thumbnail = item['snippet']['thumbnails']['default']['url'],
                        Caption_Status = item['contentDetails']['caption']
                        )
            video_details.append(data)
    return video_details
                    
#Get_Comment_details
def Comment_details(Video_ids):
    Comment_data = []
    for videoid in Video_ids:
        try:
            request = youtube.commentThreads().list(
                part = 'snippet',
                videoId = videoid,
                maxResults = 100)
            response = request.execute()
            if len(response['items'])>0:
                for item in response['items']:
                    data = dict(
                        Comment_Id = item.get('id'),
                        Video_Id=item['snippet']['topLevelComment']['snippet']['videoId'],          
                        Comment_Text = item['snippet']['topLevelComment']['snippet']['textDisplay'],
                        Comment_Author = item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                        Comment_PublishAt = item['snippet']['topLevelComment']['snippet']['publishedAt'])

                    Comment_data.append(data)
        except:
            pass
    return Comment_data


#Table creation for Channel, Video_details and Comment details
def Channels_table():
    mydb = psycopg2.connect(host = "localhost",
                            user = "postgres",
                            password = "Groot",
                            database = "youtube_db",
                            port = "5432")
    cursor = mydb.cursor()

    #drop query
    drop_query = ' ' ' drop table if exists channels' ' ' 
    cursor.execute(drop_query)
    mydb.commit()

    try:
        table_qurey = ''' CREATE TABLE IF NOT EXISTS Channels(
                            Channel_Name VARCHAR(255),
                            Channel_id VARCHAR(100) PRIMARY KEY,
                            Channel_SubCount INT,
                            Channel_ViewCount BIGINT,
                            Total_Videos INT,
                            Channel_Desc TEXT,
                            Channel_Playlist VARCHAR(100))'''
        
        cursor.execute(table_qurey)
        mydb.commit()
    except:
        print("Channel already exists")   


def Videos_table():
    mydb = psycopg2.connect(host = "localhost",
                            user = "postgres",
                            password = "Groot",
                            database = "youtube_db",
                            port = "5432")
    cursor = mydb.cursor()

    #drop query
    drop_query = '''drop table if exists videos'''
    cursor.execute(drop_query)
    mydb.commit()

    try:
        table_qurey = ''' CREATE TABLE IF NOT EXISTS Videos(
                            Channel_Name VARCHAR(100),
                            Video_ID VARCHAR(100) PRIMARY KEY,
                            Video_Name VARCHAR(255),
                            Video_Description TEXT,
                            Tag TEXT,
                            Published_date TIMESTAMP,
                            View_Count BIGINT,
                            Like_Count BIGINT,
                            Favorite_Count INT,
                            Comment_Count INT,
                            Vid_Duration INTERVAL,
                            Thumbnail VARCHAR(255),
                            Caption_Status VARCHAR(100))'''
            
        cursor.execute(table_qurey)
        mydb.commit()
    except:
        print("Videos already exists")


def Comments_table():
    mydb = psycopg2.connect(host = "localhost",
                            user = "postgres",
                            password = "Groot",
                            database = "youtube_db",
                            port = "5432")
    cursor = mydb.cursor()

    #drop query
    drop_query = '''drop table if exists comments''' 
    cursor.execute(drop_query)
    mydb.commit()

    try:
        table_qurey = ''' CREATE TABLE IF NOT EXISTS Comments(
                                                        Comment_id VARCHAR(255) PRIMARY KEY,
                                                        Video_id VARCHAR(100),
                                                        Comment_text TEXT,
                                                        Comment_Author VARCHAR(150),
                                                        Comment_PublishDate TIMESTAMP
                                                        )'''
        
        cursor.execute(table_qurey)
        mydb.commit()
    except:
        print("Comments already exists")
    

def tables():
    Channels_table()
    Videos_table()
    Comments_table()
    
    return "Tables haouve been created successfully!"

#Insert query for all tables
def insert_ch_table(channelIds):
    mydb = psycopg2.connect(host = "localhost",
                            user = "postgres",
                            password = "Groot",
                            database = "youtube_db",
                            port = "5432")
    cursor = mydb.cursor()

    Ch_info = Channel_info(channelIds)
        
    #Converting into DataFrame
    Channel_df = pd.DataFrame(Ch_info)  

    #Inser query
    for index, row in Channel_df.iterrows():
        insert_query = ''' INSERT INTO channels(Channel_name,
                                                Channel_id,
                                                Channel_subcount,
                                                Channel_viewcount,
                                                Total_Videos,
                                                Channel_desc,
                                                Channel_playlist)

                                                VALUES(%s,%s,%s,%s,%s,%s,%s) '''
        values = (row['Channel_Name'],
                row['Channel_id'],
                row['Channel_SubCount'],
                row['Channel_ViewCount'],
                row['Total_Videos'],
                row['Channel_Desc'],
                row['Channel_Playlist'])
        
        try:
            cursor.execute(insert_query, values)
            mydb.commit()
            
        except:
            print("Data's already inserted!") 

def insert_vid_table(channelIds):
    mydb = psycopg2.connect(host = "localhost",
                            user = "postgres",
                            password = "Groot",
                            database = "youtube_db",
                            port = "5432")
    cursor = mydb.cursor()    

    VideoIds_of_10_channels = []
    for i in channelIds:
        Video_ids = Get_videoId(i)
        VideoIds_of_10_channels.append(Video_ids)

    Single_listOf_VideoIds = []
    for i in VideoIds_of_10_channels:
        for j in i:
            ob = j
            Single_listOf_VideoIds.append(ob)    

    Video_info = Get_VideoDetails(Single_listOf_VideoIds)
    vid_df = pd.DataFrame(Video_info)

    for index, row in vid_df.iterrows():
        insert_query = ''' INSERT INTO Videos(Channel_Name,
                                                Video_ID,
                                                Video_Name,
                                                Video_Description,
                                                Tag,
                                                Published_date,
                                                View_Count,
                                                Like_Count,
                                                Favorite_Count,
                                                Comment_Count,
                                                Vid_Duration,
                                                Thumbnail,
                                                Caption_Status)

                                                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '''
        values = (row['Channel_Name'],
                    row['Video_ID'],
                    row['Video_Name'],
                    row['Video_Description'],
                    row['Tag'],
                    row['Published_date'],
                    row['View_Count'],
                    row['Like_Count'],
                    row['Favorite_Count'],
                    row['Comment_Count'],
                    row['Vid_Duration'],
                    row['Thumbnail'],
                    row['Caption_Status'])
        
        try:
            cursor.execute(insert_query, values)
            mydb.commit()
            
        except:
            print("Data's already inserted!")

def insert_com_table(chennelIds):
    mydb = psycopg2.connect(host = "localhost",
                            user = "postgres",
                            password = "Groot",
                            database = "youtube_db",
                            port = "5432")
    cursor = mydb.cursor()

    VideoIds_of_10_channels = []
    for i in chennelIds:
        Video_ids = Get_videoId(i)
        VideoIds_of_10_channels.append(Video_ids)

    Single_listOf_VideoIds = []
    for i in VideoIds_of_10_channels:
        for j in i:
            ob = j
            Single_listOf_VideoIds.append(ob)

    Comment_info = Comment_details(Single_listOf_VideoIds) 
    Comment_df = pd.DataFrame(Comment_info)

    for index, row in Comment_df.iterrows():
        insert_query = '''INSERT INTO Comments(Comment_id,
                                                Video_id,
                                                Comment_text,
                                                Comment_Author,
                                                Comment_PublishDate)
                        VALUES (%s, %s, %s, %s, %s)'''
        values = (row['Comment_Id'],
                    row['Video_Id'],
                    row['Comment_Text'],
                    row['Comment_Author'],
                    row['Comment_PublishAt'])
        
        try:
            cursor.execute(insert_query, values)         
            mydb.commit()
            
        except Exception as e:
            print("Data's already inserted!")  

#Adding channel details to the existing table
def ins_tables(ls):
    if isinstance(ls, str):
        ls = [ls]  # Convert single string input to list
    insert_ch_table(ls)
    insert_vid_table(ls)
    insert_com_table(ls)    

    return "New channel details added successfully"


#Dataframe details getting from PostgreSQL
def DF_Channel_table():
    mydb = psycopg2.connect(host = "localhost",
                                    user = "postgres",
                                    password = "Groot",
                                    database = "youtube_db",
                                    port = "5432")
    cursor = mydb.cursor()

    cursor.execute("SELECT * FROM channels")
    ch_tab = cursor.fetchall()
    #to retrive column names from the tables
    column_name = [des[0] for des in cursor.description]
    df = pd.DataFrame(ch_tab, columns = column_name)

    st.dataframe(df)

def DF_Video_table():
    mydb = psycopg2.connect(host = "localhost",
                                        user = "postgres",
                                        password = "Groot",
                                        database = "youtube_db",
                                        port = "5432")
    cursor = mydb.cursor()

    cursor.execute("SELECT * FROM videos")
    Vid_tab = cursor.fetchall()
    column_name = [des[0] for des in cursor.description]
    df = pd.DataFrame(Vid_tab, columns = column_name)

    st.dataframe(df)

def DF_Comment_table():
    mydb = psycopg2.connect(host = "localhost",
                                        user = "postgres",
                                        password = "Groot",
                                        database = "youtube_db",
                                        port = "5432")
    cursor = mydb.cursor()
    
    cursor.execute("SELECT * FROM comments")
    Com_tab = cursor.fetchall()
    column_name = [des[0] for des in cursor.description]
    df = pd.DataFrame(Com_tab, columns=column_name)

    st.dataframe(df)

#Streamlit
with st.sidebar:
    st.title(":red[YOUTUBE DATA HAVERSTING AND WAREHOUSING]")
    st.header(":blue[Objective]")
    st.markdown("This project demonstrates how to harvest data from YouTube and store it in a PostgreSQL database. It uses the YouTube Data API to collect information about channels, videos, and comments. The data is then stored in a PostgreSQL database for analysis and retrieval.")
    st.header(":blue[Skills Takeaway]")
    st.markdown("- Python Scripting\n- Data Collection\n- Streamlit\n- API Intergration\n- Sql ")

st.title(":green[Data Harvesting Zone]")
st.write("Data is gathered from YouTube using the Channel ID and stored in an SQL database for warehousing and further analysis.")
channel_id = st.text_input("Enter the Channel ID")

if st.button("Collect and Store the data into SQL"):
    mydb = psycopg2.connect(host = "localhost",
                                user = "postgres",
                                password = "Groot",
                                database = "youtube_db",
                                port = "5432")
    cursor = mydb.cursor()

    ch_lis = []
    cursor.execute("SELECT channel_id FROM Channels")
    ch_table = cursor.fetchall()
    for c in ch_table:
        ch_lis.append(c[0])

    mydb.commit()

    if channel_id in ch_lis:
        st.success("Channel details of the given id is already exists")
    else:
        insert = ins_tables(channel_id)
        st.success(insert)

st.title(":green[Data Warehousing Zone]")
st.write("The collected data is stored for further analysis.")
#radio button function
show_table_df = st.radio("SQL Tables", ("CHANNELS", "VIDEOS", "COMMENTS"))

if show_table_df == "CHANNELS":
    DF_Channel_table()
elif show_table_df == "VIDEOS" :
    DF_Video_table()
elif show_table_df == "COMMENTS":
    DF_Comment_table()

#SQL Connection and setting questions
mydb = psycopg2.connect(host = "localhost",
                            user = "postgres",
                            password = "Groot",
                            database = "youtube_db",
                            port = "5432")
cursor = mydb.cursor()

st.title(":blue[Queries & Results]")
question = st.selectbox("Select your queries", ("1. What are the names of all the videos and their corresponding channels?",
                                                "2. Which channels have the most number of videos, and how many videos do they have?",
                                                "3. What are the top 10 most viewed videos and their respective channels?",
                                                "4. How many comments were made on each video, and what are their corresponding video names?",
                                                "5. Which videos have the highest number of likes, and what are their corresponding channel names?",
                                                "6. What is the total number of likes for each video, and what are their corresponding video names?",
                                                "7. What is the total number of views for each channel, and what are their corresponding channel names?",
                                                "8. What are the names of all the channels that have published videos in the year 2022?",
                                                "9. What is the average duration of all videos in each channel, and what are their corresponding channel names?",
                                                "10. Which videos have the highest number of comments, and what are their corresponding channel names?"))

if question == "1. What are the names of all the videos and their corresponding channels?":
    query_01 = '''SELECT video_name, channel_name FROM videos'''
    cursor.execute(query_01)
    mydb.commit()
    t1 = cursor.fetchall()
    df1 = pd.DataFrame(t1, columns = ["Videos Title", "Channel Name"])
    st.write(df1)

elif question == "2. Which channels have the most number of videos, and how many videos do they have?":
    query_02 = '''SELECT channel_name, total_videos FROM channels ORDER BY total_videos DESC'''
    cursor.execute(query_02)
    mydb.commit()
    t2 = cursor.fetchall()
    df2 = pd.DataFrame(t2, columns = ["Channel Name", "Total Videos"])
    st.write(df2)

    fiz = px.bar(df2, x = "Channel Name", y = "Total Videos",title = "Channels with the Highest number of Videos")
    #Update layout
    fiz.update_layout(
        xaxis_title="Channel",
        yaxis_title="Number of Videos")
    #display the chart using Streamlit
    st.write("Graphical demonstration")
    st.plotly_chart(fiz)

elif question == "3. What are the top 10 most viewed videos and their respective channels?":
    query_03 = '''SELECT video_name, channel_name, view_count FROM videos WHERE view_count IS NOT NULL ORDER BY view_count DESC LIMIT 10'''
    cursor.execute(query_03)
    mydb.commit()
    t3 = cursor.fetchall()
    df3 = pd.DataFrame(t3, columns = ["Video Title", "Channel Name", "View Count"])
    st.write(df3)

    fiz = px.bar(df3, x = "Channel Name", y = "View Count", title = "Top 10 Videos with the Highest Views by Channel")
    fiz.update_layout(
        xaxis_title="Channel Name",
        yaxis_title="View Count")
    st.write("Graphical demonstration")
    st.plotly_chart(fiz)

elif question == "4. How many comments were made on each video, and what are their corresponding video names?":
    query_04 = '''SELECT comment_count, video_name FROM videos WHERE comment_count IS NOT NULL'''
    cursor.execute(query_04)
    mydb.commit()
    t4 = cursor.fetchall()
    df4 = pd.DataFrame(t4, columns = ["Comment Count", "Video Title"])
    st.write(df4)

    fiz = px.bar(df4, x = "Video Title", y = "Comment Count", title = "Number of Comments on each Video")
    fiz.update_layout(
        xaxis_title="Video Title",
        yaxis_title="Comment Count")
    st.write("Graphical demonstration")
    st.plotly_chart(fiz)

elif question == "5. Which videos have the highest number of likes, and what are their corresponding channel names?":
    query_05 = '''SELECT video_name, channel_name, like_count FROM videos WHERE like_count IS NOT NULL ORDER BY like_count DESC'''
    cursor.execute(query_05)
    mydb.commit()
    t5 = cursor.fetchall()
    df5 = pd.DataFrame(t5, columns = ["Video Title", "Channel Name", "Like Count"])
    st.write(df5)

    fiz = px.bar(df5, x = "Video Title", y = "Like Count",color = "Channel Name", title = "Videos with the Highest Likes by Channel")
    fiz.update_layout(
        xaxis_title="Video Title",
        yaxis_title="Like Count", legend_title = "Channel Name")
    st.write("Graphical demonstration")
    st.plotly_chart(fiz)

elif question == "6. What is the total number of likes for each video, and what are their corresponding video names?":
    query_06 = '''SELECT like_count, video_name FROM videos WHERE like_count IS NOT NULL'''
    cursor.execute(query_06)
    mydb.commit()
    t6 = cursor.fetchall()
    df6 = pd.DataFrame(t6, columns=["Like Count", "Video Title"])
    st.write(df6)

    fiz = px.bar(df6, x = "Video Title", y = "Like Count", title = "Total Number of Likes for Each Video")
    fiz.update_layout(
        xaxis_title="Video Title",
        yaxis_title="Like Count")
    st.write("Graphical demonstration")
    st.plotly_chart(fiz)


elif question == "7. What is the total number of views for each channel, and what are their corresponding channel names?":
    query_07 = '''SELECT channel_viewcount, channel_name FROM channels WHERE channel_viewcount IS NOT NULL'''
    cursor.execute(query_07)
    mydb.commit()
    t7 = cursor.fetchall()
    df7 = pd.DataFrame(t7, columns = ["View Count", "Channel Name"])
    st.write(df7)

    fiz = px.bar(df7, x = "Channel Name", y = "View Count", title = "Total Number of Views for Each Channel")
    fiz.update_layout(
        xaxis_title="Channel Name",
        yaxis_title="Total Number of Views")
    st.write("Graphical demonstration") 
    st.plotly_chart(fiz)

elif question == "8. What are the names of all the channels that have published videos in the year 2022?":
    query_08 = '''SELECT channel_name, video_name, published_date FROM videos WHERE EXTRACT(YEAR FROM published_date)=2022'''
    cursor.execute(query_08)
    mydb.commit()
    t8 = cursor.fetchall()
    df8 = pd.DataFrame(t8, columns = ["Channel Name","Video Title", "Published Date"])
    st.write(df8)

    fiz = px.histogram(df8, x = "Channel Name", title = "Channels with Published Videos in 2022")
    fiz.update_layout(
        xaxis_title="Channel Name",
        yaxis_title="Frequency")
    st.write("Graphical demonstration")
    st.plotly_chart(fiz)

elif question == "9. What is the average duration of all videos in each channel, and what are their corresponding channel names?":
    query_09 = '''SELECT channel_name, AVG(vid_duration) AS avgDuration FROM videos GROUP BY channel_name'''
    cursor.execute(query_09)
    mydb.commit()
    t9 = cursor.fetchall()
    df9 = pd.DataFrame(t9, columns = ["Channel Name", "Avg Duration"])

    #converting the Avg duration time format to string
    N9 = []
    for index, row in df9.iterrows():
        chn_name = row["Channel Name"]
        avg_dur = row["Avg Duration"]
        avg_dur_str = str(avg_dur)
        N9.append(dict(Channel_Name=chn_name,Avg_Duration=avg_dur_str))
    dfN9 = pd.DataFrame(N9)
    st.write(dfN9)

    fiz = px.bar(dfN9, x = "Channel_Name", y = "Avg_Duration", title = "Average Duration of Videos by Channel")
    fiz.update_layout(
        xaxis_title = "Channel Name",
        yaxis_title = "Average Duration")
    st.write("Graphical demonstration")
    st.plotly_chart(fiz)

elif question == "10. Which videos have the highest number of comments, and what are their corresponding channel names?":
    query_10 = '''SELECT channel_name, video_name, comment_count FROM videos WHERE comment_count IS NOT NULL ORDER BY comment_count DESC'''
    cursor.execute(query_10)
    mydb.commit()
    t10 = cursor.fetchall()
    df10 = pd.DataFrame(t10, columns = ["Channel Name", "Video Title", "Comment Count"])    
    st.write(df10)

    fiz = px.bar(df10, x = "Video Title", y = "Comment Count", color = "Channel Name", title = "Videos with the Highest Number of Comments by Channel")
    fiz.update_layout(
        xaxis_title = "Video Title",
        yaxis_title = "Comment Count")
    st.write("Graphical demonstration")
    st.plotly_chart(fiz)