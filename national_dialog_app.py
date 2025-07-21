import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from collections import Counter
import re

# --- THEME & STYLE ---
st.set_page_config(page_title="National Dialog SA", layout="wide", initial_sidebar_state="expanded")

# Dark theme CSS
DARK_CSS = """
<style>
body, .stApp {
    background-color: #18181b !important;
    color: #fff !important;
}
.stTextInput, .stTextArea, .stSelectbox, .stMultiSelect, .stFileUploader, .stButton, .stForm, .stMarkdown, .stDataFrame, .stSidebar, .stTabs, .stCard {
    background-color: #23272f !important;
    color: #fff !important;
}
.stButton>button {
    background-color: #1e293b !important;
    color: #fff !important;
}
.stButton>button:hover {
    background-color: #334155 !important;
}
::-webkit-input-placeholder { color: #fff !important; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# --- DATA STORAGE ---
DATA_DIR = "user_data_store"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
JSON_PATH = os.path.join(DATA_DIR, "users.json")
CSV_PATH = os.path.join(DATA_DIR, "users.csv")

# --- SIDEBAR LINKS ---
st.sidebar.title("Tourist Attractions")
st.sidebar.markdown('[Facebook](https://www.facebook.com/TshwaneTourismAssociation)')
st.sidebar.markdown('[X](https://twitter.com/Tshwane_Tourism)')
st.sidebar.markdown('[Youtube](https://www.youtube.com/channel/UCXeVsem77xzvepVaYJKZtlw)')

def is_valid_sa_phone(phone):
    # Accepts 0[6-8]XXXXXXXX or +27[6-8]XXXXXXXX
    return bool(re.fullmatch(r"(0[6-8][0-9]{8}|\+27[6-8][0-9]{8})", phone))

def is_valid_email(email):
    # Simple email regex
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))

# --- AUTHENTICATION ---
def authenticate():
    st.title("Welcome to National Dialog SA")
    st.markdown("#### Please enter your details to proceed:")
    with st.form("auth_form"):
        name = st.text_input("Name", key="auth_name")
        phone = st.text_input("Phone Number", key="auth_phone")
        email = st.text_input("Email", key="auth_email")
        submit = st.form_submit_button("Enter")
    if submit:
        errors = []
        if not name:
            errors.append("Name is required.")
        if not phone or not is_valid_sa_phone(phone):
            errors.append("Enter a valid South African cell phone number (e.g., 0821234567 or +27821234567).")
        if not email or not is_valid_email(email):
            errors.append("Enter a valid email address.")
        if errors:
            for err in errors:
                st.error(err)
        else:
            st.session_state["user"] = {"name": name, "phone": phone, "email": email}
            # Save to JSON/CSV
            user_row = {"name": name, "phone": phone, "email": email, "timestamp": datetime.now().isoformat()}
            # JSON
            if os.path.exists(JSON_PATH):
                with open(JSON_PATH, "r") as f:
                    users = json.load(f)
            else:
                users = []
            users.append(user_row)
            with open(JSON_PATH, "w") as f:
                json.dump(users, f, indent=2)
            # CSV
            df = pd.DataFrame(users)
            df.to_csv(CSV_PATH, index=False)
            st.success("Access granted!")
            st.rerun()
    st.stop()

if "user" not in st.session_state:
    authenticate()

# --- BLOG DATA ---
BLOG_PATH = os.path.join(DATA_DIR, "blog.json")
if os.path.exists(BLOG_PATH):
    with open(BLOG_PATH, "r") as f:
        blog_data = json.load(f)
else:
    blog_data = []

# --- QUESTIONS (from web search and scope) ---
FORM_QUESTIONS = [
    {
        "title": "Retail Experience",
        "questions": [
            ("Which retail stores do you visit most often?", "text"),
            ("How satisfied are you with the cleanliness and security of these stores?", "select", ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"]),
            ("What do you value most: price, quality, or convenience?", "select", ["Price", "Quality", "Convenience"]),
            ("Any suggestions for improvement?", "text")
        ]
    },
    {
        "title": "Public Services",
        "questions": [
            ("Which public services do you use most (e.g., transport, clinics, libraries)?", "text"),
            ("How would you rate their quality?", "select", ["Excellent", "Good", "Average", "Poor", "Very Poor"]),
            ("What is the biggest challenge you face with public services?", "text"),
            ("What improvement would you like to see?", "text")
        ]
    },
    {
        "title": "Shopping Preferences",
        "questions": [
            ("Do you prefer shopping online or in-store? Why?", "text"),
            ("What factors influence your choice of shopping location?", "text"),
            ("Which brands or stores do you trust most?", "text"),
            ("How important are sales and promotions to you?", "select", ["Very Important", "Somewhat Important", "Not Important"])
        ]
    },
    {
        "title": "Favorite Places & Experiences",
        "questions": [
            ("What is your favorite place in South Africa?", "text"),
            ("Why do you like it?", "text"),
            ("Upload an image of this place (optional)", "file"),
            ("Leave a comment about your experience", "text")
        ]
    }
]

# --- POLL DATA ---
POLL_PATH = os.path.join(DATA_DIR, "polls.json")
if os.path.exists(POLL_PATH):
    with open(POLL_PATH, "r") as f:
        poll_data = json.load(f)
else:
    poll_data = []

# --- MAIN UI ---
st.title("National Dialog: South Africa")
st.caption("A national platform to understand public preferences, retail habits, and service experiences across South Africa.")

# --- AD SPACE ---
st.markdown("---")
st.subheader("Ad Space")
ad_tabs = st.tabs([f"Ad {i+1}" for i in range(5)])
for i, tab in enumerate(ad_tabs):
    with tab:
        st.info(f"[Ad Space {i+1}] - Interactive card coming soon!")

st.markdown("---")

# --- FORMS (Cyclable Cards) ---
form_tab = st.tabs([f"Form {i+1}: {f['title']}" for i, f in enumerate(FORM_QUESTIONS)])
for idx, (tab, form) in enumerate(zip(form_tab, FORM_QUESTIONS)):
    with tab:
        with st.form(f"form_{idx}"):
            responses = {}
            for q_idx, (q, qtype, *opts) in enumerate(form["questions"]):
                if qtype == "text":
                    responses[q] = st.text_input(q, key=f"q_{idx}_{q_idx}")
                elif qtype == "select":
                    responses[q] = st.selectbox(q, opts[0], key=f"q_{idx}_{q_idx}")
                elif qtype == "file":
                    responses[q] = st.file_uploader(q, type=["jpg", "png"], key=f"q_{idx}_{q_idx}")
            submit = st.form_submit_button("Submit")
        if submit:
            entry = {
                "user": st.session_state["user"],
                "form": form["title"],
                "responses": responses,
                "timestamp": datetime.now().isoformat()
            }
            # Save to blog
            blog_data.append(entry)
            with open(BLOG_PATH, "w") as f:
                json.dump(blog_data, f, indent=2)
            # Poll update (for establishments)
            if idx == 0 and responses.get("Which retail stores do you visit most often?"):
                poll_data.append(responses["Which retail stores do you visit most often?"])
                with open(POLL_PATH, "w") as f:
                    json.dump(poll_data, f, indent=2)
            st.success("Your response has been submitted and will appear in the blog!")
            st.rerun()

# --- BLOG DISPLAY ---
st.markdown("---")
st.subheader("Public Blog: Responses from Across South Africa")
for entry in reversed(blog_data[-20:]):
    user = entry["user"]
    form = entry["form"]
    responses = entry["responses"]
    ts = entry["timestamp"]
    st.markdown(f"**{user['name']}** ({user['email']}, {user['phone']}) at {ts}")
    st.markdown(f"*Form: {form}*")
    for k, v in responses.items():
        if hasattr(v, "name") and hasattr(v, "read"):
            st.image(v, caption=k)
        else:
            st.markdown(f"- **{k}**: {v}")
    st.markdown("---")

# --- POLL DISPLAY ---
st.sidebar.subheader("Popular Retail Establishments (Poll)")
if poll_data:
    poll_counts = Counter(poll_data)
    poll_df = pd.DataFrame(poll_counts.items(), columns=["Establishment", "Mentions"])
    poll_df = poll_df.sort_values("Mentions", ascending=False)
    st.sidebar.dataframe(poll_df, use_container_width=True)
else:
    st.sidebar.info("No poll data yet. Fill in the forms to see popular places!")

# --- FOOTER ---
st.markdown("<center>Developed by Thapelo Kgothatso Thooe | kgothatsothooe@gmail.com | github.com/ybadk</center>", unsafe_allow_html=True) 