import streamlit as st
import numpy as np
import SessionState
from streamlit.ScriptRunner import RerunException
from streamlit.ScriptRequestQueue import RerunData

state = SessionState.get(question_number=0, num_correct=0)

@st.cache
def get_question(question_number):
    arr = np.random.randint(0, 100, 2)
    q = f"{arr[0]} * {arr[1]}"
    ans = arr[0]*arr[1]
    choices = ["Please select an answer", ans, ans-1, ans+1, ans+2]
    return arr, q, ans, choices

arr, q, ans, choices = get_question(state.question_number)
answered = False
st.write(f"Your score is {state.num_correct}/{state.question_number}")
st.write("")
st.text(f"Solve: {q}")
a = st.selectbox('Answer:', choices)

if a != "Please select an answer":
    st.write(f"You chose {a}")
    if (ans == a):
        answered = True
        st.write(f"Correct!")
    else:
        st.write(f"Wrong!, the correct answer is {ans}")
        
            
if st.button('Next question'):
    state.question_number += 1
    if (answered):
        state.num_correct += 1
    raise RerunException(RerunData(widget_state=None))
    
    
if st.button('Reset'):
    state.question_number = 0
    state.num_correct = 0
    raise RerunException(RerunData(widget_state=None))
