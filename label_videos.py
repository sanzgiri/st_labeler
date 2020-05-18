import streamlit as st
import numpy as np
import SessionState
from streamlit.ScriptRunner import RerunException
from streamlit.ScriptRequestQueue import RerunData
from streamlit import ReportSession
from smart_open import open
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
    choices = [f'Select emotion for video id #{vrnd} :', 'Anger', 'Disgust', 'Fear', 'Joy', 'Neutral', 'Surprise', 'Sadness']
    return vrnd, choices
    
    
def run_labeler():
    
    state = SessionState.get(vnum=0)
    vlist = get_video_list()
    
    st.title("Emotion Labeler")
    st.write("Please label as many videos as you can. When done, simply close browser tab.")
    st.write("")
    st.write(f"Total videos labeled in current session:{state.vnum}")
    st.write("Note: refreshing browser tab will reset counts.")

    vrnd, choices = get_random_video(vlist, state.vnum)
    vpath = f'{bucket_path}vid_{vrnd}.mp4'
    with open(vpath, 'rb') as video_file:
        vbytes = video_file.read()
    st.video(vbytes)
    
    emo = st.selectbox('Emotion:', choices)
    
    if st.button('Get next video'):
        with open(labelfile,'a') as fd:
            fd.write(f"{time.time()}, {SessionState.get_session_id()}, {vrnd}, {emo}\n")
        state.vnum += 1
        raise RerunException(RerunData(widget_state=None))




# main block run by code
if __name__ == '__main__':
    run_labeler()