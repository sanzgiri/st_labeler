import streamlit as st
import numpy as np
import SessionState
from streamlit.ScriptRunner import RerunException
from streamlit.ScriptRequestQueue import RerunData
from streamlit import ReportSession
from smart_open import smart_open
import boto3
import re
import time

s3 = boto3.resource('s3')
bucket = s3.Bucket('ashu-tb-1')
bucket_path = 's3://ashu-tb-1/'
labelfile = "vid_emo_labels.csv"


@st.cache
def get_video_list():
    vlist = []
    for o in bucket.objects.all():
        oid = int(re.search(r'vid_(\d+)\.mp4', o.key).group(1))
        vlist.append(oid)
    return vlist

@st.cache
def get_random_video(vlist, vnum):
    num_vids = len(vlist)
    vrnd = vlist[np.random.randint(0, num_vids, 1)[0]]
    choices = [f'Please select label for video id #{vrnd} :', 'Anger', 'Disgust', 'Fear', 'Joy', 'Neutral', 'Surprise', 'Sadness']
    return vrnd, choices    
    
    
def run_labeler():
    
    state = SessionState.get(vnum=0)
    vlist = get_video_list()
    
    st.title("Emotion Labeler")
    st.write(f"Total Videos Labeled: {state.vnum}")
    st.write("")
    st.write("Please label the primary emotion in the video below:")
    
    vrnd, choices = get_random_video(vlist, state.vnum)
    vpath = f'{bucket_path}vid_{vrnd}.mp4'
    with smart_open(vpath, 'rb') as video_file:
        video_bytes = video_file.read()
    st.video(video_bytes)
    
    emo = st.selectbox('Emotion:', choices)
    
    if st.button('Next video'):
        with open(labelfile,'a') as fd:
            fd.write(f"{time.time()}, {SessionState.get_session_id()}, {vrnd}, {emo}\n")
        state.vnum += 1
        raise RerunException(RerunData(widget_state=None))




# main block run by code
if __name__ == '__main__':
    run_labeler()