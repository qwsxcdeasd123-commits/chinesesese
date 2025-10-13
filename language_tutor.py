import streamlit as st

st.title("테스트")
st.write("작동합니다!")

name = st.text_input("이름을 입력하세요")
if name:
    st.write(f"안녕하세요, {name}님!")
