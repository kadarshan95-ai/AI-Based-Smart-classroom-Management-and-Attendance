import streamlit as st

st.set_page_config(
    page_title="AI Smart Classroom",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 AI-Based Smart Classroom Management")
st.subheader("Attendance Management System")

st.write("Welcome to the Smart Classroom Management System")

st.success("Streamlit app is running successfully!")

st.sidebar.title("Menu")

option = st.sidebar.selectbox(
    "Select Page",
    ["Home", "Students", "Attendance", "Courses", "Reports"]
)

if option == "Home":
    st.header("Dashboard")
    st.write("Welcome to the Smart Classroom Dashboard.")

elif option == "Students":
    st.header("Student Management")

elif option == "Attendance":
    st.header("Attendance Management")

elif option == "Courses":
    st.header("Course Management")

elif option == "Reports":
    st.header("Attendance Reports")