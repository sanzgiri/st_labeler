import pandas as pd
import re
import time
import os

import streamlit as st
import numpy as np
import SessionState

from streamlit.script_runner import ScriptRunner
from streamlit.script_request_queue import ScriptRequestQueue

#from streamlit.script_runner.ScriptRunner import RerunException
#from streamlit.script_runner.ScriptRequestQueue import RerunData

### https://gist.github.com/scotta/1063364
### based on: http://www.catalysoft.com/articles/StrikeAMatch.html
### similar projects: https://pypi.org/project/Fuzzy/
### another good article: https://medium.com/@yash_agarwal2/soundex-and-levenshtein-distance-in-python-8b4b56542e9e

def _get_character_pairs(text):
    """Returns a defaultdict(int) of adjacent character pair counts.
    >>> _get_character_pairs('Test is')
    {'IS': 1, 'TE': 1, 'ES': 1, 'ST': 1}
    >>> _get_character_pairs('Test 123')
    {'23': 1, '12': 1, 'TE': 1, 'ES': 1, 'ST': 1}
    >>> _get_character_pairs('Test TEST')
    {'TE': 2, 'ES': 2, 'ST': 2}
    >>> _get_character_pairs('ai a al a')
    {'AI': 1, 'AL': 1}
    >>> _get_character_pairs('12345')
    {'34': 1, '12': 1, '45': 1, '23': 1}
    >>> _get_character_pairs('A')
    {}
    >>> _get_character_pairs('A B')
    {}
    >>> _get_character_pairs(123)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "strikeamatch.py", line 31, in _get_character_pairs
        if not hasattr(text, "upper"): raise ValueError
    ValueError: Invalid argument
    """

    if not hasattr(text, "upper"):
        raise ValueError("Invalid argument")

    results = dict()

    for word in text.upper().split():
        for pair in [word[i]+word[i+1] for i in range(len(word)-1)]:
            if pair in results:
                results[pair] += 1
            else:
                results[pair] = 1
    return results

def compare_strings(string1, string2):
    """Returns a value between 0.0 and 1.0 indicating the similarity between the
    two strings. A value of 1.0 is a perfect match and 0.0 is no similarity.
    >>> for w in ('Sealed', 'Healthy', 'Heard', 'Herded', 'Help', 'Sold'):
    ...     compare_strings('Healed', w)
    ... 
    0.8
    0.5454545454545454
    0.4444444444444444
    0.4
    0.25
    0.0
    >>> compare_strings("Horse", "Horse box")
    0.8
    >>> compare_strings("Horse BOX", "Horse box")
    1.0
    >>> compare_strings("ABCD", "AB") == compare_strings("AB", "ABCD") 
    True
    
    """
    s1_pairs = _get_character_pairs(string1)
    s2_pairs = _get_character_pairs(string2)

    s1_size = sum(s1_pairs.values())
    s2_size = sum(s2_pairs.values())

    intersection_count = 0

    # determine the smallest dict to optimise the calculation of the
    # intersection.
    if s1_size < s2_size:
        smaller_dict = s1_pairs
        larger_dict = s2_pairs
    else:
        smaller_dict = s2_pairs
        larger_dict = s1_pairs

    # determine the intersection by counting the subtractions we make from both
    # dicts.
    for pair, smaller_pair_count in smaller_dict.items():
        if pair in larger_dict and larger_dict[pair] > 0:
            if smaller_pair_count < larger_dict[pair]:
                intersection_count += smaller_pair_count
            else:
                intersection_count += larger_dict[pair]

    return (2.0 * intersection_count) / (s1_size + s2_size)
    
def sanitize(string):
    string = re.sub(r"/[^\w\s]/i", "", string)
    string = re.sub(r"\([^()]*\)", "", string)
    string = re.sub(r"/^(the|a|an) /i", "", string)
    string = string.strip().lower()
    return string

@st.cache    
def read_jarchive():
    df = pd.read_csv('https://github.com/sanzgiri/jarchive/blob/master/jarchive.csv', sep='\|\|', engine='python', names=['gid', 'airdate', 'rnd', 'category', 'value', 'text', 'answer'])
    df = df[df.text != ' = ']
    df = df[df.answer != ' = ']
    df = df[df.text != ' ? ']
    return df

@st.cache
def get_one_question(question_number, df):
    row = df.sample(n=1)
    category = row['category'].iloc[0]
    value = row['value'].iloc[0]
        
    if (value == ''):
        value = 100
    elif (np.isnan(value)):
        value = 100
    else:
        value = str(value).replace(',','')
        value = int(value)
        
    question = row['text'].iloc[0]
    answer = row['answer'].iloc[0]
    return category, question, answer, value


def main():
    
    df = read_jarchive()
    st.write(df.head())
    state = SessionState.get(question_number=1, num_correct=0, score=0)

    st.title("Streamlit Jeopardy!")
    
    category, question, answer, value = get_one_question(state.question_number, df)
    answered = False
    
    st.write(f"Question from category {category} for ${value}:")
    st.write(f"    {question}")
    response = st.text_input("What is: ", key=str(state.question_number))
        
    if (response != ''):
        sresponse = sanitize(response)
        sanswer = sanitize(answer)
                
        if (compare_strings(sresponse, sanswer) >= 0.5):
            answered = True
            st.write(f"Correct! The reference answer is {answer}.")
        else:
            answered = False
            st.write(f"Sorry! Your response was {response}. The correct answer is {answer}.")
            
        if (answered):
            state.num_correct += 1
            state.score += value
        else:
            state.score -= value
        st.write(f"Your score is {state.num_correct}/{state.question_number} and winnings are ${state.score}")
        st.write("")
        
            
    if st.button('Next question'):
        state.question_number += 1
        raise ScriptRunner.RerunException(ScriptRequestQueue.RerunData(widget_state=None))
        
    
    if st.button('Reset score'):
        state.question_number = 0
        state.num_correct = 0
        state.score = 0
        raise ScriptRunner.RerunException(ScriptRequestQueue.RerunData(widget_state=None))

 

if __name__ == "__main__":
    main()
