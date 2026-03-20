import base64
import json
import mimetypes
import os
import re
import time
from collections import Counter
from datetime import datetime
from html import escape
from urllib.parse import quote
from uuid import uuid4

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# --- APP CONFIG ---
st.set_page_config(page_title="National Dialog SA", layout="wide", initial_sidebar_state="expanded")

# --- DATA STORAGE ---
DATA_DIR = "user_data_store"
MEDIA_DIR = os.path.join(DATA_DIR, "media")
BLOG_MEDIA_DIR = os.path.join(MEDIA_DIR, "blog")
AD_MEDIA_DIR = os.path.join(MEDIA_DIR, "ads")

for directory in [DATA_DIR, MEDIA_DIR, BLOG_MEDIA_DIR, AD_MEDIA_DIR]:
    os.makedirs(directory, exist_ok=True)

JSON_PATH = os.path.join(DATA_DIR, "users.json")
CSV_PATH = os.path.join(DATA_DIR, "users.csv")
BLOG_PATH = os.path.join(DATA_DIR, "blog.json")
POLL_PATH = os.path.join(DATA_DIR, "polls.json")
ADS_PATH = os.path.join(DATA_DIR, "ads.json")

# --- SIDEBAR LINKS ---
TOURIST_LINKS = [
    {"label": "Facebook", "url": "https://www.facebook.com/TshwaneTourismAssociation"},
    {"label": "X", "url": "https://twitter.com/Tshwane_Tourism"},
    {"label": "YouTube", "url": "https://www.youtube.com/channel/UCXeVsem77xzvepVaYJKZtlw"},
]

RETAILER_LINKS = {
    "shoprite": "https://www.shoprite.co.za/",
    "pick n pay": "https://www.pnp.co.za/",
    "woolworths": "https://www.woolworths.co.za/",
    "checkers": "https://www.checkers.co.za/",
    "spar": "https://www.spar.co.za/",
    "truworths": "https://www.truworths.co.za/",
    "jet": "https://www.jetstores.co.za/",
    "mr price": "https://www.mrp.com/",
    "pep": "https://www.pepstores.com/",
    "clicks": "https://www.clicks.co.za/",
    "dis-chem": "https://www.dischem.co.za/",
}

GENDER_OPTIONS = [
    "Prefer not to say",
    "Female",
    "Male",
    "Non-binary",
    "Other",
]

SERVICE_STAR_RATING_LABEL = "Rate the service using stars"
STAR_RATING_OPTIONS = [1, 2, 3, 4, 5]


def normalize_star_rating(value):
    if value is None:
        return 0
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(0, min(5, int(value)))

    text = str(value).strip()
    if not text:
        return 0

    if "★" in text:
        return max(0, min(5, text.count("★")))

    match = re.search(r"([1-5])", text)
    if match:
        return int(match.group(1))

    return 0


def format_star_rating_text(value):
    rating = normalize_star_rating(value)
    if rating <= 0:
        return "☆☆☆☆☆"
    return ("★" * rating) + ("☆" * (5 - rating))


def apply_south_africa_theme():
    st.markdown(
        """
        <style>
        :root {
          --sa-red: #ce1126;
          --sa-blue: #002395;
          --sa-green: #007a4d;
          --sa-gold: #ffb612;
          --sa-black: #111827;
          --sa-flag-gradient: linear-gradient(90deg, #111827 0%, #ce1126 22%, #002395 48%, #007a4d 74%, #ffb612 100%);
        }

        .stApp {
          background:
            radial-gradient(circle at top left, rgba(206, 17, 38, 0.10), transparent 28%),
            radial-gradient(circle at top right, rgba(0, 35, 149, 0.10), transparent 30%),
            radial-gradient(circle at bottom left, rgba(0, 122, 77, 0.10), transparent 32%),
            linear-gradient(180deg, #fffdf7 0%, #f8fafc 48%, #f5fff9 100%);
        }

        [data-testid="stHeader"] {
          background: rgba(255, 255, 255, 0.72);
          backdrop-filter: blur(8px);
        }

        [data-testid="stSidebar"] {
          background:
            linear-gradient(180deg, rgba(17, 24, 39, 0.98) 0%, rgba(0, 35, 149, 0.96) 34%, rgba(0, 122, 77, 0.95) 68%, rgba(206, 17, 38, 0.93) 100%);
        }

        [data-testid="stSidebar"] * {
          color: #f8fafc;
        }

        [data-testid="stSidebar"] .stCaption {
          color: rgba(248, 250, 252, 0.82);
        }

        h1, h2, h3, h4 {
          color: #111827;
          letter-spacing: -0.02em;
        }

        h1 {
          background: linear-gradient(90deg, #111827 0%, #002395 26%, #007a4d 56%, #ffb612 78%, #ce1126 100%);
          -webkit-background-clip: text;
          background-clip: text;
          color: transparent;
        }

        h3 {
          position: relative;
          display: inline-block;
          padding-bottom: 0.2rem;
        }

        h3::after {
          content: "";
          display: block;
          width: 100%;
          height: 4px;
          margin-top: 6px;
          border-radius: 999px;
          background: linear-gradient(90deg, #111827 0%, #ce1126 24%, #002395 50%, #007a4d 76%, #ffb612 100%);
        }

        h4 {
          color: var(--sa-blue);
          font-weight: 800;
        }

        hr {
          border-top: 2px solid rgba(17, 24, 39, 0.08);
          background-image: linear-gradient(90deg, #111827 0%, #ce1126 20%, #002395 45%, #007a4d 70%, #ffb612 100%);
          height: 2px;
          border: none;
        }

        [data-baseweb="tab-list"] {
          gap: 8px;
        }

        [data-baseweb="tab"] {
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.98));
          border: 1px solid rgba(17, 24, 39, 0.08);
          border-radius: 14px 14px 0 0;
          padding: 10px 14px;
          box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
          transition: background 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease, color 0.25s ease;
        }

        [data-baseweb="tab"]:hover {
          background: linear-gradient(90deg, rgba(206, 17, 38, 0.12) 0%, rgba(0, 35, 149, 0.12) 35%, rgba(0, 122, 77, 0.12) 70%, rgba(255, 182, 18, 0.18) 100%);
          color: #111827 !important;
          transform: translateY(-1px);
          box-shadow: 0 12px 20px rgba(15, 23, 42, 0.08);
        }

        [data-baseweb="tab"][aria-selected="true"] {
          background: linear-gradient(90deg, #002395 0%, #007a4d 60%, #ffb612 100%);
          color: #ffffff !important;
          border-color: transparent;
        }

        div[data-testid="stForm"] {
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(255, 248, 235, 0.98));
          border: 1px solid rgba(17, 24, 39, 0.08);
          border-top: 5px solid #ffb612;
          border-radius: 20px;
          padding: 1rem 1rem 0.75rem;
          box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
          transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease, background 0.22s ease;
        }

        div[data-testid="stForm"]:hover,
        div[data-testid="stForm"]:focus-within {
          transform: translateY(-2px);
          border-color: rgba(0, 122, 77, 0.24);
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(255, 248, 235, 0.98), rgba(255, 245, 214, 0.94));
          box-shadow: 0 18px 34px rgba(17, 24, 39, 0.12), 0 12px 24px rgba(0, 35, 149, 0.08), 0 10px 22px rgba(0, 122, 77, 0.08);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.98));
          border: 1px solid rgba(17, 24, 39, 0.08);
          border-top: 4px solid var(--sa-blue);
          border-radius: 18px;
          box-shadow: 0 12px 24px rgba(15, 23, 42, 0.07);
          transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease, border-top-color 0.22s ease;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:hover,
        div[data-testid="stVerticalBlockBorderWrapper"]:focus-within {
          transform: translateY(-2px);
          border-color: rgba(206, 17, 38, 0.18);
          border-top-color: var(--sa-green);
          box-shadow: 0 18px 32px rgba(17, 24, 39, 0.12), 0 10px 22px rgba(206, 17, 38, 0.08), 0 10px 22px rgba(255, 182, 18, 0.10);
        }

        div[data-testid="stTextInput"] > div > div,
        div[data-testid="stNumberInput"] > div > div,
        div[data-testid="stTextArea"] > div > div,
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
        section[data-testid="stFileUploaderDropzone"],
        div[data-testid="stFileUploaderDropzone"] {
          border-radius: 14px !important;
          border: 1px solid rgba(17, 24, 39, 0.12) !important;
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.95)) !important;
          transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease, background 0.22s ease !important;
        }

        div[data-testid="stTextInput"] > div > div:hover,
        div[data-testid="stNumberInput"] > div > div:hover,
        div[data-testid="stTextArea"] > div > div:hover,
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div:hover,
        section[data-testid="stFileUploaderDropzone"]:hover,
        div[data-testid="stFileUploaderDropzone"]:hover {
          transform: translateY(-1px);
          border-color: rgba(206, 17, 38, 0.30) !important;
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(255, 248, 235, 0.96), rgba(255, 245, 214, 0.92)) !important;
          box-shadow: 0 0 0 1px rgba(206, 17, 38, 0.05), 0 0 0 4px rgba(0, 35, 149, 0.06), 0 12px 24px rgba(0, 122, 77, 0.08) !important;
        }

        div[data-testid="stTextInput"] > div > div:focus-within,
        div[data-testid="stNumberInput"] > div > div:focus-within,
        div[data-testid="stTextArea"] > div > div:focus-within,
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
        div[data-testid="stSelectbox"]:focus-within [data-baseweb="select"] > div,
        section[data-testid="stFileUploaderDropzone"]:focus-within,
        div[data-testid="stFileUploaderDropzone"]:focus-within {
          border-color: rgba(0, 122, 77, 0.48) !important;
          background: linear-gradient(180deg, rgba(255, 255, 255, 1), rgba(245, 255, 249, 0.98)) !important;
          box-shadow: 0 0 0 1px rgba(0, 122, 77, 0.08), 0 0 0 4px rgba(255, 182, 18, 0.18), 0 14px 26px rgba(0, 35, 149, 0.10) !important;
        }

        div[data-testid="stSegmentedControl"] {
          margin: 0.2rem 0 0.75rem;
        }

        div[data-testid="stSegmentedControl"] [role="radiogroup"] {
          gap: 0.45rem;
          flex-wrap: wrap;
        }

        div[data-testid="stSegmentedControl"] button {
          border-radius: 999px !important;
          border: 1px solid rgba(17, 24, 39, 0.12) !important;
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(255, 248, 235, 0.94)) !important;
          color: var(--sa-black) !important;
          font-weight: 700 !important;
          transition: transform 0.22s ease, box-shadow 0.22s ease, background 0.22s ease, color 0.22s ease !important;
        }

        div[data-testid="stSegmentedControl"] button:hover {
          transform: translateY(-1px);
          background: linear-gradient(90deg, rgba(206, 17, 38, 0.10), rgba(0, 35, 149, 0.10), rgba(0, 122, 77, 0.10), rgba(255, 182, 18, 0.16)) !important;
          box-shadow: 0 10px 18px rgba(17, 24, 39, 0.10), 0 0 0 1px rgba(0, 35, 149, 0.08) !important;
        }

        div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
          background: var(--sa-flag-gradient) !important;
          color: #ffffff !important;
          border-color: rgba(17, 24, 39, 0.22) !important;
          box-shadow: 0 12px 22px rgba(17, 24, 39, 0.14), 0 0 0 3px rgba(255, 182, 18, 0.18) !important;
        }

        .stButton > button,
        div[data-testid="stForm"] button {
          border: none;
          border-radius: 999px;
          background: linear-gradient(90deg, #ce1126 0%, #002395 38%, #007a4d 74%, #ffb612 100%);
          color: #ffffff;
          font-weight: 700;
          box-shadow: 0 10px 24px rgba(15, 23, 42, 0.16);
          transition: transform 0.22s ease, box-shadow 0.22s ease, background 0.22s ease, filter 0.22s ease;
        }

        .stButton > button:hover,
        div[data-testid="stForm"] button:hover {
          background: var(--sa-flag-gradient);
          box-shadow: 0 16px 30px rgba(17, 24, 39, 0.18), 0 10px 24px rgba(0, 35, 149, 0.12), 0 8px 18px rgba(0, 122, 77, 0.10);
          filter: saturate(1.08);
          transform: translateY(-2px);
        }

        a:hover {
          color: var(--sa-blue);
        }

        [data-testid="stSidebar"] a:hover {
          color: var(--sa-gold);
        }

        div[data-testid="stAlert"],
        div[role="alert"] {
          border-radius: 18px;
          border: 1px solid rgba(17, 24, 39, 0.10);
          border-left: 6px solid var(--sa-blue);
          background: linear-gradient(90deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 250, 252, 0.98) 52%, rgba(245, 255, 249, 0.98) 100%);
          box-shadow: 0 12px 24px rgba(15, 23, 42, 0.07);
          transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
        }

        div[data-testid="stAlert"]:hover,
        div[role="alert"]:hover {
          transform: translateY(-1px);
          border-color: rgba(0, 122, 77, 0.20);
          box-shadow: 0 16px 28px rgba(17, 24, 39, 0.10), 0 8px 20px rgba(0, 35, 149, 0.08);
        }

        div[data-testid="stNotification"],
        div[data-testid="stAlertContainer"] {
          border-radius: 18px;
        }

        .sa-empty-state {
          margin: 0.35rem 0 0.8rem;
          padding: 1rem 1.1rem;
          border-radius: 20px;
          border: 1px solid rgba(17, 24, 39, 0.10);
          border-left: 6px solid var(--sa-red);
          background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.98) 48%, rgba(245, 255, 249, 0.96) 100%);
          box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
        }

        .sa-empty-state__badge {
          display: inline-block;
          margin-bottom: 0.55rem;
          padding: 0.3rem 0.7rem;
          border-radius: 999px;
          background: var(--sa-flag-gradient);
          color: #ffffff;
          font-size: 0.72rem;
          font-weight: 800;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .sa-empty-state__text {
          color: #1f2937;
          font-weight: 600;
          line-height: 1.5;
        }

        .sa-empty-state--sidebar {
          border-color: rgba(255, 255, 255, 0.16);
          border-left-color: var(--sa-gold);
          background: linear-gradient(135deg, rgba(17, 24, 39, 0.94) 0%, rgba(0, 35, 149, 0.92) 42%, rgba(0, 122, 77, 0.90) 100%);
          box-shadow: 0 16px 28px rgba(0, 0, 0, 0.22);
        }

        .sa-empty-state--sidebar .sa-empty-state__text {
          color: #f8fafc;
        }

        .sa-footer {
          margin: 1.4rem auto 0.25rem;
          padding: 1rem 1.2rem;
          max-width: 920px;
          border-radius: 20px;
          border: 1px solid rgba(17, 24, 39, 0.10);
          background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.96) 50%, rgba(255, 248, 235, 0.98) 100%);
          box-shadow: 0 16px 30px rgba(15, 23, 42, 0.08);
          text-align: center;
          color: #1f2937;
          font-size: 0.95rem;
          line-height: 1.7;
        }

        .sa-footer strong {
          color: var(--sa-black);
        }

        .sa-footer a {
          color: var(--sa-blue);
          font-weight: 700;
          text-decoration: none;
        }

        .sa-footer a:hover {
          color: var(--sa-red);
        }

        .stCaption {
          color: #475569;
          font-weight: 500;
        }

        p, label {
          color: #1f2937;
        }

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label {
          color: #f8fafc;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def is_valid_sa_phone(phone):
    # Accepts 0[6-8]XXXXXXXX or +27[6-8]XXXXXXXX
    return bool(re.fullmatch(r"(0[6-8][0-9]{8}|\+27[6-8][0-9]{8})", phone))


def render_empty_state(message, sidebar=False):
    classes = "sa-empty-state sa-empty-state--sidebar" if sidebar else "sa-empty-state"
    st.markdown(
        f"<div class='{classes}'><div class='sa-empty-state__badge'>South Africa</div><div class='sa-empty-state__text'>{escape(message)}</div></div>",
        unsafe_allow_html=True,
    )


def is_valid_email(email):
    # Simple email regex
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


def mask_email(email):
    text = str(email or "").strip()
    if not text or text == "No email provided" or "@" not in text:
        return "Email hidden"

    local_part, domain_part = text.split("@", 1)
    if len(local_part) <= 2:
        masked_local = f"{local_part[:1]}*"
    else:
        masked_local = f"{local_part[:1]}{'*' * (len(local_part) - 2)}{local_part[-1:]}"

    domain_name, dot, domain_suffix = domain_part.partition(".")
    masked_domain = f"{domain_name[:1]}***"
    if dot and domain_suffix:
        masked_domain = f"{masked_domain}.{domain_suffix}"

    return f"{masked_local}@{masked_domain}"


def mask_phone(phone):
    text = str(phone or "").strip().replace(" ", "")
    if not text or text == "No phone provided":
        return "Phone hidden"
    if len(text) <= 5:
        return "*" * len(text)
    return f"{text[:3]}****{text[-3:]}"


def load_json_list(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    return []


def save_json_list(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def save_uploaded_media(uploaded_file, target_dir):
    if uploaded_file is None:
        return None

    _, extension = os.path.splitext(uploaded_file.name)
    filename = f"{uuid4().hex}{extension.lower()}"
    file_path = os.path.join(target_dir, filename)

    with open(file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    media_type = uploaded_file.type or ""
    media_kind = "video" if media_type.startswith("video/") else "image"

    return {
        "path": os.path.relpath(file_path).replace("\\", "/"),
        "name": uploaded_file.name,
        "kind": media_kind,
    }


def serialize_response_value(value):
    if hasattr(value, "getbuffer") and hasattr(value, "name"):
        return save_uploaded_media(value, BLOG_MEDIA_DIR)
    return value


def render_saved_media(media, caption=None):
    if not isinstance(media, dict) or not media.get("path"):
        return

    file_path = os.path.normpath(media["path"])
    if not os.path.exists(file_path):
        st.caption("Uploaded media is unavailable.")
        return

    if media.get("kind") == "video":
        st.video(file_path)
    else:
        st.image(file_path, caption=caption or media.get("name"), use_container_width=True)


def normalize_whatsapp_number(phone):
    text = str(phone or "").strip().replace(" ", "")
    if not text:
        return ""
    if text.startswith("+27"):
        return f"27{text[3:]}"
    if text.startswith("27"):
        return text
    if text.startswith("0"):
        return f"27{text[1:]}"
    return text


def get_ad_action(ad):
    link = str(ad.get("link", "")).strip()
    if link:
        return link, "More info"

    whatsapp = str(ad.get("whatsapp", "")).strip()
    if whatsapp and is_valid_sa_phone(whatsapp):
        phone_number = normalize_whatsapp_number(whatsapp)
        message = quote(
            f"Hello, I saw your ad on National Dialog and I am interested in {ad.get('title', 'your offer')}."
        )
        return f"https://wa.me/{phone_number}?text={message}", "WhatsApp"

    return None, "More info"


def prepare_ads_data(ads):
    prepared_ads = []
    changed = False

    for ad in ads:
        if not isinstance(ad, dict):
            continue

        prepared = dict(ad)
        if not prepared.get("ad_id"):
            prepared["ad_id"] = f"ad-{uuid4().hex[:10]}"
            changed = True

        for field in ["price", "location", "whatsapp", "link"]:
            if field not in prepared:
                prepared[field] = ""
                changed = True

        prepared_ads.append(prepared)

    return prepared_ads, changed


def render_ad_card(ad):
    st.caption("Live Preview (as it will appear in the feed)")
    # We use the same HTML generator for consistency
    ad_html = build_blog_ad_card_html(ad)
    st.components.v1.html(ad_html, height=650, scrolling=True)


def get_media_data_uri(media):
    if not isinstance(media, dict) or not media.get("path"):
        return None, None

    file_path = os.path.normpath(media["path"])
    if not os.path.exists(file_path):
        return None, None

    mime_type = mimetypes.guess_type(file_path)[0]
    if not mime_type:
        mime_type = "video/mp4" if media.get("kind") == "video" else "image/png"

    with open(file_path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode("utf-8")

    return media.get("kind", "image"), f"data:{mime_type};base64,{encoded}"


def build_ad_showcase_html(ads):
    cards = []
    action_icon = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" style="width:10px;height:10px;fill:currentColor;">
      <path d="M73 39c-14.8-9.1-33.4-9.4-48.5-.9S0 62.6 0 80V432c0 17.4 9.4 33.4 24.5 41.9s33.7 8.1 48.5-.9L361 297c14.3-8.7 23-24.2 23-41s-8.7-32.2-23-41L73 39z"></path>
    </svg>
    """

    for idx, ad in enumerate(reversed(ads)):
        theme_index = (idx % 5) + 1
        media_kind, media_uri = get_media_data_uri(ad.get("media"))
        ad_id = escape(str(ad.get("ad_id", "")))
        
        price = ad.get("price") or "Request"
        location = ad.get("location") or "SA"
        title = escape(ad.get("title", "Ad"))
        
        if media_uri and media_kind == "video":
            media_markup = (
                f'<div class="card-image-container">'
                f'<video class="card-media" muted playsinline preload="metadata" src="{media_uri}"></video>'
                f'<div class="media-overlay">▶ Watch</div>'
                f'</div>'
            )
        elif media_uri:
            media_markup = (
                f'<div class="card-image-container">'
                f'<img class="card-media" src="{media_uri}" alt="{title}">'
                f'<div class="media-overlay">👁 View</div>'
                f'</div>'
            )
        else:
            media_markup = '<div class="card-image-container"><div class="fallback-media">ADS</div></div>'

        action_url, action_label = get_ad_action(ad)
        action_text = action_label if action_url else "Go"
        
        cards.append(
            f'''
            <div class="card theme-{theme_index}">
              {media_markup}
              <div class="card-content">
                <p class="card-title">{title}</p>
                <div class="details-container">
                  <div class="detail-row"><span>{price}</span><span>•</span><span>{location}</span></div>
                </div>
                <div class="card-btn-row">
                  <a class="card-btn action-btn" href="{escape(action_url or '#', quote=True)}" target="_blank">
                    {action_icon}
                    <span class="card-btn-text">{escape(action_text)}</span>
                  </a>
                  <a class="card-btn feed-btn" href="#ad-{ad_id}" target="_top" onclick="window.parent.location.hash='ad-{ad_id}'; return true;">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" style="width:10px;height:10px;fill:currentColor;"><path d="M448 32H64C28.65 32 0 60.65 0 96v320c0 35.35 28.65 64 64 64h384c35.35 0 64-28.65 64-64V96c0-35.35-28.65-64-64-64zM256 416H96v-32h160v32zm160-96H96v-32h320v32zm0-96H96v-32h320v32zm0-96H96V96h320v32z"/></svg>
                    <span class="card-btn-text">Feed</span>
                  </a>
                </div>
              </div>
            </div>
            '''
        )

    return f'''
    <html>
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
      </head>
      <body>
        <div class="ad-grid-wrap">{"".join(cards)}</div>
      </body>
      <style>
        body {{ margin: 0; padding: 0; font-family: 'Outfit', sans-serif; background: transparent; }}
        .ad-grid-wrap {{
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
          gap: 12px;
          padding: 8px;
        }}
        .card {{
          display: flex; flex-direction: column; background: #fff; border-radius: 12px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.06); overflow: hidden; transition: transform 0.3s ease;
          padding: 10px; text-decoration: none; border-top: 4px solid var(--accent);
          height: 250px; box-sizing: border-box; position: relative;
        }}
        .card:hover {{ transform: scale(1.03); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }}
        
        .theme-1 {{ --accent: #ce1126; }} .theme-2 {{ --accent: #002395; }} 
        .theme-3 {{ --accent: #007a4d; }} .theme-4 {{ --accent: #ffb612; }} 
        .theme-5 {{ --accent: #111827; }}
        
        .card-image-container {{
          width: 100%; height: 100px; border-radius: 8px; margin-bottom: 8px;
          overflow: hidden; background: #f1f5f9; display: flex; align-items: center; justify-content: center;
          position: relative; border: 1px solid #e2e8f0;
        }}
        .card-media {{ width: 100%; height: 100%; object-fit: cover; }}
        .media-overlay {{
          position: absolute; inset: 0; background: rgba(0,0,0,0.3); display: flex;
          align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s;
          color: white; font-weight: 600; font-size: 10px; pointer-events: none;
        }}
        .card:hover .media-overlay {{ opacity: 1; }}
        
        .card-content {{ display: flex; flex-direction: column; gap: 4px; flex-grow: 1; }}
        .card-title {{
          margin: 0; font-size: 13px; font-weight: 700; color: #1e293b;
          display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;
        }}
        .details-container {{
          background: #f8fafc; padding: 4px 6px; border-radius: 6px; font-size: 10px;
          font-weight: 600; color: #64748b; margin-bottom: 4px;
        }}
        .detail-row {{ display: flex; justify-content: space-between; }}
        
        .card-btn-row {{
          display: flex; gap: 6px; margin-top: auto;
        }}
        
        .card-btn {{
          background: #f1f5f9; color: #64748b; height: 26px; flex: 1;
          border-radius: 6px; display: flex; align-items: center; justify-content: center;
          transition: all 0.3s ease; text-decoration: none; border: 1px solid #e2e8f0;
          gap: 4px; font-size: 10px; font-weight: 700;
        }}
        
        .action-btn {{ background: var(--accent); color: #fff; border: none; }}
        .action-btn:hover {{ background: #1e293b; color: #fff; }}
        .feed-btn:hover {{ background: #e2e8f0; color: #1e293b; }}
        
        .card-btn svg {{ width: 12px; height: 12px; }}
        .card-btn-text {{ white-space: nowrap; }}
      </style>
    </html>
    '''


def build_blog_ad_card_html(ad):
    ad_id = escape(str(ad.get("ad_id", "ad-default")))
    title = escape(str(ad.get("title", "Sponsored Ad")))
    description = escape(str(ad.get("description", "Community promotion")))
    price = escape(str(ad.get("price") or "Price on Request"))
    location = escape(str(ad.get("location") or "South Africa"))
    whatsapp = escape(str(ad.get("whatsapp") or "Contact for info"))
    author = escape(str(ad.get("author") or "Member"))
    timestamp = escape(str(ad.get("timestamp") or "Just now"))
    media_kind, media_uri = get_media_data_uri(ad.get("media"))
    
    action_url, action_label = get_ad_action(ad)
    action_text = action_label if action_url else "Visit Merchant"

    if media_uri and media_kind == "video":
        media_markup = (
            f'<div class="card-media-wrapper">'
            f'<video class="card-media" controls playsinline preload="metadata" src="{media_uri}"></video>'
            f'</div>'
        )
    elif media_uri:
        media_markup = (
            f'<div class="card-media-wrapper">'
            f'<img class="card-media" src="{media_uri}" alt="{title}">'
            f'</div>'
        )
    else:
        media_markup = '<div class="card-media-wrapper"><div class="fallback-media">AD</div></div>'

    website_button = ""
    if ad.get("link"):
        website_button = f'''
        <a class="website-btn" href="{escape(ad["link"], quote=True)}" target="_blank" rel="noopener noreferrer">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
          Visit Website
        </a>
        '''

    return f'''
    <html>
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
      </head>
      <body>
        <div id="ad-{ad_id}" class="card-anchor"></div>
        <div class="card-container">
          <div class="card-grid">
            <!-- Left Column: Media & Contact -->
            <div class="column-left">
              {media_markup}
              <div class="contact-info">
                <p class="contact-title">Media Contact</p>
                <div class="contact-row"><span>👤</span> {author}</div>
                <div class="contact-row"><span>💬</span> {whatsapp}</div>
                <div class="contact-row"><span>📍</span> {location}</div>
              </div>
            </div>
            
            <!-- Right Column: Details -->
            <div class="column-right">
              <div class="card-header">
                <span class="ad-tag">SPONSORED AD</span>
                <span class="timestamp">{timestamp}</span>
              </div>
              <h1 class="card-title">{title}</h1>
              <p class="card-description">{description}</p>
              
              <div class="price-box">
                <span class="price-label">Price</span>
                <span class="price-value">💰 {price}</span>
              </div>
              
              <div class="action-footer">
                {website_button}
                <a class="contact-btn" href="{escape(action_url or '#', quote=True)}" target="_blank">
                   <span>{escape(action_text)}</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      </body>
      <style>
        :root {{
          --primary: #002395;
          --accent: #ce1126;
          --text-main: #1e293b;
          --text-muted: #64748b;
          --bg-light: #f8fafc;
          --border: #e2e8f0;
        }}
        body {{ margin: 0; padding: 10px; font-family: 'Outfit', sans-serif; background: transparent; overflow: hidden; }}
        
        .card-anchor {{ position: absolute; top: -20px; }}
        
        .card-container {{
          background: #ffffff;
          border-radius: 20px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.08);
          border: 1px solid var(--border);
          overflow: hidden;
          max-width: 800px;
          margin: 0 auto;
        }}
        
        .card-grid {{
          display: grid;
          grid-template-columns: 1fr 1.2fr;
          min-height: 480px;
        }}
        
        @media (max-width: 600px) {{
          .card-grid {{ grid-template-columns: 1fr; }}
        }}

        /* Left Column */
        .column-left {{
          background: var(--bg-light);
          padding: 24px;
          display: flex;
          flex-direction: column;
          gap: 20px;
          border-right: 1px solid var(--border);
        }}
        
        .card-media-wrapper {{
          width: 100%;
          aspect-ratio: 1;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 4px 12px rgba(0,0,0,0.05);
          background: #000;
          display: flex;
          align-items: center;
          justify-content: center;
        }}
        .card-media {{ width: 100%; height: 100%; object-fit: cover; }}
        
        .fallback-media {{
          width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
          background: linear-gradient(135deg, var(--primary), var(--accent));
          color: white; font-weight: 800; font-size: 32px;
        }}
        
        .contact-info {{
          background: white;
          padding: 16px;
          border-radius: 12px;
          border: 1px solid var(--border);
        }}
        .contact-title {{
          margin: 0 0 10px 0;
          font-size: 11px;
          font-weight: 800;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }}
        .contact-row {{
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          font-weight: 600;
          color: var(--text-main);
          margin-bottom: 6px;
        }}
        .contact-row span {{ width: 18px; text-align: center; }}

        /* Right Column */
        .column-right {{
          padding: 32px;
          display: flex;
          flex-direction: column;
        }}
        
        .card-header {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }}
        .ad-tag {{
          font-size: 10px;
          font-weight: 800;
          background: var(--primary);
          color: white;
          padding: 3px 8px;
          border-radius: 4px;
        }}
        .timestamp {{ font-size: 11px; color: var(--text-muted); font-weight: 600; }}
        
        .card-title {{
          margin: 0 0 12px 0;
          font-size: 24px;
          font-weight: 800;
          color: #0f172a;
          line-height: 1.2;
        }}
        
        .card-description {{
          margin: 0 0 24px 0;
          font-size: 15px;
          color: var(--text-muted);
          line-height: 1.6;
          flex-grow: 1;
        }}
        
        .price-box {{
          background: #f1f5f9;
          padding: 16px;
          border-radius: 12px;
          margin-bottom: 24px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }}
        .price-label {{ font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; }}
        .price-value {{ font-size: 18px; font-weight: 800; color: var(--primary); }}
        
        .action-footer {{
          display: flex;
          gap: 12px;
        }}
        
        .website-btn, .contact-btn {{
          flex: 1;
          height: 44px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          text-decoration: none;
          font-weight: 700;
          font-size: 14px;
          transition: all 0.3s ease;
        }}
        
        .website-btn {{
          background: white;
          color: var(--text-main);
          border: 1px solid var(--border);
        }}
        .website-btn:hover {{ background: #f8fafc; border-color: var(--text-muted); }}
        
        .contact-btn {{
          background: var(--primary);
          color: white;
        }}
        .contact-btn:hover {{ background: #1e3a8a; transform: translateY(-1px); }}
      </style>
    </html>
    '''


def build_blog_post_card_html(entry):
    user = entry.get("user", {})
    form_name = escape(str(entry.get("form", "Community Response")))
    timestamp = escape(str(entry.get("timestamp", "")))
    name = escape(str(user.get("name", "Community member")))
    email = escape(mask_email(user.get("email", "No email provided")))
    phone = escape(mask_phone(user.get("phone", "No phone provided")))

    text_rows = []
    media_blocks = []
    responses = entry.get("responses", {})
    text_line_units = 0

    for key, value in responses.items():
        if isinstance(value, dict) and value.get("path"):
            media_kind, media_uri = get_media_data_uri(value)
            if media_uri and media_kind == "video":
                media_blocks.append(
                    f'''
                    <div class="media-card">
                      <p class="media-label">{escape(str(key))}</p>
                      <video controls playsinline preload="metadata" src="{media_uri}"></video>
                    </div>
                    '''
                )
            elif media_uri:
                media_blocks.append(
                    f'''
                    <div class="media-card">
                      <p class="media-label">{escape(str(key))}</p>
                      <img src="{media_uri}" alt="{escape(str(key))}">
                    </div>
                    '''
                )
        else:
            safe_key = escape(str(key))
            safe_value = escape(str(value if value is not None else "")) or "Not provided"
            combined_text = f"{safe_key} {safe_value}"
            text_line_units += max(2, (len(combined_text) + 59) // 60)
            text_rows.append(
                f'<li class="response-item response-item--{(len(text_rows) % 5) + 1}"><span class="label">{safe_key}</span><span class="value">{safe_value}</span></li>'
            )

    responses_markup = "".join(text_rows) or "<li><span class=\"value\">No response details provided.</span></li>"
    media_markup = ""
    if media_blocks:
        media_markup = f'<div class="media-grid">{"".join(media_blocks)}</div>'

    metadata_line_units = max(4, (len(email) + len(phone) + len(form_name) + len(timestamp) + 79) // 80)
    estimated_height = 260 + (text_line_units * 28) + (metadata_line_units * 22) + (len(media_blocks) * 320)
    card_height = min(max(estimated_height, 420), 1500)

    return (
        f'''
        <html>
          <body>
            <div class="card">
              <div class="content">
                <div class="meta-block">
                  <p class="eyebrow">Public Blog Post</p>
                  <p class="heading">{name}</p>
                  <p class="meta">{form_name}</p>
                  <p class="meta">{email} • {phone}</p>
                  <p class="meta">{timestamp}</p>
                </div>
                <ul class="response-list">{responses_markup}</ul>
                {media_markup}
              </div>
            </div>
          </body>
          <style>
            body {{
              margin: 0;
              padding: 8px 2px 18px;
              background: transparent;
              font-family: Arial, sans-serif;
            }}

            .card {{
              position: relative;
              display: flex;
              align-items: center;
              justify-content: center;
              width: 100%;
              padding: 2px;
              border-radius: 24px;
              overflow: hidden;
              line-height: 1.6;
              transition: all 0.48s cubic-bezier(0.23, 1, 0.32, 1);
              isolation: isolate;
            }}

            .content {{
              position: relative;
              z-index: 1;
              display: flex;
              flex-direction: column;
              align-items: flex-start;
              gap: 18px;
              padding: 28px;
              border-radius: 22px;
              color: #0f172a;
              overflow: hidden;
              background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
              width: 100%;
              box-sizing: border-box;
              transition: all 0.48s cubic-bezier(0.23, 1, 0.32, 1);
              box-shadow: 0 18px 38px rgba(15, 23, 42, 0.10);
            }}

            .heading {{
              margin: 0;
              font-weight: 700;
              font-size: 24px;
              line-height: 1.2;
              overflow-wrap: anywhere;
              transition: all 0.48s cubic-bezier(0.23, 1, 0.32, 1);
            }}

            .eyebrow, .meta {{
              margin: 0;
            }}

            .eyebrow {{
              font-size: 12px;
              letter-spacing: 0.08em;
              text-transform: uppercase;
              color: #007a4d;
              font-weight: 700;
            }}

            .meta {{
              color: #475569;
              font-size: 14px;
              line-height: 1.5;
              overflow-wrap: anywhere;
            }}

            .response-list {{
              list-style: none;
              padding: 0;
              margin: 0;
              width: 100%;
              display: flex;
              flex-direction: column;
              gap: 10px;
            }}

            .response-list li {{
              display: flex;
              flex-direction: column;
              gap: 4px;
              padding: 12px 14px;
              border-radius: 14px;
              background: #f8fafc;
              border-left: 4px solid transparent;
              transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
            }}

            .response-item--1 {{ background: linear-gradient(90deg, #fff1f2 0%, #ffffff 100%); border-left-color: #ce1126; }}
            .response-item--2 {{ background: linear-gradient(90deg, #eff6ff 0%, #ffffff 100%); border-left-color: #002395; }}
            .response-item--3 {{ background: linear-gradient(90deg, #f0fdf4 0%, #ffffff 100%); border-left-color: #007a4d; }}
            .response-item--4 {{ background: linear-gradient(90deg, #fff8e1 0%, #ffffff 100%); border-left-color: #ffb612; }}
            .response-item--5 {{ background: linear-gradient(90deg, #f3f4f6 0%, #ffffff 100%); border-left-color: #111827; }}

            .response-item--1:hover {{ background: linear-gradient(90deg, #ffe4e6 0%, #fff1f2 100%); box-shadow: 0 10px 18px rgba(206, 17, 38, 0.10); transform: translateX(2px); }}
            .response-item--2:hover {{ background: linear-gradient(90deg, #dbeafe 0%, #eff6ff 100%); box-shadow: 0 10px 18px rgba(0, 35, 149, 0.10); transform: translateX(2px); }}
            .response-item--3:hover {{ background: linear-gradient(90deg, #dcfce7 0%, #f0fdf4 100%); box-shadow: 0 10px 18px rgba(0, 122, 77, 0.10); transform: translateX(2px); }}
            .response-item--4:hover {{ background: linear-gradient(90deg, #fef3c7 0%, #fff8e1 100%); box-shadow: 0 10px 18px rgba(255, 182, 18, 0.12); transform: translateX(2px); }}
            .response-item--5:hover {{ background: linear-gradient(90deg, #e5e7eb 0%, #f3f4f6 100%); box-shadow: 0 10px 18px rgba(17, 24, 39, 0.12); transform: translateX(2px); }}

            .label {{
              font-size: 11px;
              font-weight: 700;
              color: #002395;
              text-transform: none;
              line-height: 1.45;
              overflow-wrap: anywhere;
            }}

            .value {{
              font-size: 14px;
              line-height: 1.55;
              color: #111827;
              overflow-wrap: anywhere;
              word-break: break-word;
            }}

            .media-grid {{
              display: grid;
              grid-template-columns: 1fr;
              gap: 14px;
              width: 100%;
            }}

            .media-card {{
              background: linear-gradient(135deg, #eff6ff 0%, #fff8e1 100%);
              border-radius: 16px;
              padding: 14px;
              border: 1px solid rgba(17, 24, 39, 0.08);
              transition: transform 0.2s ease, box-shadow 0.2s ease;
            }}

            .media-card:hover {{
              transform: translateY(-2px);
              box-shadow: 0 14px 24px rgba(0, 35, 149, 0.08), 0 10px 18px rgba(0, 122, 77, 0.08), 0 6px 14px rgba(255, 182, 18, 0.10);
            }}

            .media-label {{
              margin: 0 0 10px;
              color: #007a4d;
              font-size: 12px;
              font-weight: 700;
              text-transform: none;
              line-height: 1.4;
              overflow-wrap: anywhere;
            }}

            .media-card img,
            .media-card video {{
              width: 100%;
              max-height: 260px;
              object-fit: cover;
              border-radius: 14px;
              background: #dbe4ff;
            }}

            .card::before {{
              content: "";
              position: absolute;
              inset: -30%;
              border-radius: inherit;
              background: conic-gradient(from 0deg, #111827, #ce1126, #002395, #007a4d, #ffb612, #111827);
              transform-origin: center;
              animation: moving 4.8s linear infinite paused;
              transition: all 0.88s cubic-bezier(0.23, 1, 0.32, 1);
            }}

            .card:hover::before {{
              animation-play-state: running;
              width: 20%;
            }}

            .card:hover {{
              box-shadow: 0rem 8px 18px rgba(17, 24, 39, 0.12),
                0rem 22px 28px rgba(0, 35, 149, 0.08),
                0rem 42px 36px rgba(0, 122, 77, 0.05),
                0rem 70px 44px rgba(206, 17, 38, 0.02);
              transform: scale(1.01);
            }}

            @keyframes moving {{
              0% {{
                transform: rotate(0);
              }}

              100% {{
                transform: rotate(360deg);
              }}
            }}
          </style>
        </html>
        ''',
        card_height,
    )


def build_sidebar_link_buttons_html(links):
    buttons = []
    for idx, link in enumerate(links):
        theme_index = (idx % 5) + 1
        buttons.append(
            f'''
            <a class="sidebar-link theme-{theme_index}" href="{escape(link["url"], quote=True)}" target="_blank" rel="noopener noreferrer">
              <button type="button">{escape(link["label"])}</button>
            </a>
            '''
        )

    return f'''
    <html>
      <body>
        <div class="button-list">{"".join(buttons)}</div>
      </body>
      <style>
        body {{
          margin: 0;
          padding: 0;
          background: transparent;
          font-family: Arial, sans-serif;
        }}

        .button-list {{
          display: flex;
          flex-direction: column;
          gap: 12px;
          padding: 4px 0 10px;
        }}

        .sidebar-link {{
          text-decoration: none;
          display: block;
        }}

        .theme-1 {{ --hover-main: #ce1126; --hover-soft: #ef4444; --hover-text: #ffffff; }}
        .theme-2 {{ --hover-main: #002395; --hover-soft: #2563eb; --hover-text: #ffffff; }}
        .theme-3 {{ --hover-main: #007a4d; --hover-soft: #16a34a; --hover-text: #ffffff; }}
        .theme-4 {{ --hover-main: #ffb612; --hover-soft: #f59e0b; --hover-text: #111827; }}
        .theme-5 {{ --hover-main: #111827; --hover-soft: #374151; --hover-text: #ffffff; }}

        button {{
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(241, 245, 249, 0.96));
          border: 1px solid rgba(255, 255, 255, 0.18);
          padding: 1rem;
          font-size: 1rem;
          width: 100%;
          border-radius: 1rem;
          color: #111827;
          box-shadow: 0 0.4rem rgba(148, 163, 184, 0.45);
          cursor: pointer;
          font-weight: 700;
          transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, color 0.2s ease;
        }}

        button:active {{
          color: white;
          box-shadow: 0 0.2rem rgba(148, 163, 184, 0.45);
          transform: translateY(0.2rem);
        }}

        .sidebar-link:hover button {{
          background: linear-gradient(90deg, #111827 0%, var(--hover-main) 56%, var(--hover-soft) 100%);
          color: var(--hover-text);
          box-shadow: 0 0.55rem 1rem rgba(17, 24, 39, 0.28);
          transform: translateY(-2px);
        }}
      </style>
    </html>
    '''


def get_first_response_value(responses, possible_keys):
    for key in possible_keys:
        value = responses.get(key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def normalize_poll_entry(entry):

    def clean_text(value, fallback):
        if value is None:
            return fallback
        text = str(value).strip()
        return text if text else fallback

    def format_store_name(value, fallback):
        text = clean_text(value, fallback)
        brand_map = {
            "absa": "ABSA",
            "fnb": "FNB",
            "tymebank": "TymeBank",
            "capitec": "Capitec",
            "standard bank": "Standard Bank",
            "nedbank": "Nedbank",
            "shoprite": "Shoprite",
            "spar": "SPAR",
            "jet": "Jet",
            "truworths": "Truworths",
        }
        lowered = text.lower()
        if lowered in brand_map:
            return brand_map[lowered]
        return text.title() if text.islower() else text

    def format_location(value, fallback):
        text = clean_text(value, fallback)
        return text.title() if text.islower() else text

    def format_gender(value):
        text = clean_text(value, "Not provided")
        gender_map = {
            "female": "Female",
            "male": "Male",
            "non-binary": "Non-binary",
            "prefer not to say": "Prefer not to say",
            "other": "Other",
            "not provided": "Not provided",
        }
        lowered = text.lower()
        if lowered in gender_map:
            return gender_map[lowered]
        return text.title() if text.islower() else text

    if isinstance(entry, str):
        store_name = format_store_name(entry, "Unknown Store")
        return {
            "store": store_name,
            "province": "Unknown Province",
            "city": "Unknown City",
            "town": "Unknown Town",
            "age": "Unknown Age",
            "gender": "Not provided",
            "star_rating": 0,
            "satisfaction": "Not provided",
            "decision_driver": "Not provided",
            "suggestion": "Not provided",
            "submitted_at": "Unknown Date",
            "mention_count": 1,
        }

    if not isinstance(entry, dict):
        return None

    age_value = entry.get("age")
    if age_value in (None, ""):
        age_text = "Unknown Age"
    else:
        age_text = str(age_value)

    star_rating_value = entry.get("star_rating")
    if star_rating_value is None:
        star_rating_value = entry.get("service_star_rating")
    if star_rating_value is None:
        star_rating_value = entry.get("rating")

    return {
        "store": format_store_name(entry.get("store"), "Unknown Store"),
        "province": format_location(entry.get("province"), "Unknown Province"),
        "city": format_location(entry.get("city"), "Unknown City"),
        "town": format_location(entry.get("town"), "Unknown Town"),
        "age": age_text,
        "gender": format_gender(entry.get("gender")),
        "star_rating": normalize_star_rating(star_rating_value),
        "satisfaction": clean_text(entry.get("satisfaction"), "Not provided"),
        "decision_driver": clean_text(entry.get("decision_driver"), "Not provided"),
        "suggestion": clean_text(entry.get("suggestion"), "Not provided"),
        "submitted_at": clean_text(entry.get("submitted_at") or entry.get("timestamp"), "Unknown Date"),
        "mention_count": entry.get("mention_count", 1),
    }


def build_retail_poll_entries(blog_entries, saved_poll_entries):
    detailed_entries = []
    detailed_signatures = set()

    store_keys = [
        "Which retail stores do you visit most often?",
        "Which retail brand or chain do you spend with most often?",
    ]
    satisfaction_keys = [
        "How satisfied are you with the cleanliness and security of these stores?",
        "How would you rate the overall in-store service, cleanliness, and stock availability?",
    ]
    driver_keys = [
        "What do you value most: price, quality, or convenience?",
        "Which factor most influences where you shop?",
    ]
    suggestion_keys = [
        "Any suggestions for improvement?",
        "What one improvement would increase your spending or loyalty?",
    ]
    rating_keys = [
        SERVICE_STAR_RATING_LABEL,
        "Rate the service using stars",
        "Service star rating",
        "Star rating",
    ]

    for blog_entry in blog_entries:
        responses = blog_entry.get("responses", {})
        store_value = get_first_response_value(responses, store_keys)
        if store_value is None:
            continue

        normalized = normalize_poll_entry(
            {
                "store": store_value,
                "age": responses.get("Age"),
                "gender": responses.get("Gender") or blog_entry.get("user", {}).get("gender"),
                "province": responses.get("Province"),
                "city": responses.get("City"),
                "town": responses.get("Town"),
                "star_rating": get_first_response_value(responses, rating_keys),
                "satisfaction": get_first_response_value(responses, satisfaction_keys),
                "decision_driver": get_first_response_value(responses, driver_keys),
                "suggestion": get_first_response_value(responses, suggestion_keys),
                "submitted_at": blog_entry.get("timestamp"),
            }
        )
        if normalized is None:
            continue

        signature = (
            normalized["store"].lower(),
            str(normalized["age"]).lower(),
            normalized["gender"].lower(),
            normalized["province"].lower(),
            normalized["city"].lower(),
            normalized["town"].lower(),
        )
        detailed_signatures.add(signature)
        detailed_entries.append(normalized)

    for saved_entry in saved_poll_entries:
        normalized = normalize_poll_entry(saved_entry)
        if normalized is None:
            continue

        signature = (
            normalized["store"].lower(),
            str(normalized["age"]).lower(),
            normalized["gender"].lower(),
            normalized["province"].lower(),
            normalized["city"].lower(),
            normalized["town"].lower(),
        )
        if signature not in detailed_signatures:
            detailed_entries.append(normalized)

    mention_counts = Counter(row["store"].lower() for row in detailed_entries)
    for row in detailed_entries:
        row["mention_count"] = mention_counts[row["store"].lower()]

    return list(reversed(detailed_entries))


def get_retailer_url(store_name):
    normalized_name = str(store_name or "").strip().lower()
    return RETAILER_LINKS.get(normalized_name)


def build_poll_cards_html(rows):
    icons = [
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="rgba(149,149,255,1)" d="M17 15.245v6.872a.5.5 0 0 1-.757.429L12 20l-4.243 2.546a.5.5 0 0 1-.757-.43v-6.87a8 8 0 1 1 10 0zm-8 1.173v3.05l3-1.8 3 1.8v-3.05A7.978 7.978 0 0 1 12 17a7.978 7.978 0 0 1-3-.582zM12 15a6 6 0 1 0 0-12 6 6 0 0 0 0 12z"></path></svg>',
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M16 16c1.657 0 3 1.343 3 3s-1.343 3-3 3-3-1.343-3-3 1.343-3 3-3zM6 12c2.21 0 4 1.79 4 4s-1.79 4-4 4-4-1.79-4-4 1.79-4 4-4zm10 6c-.552 0-1 .448-1 1s.448 1 1 1 1-.448 1-1-.448-1-1-1zM6 14c-1.105 0-2 .895-2 2s.895 2 2 2 2-.895 2-2-.895-2-2-2zm8.5-12C17.538 2 20 4.462 20 7.5S17.538 13 14.5 13 9 10.538 9 7.5 11.462 2 14.5 2zm0 2C12.567 4 11 5.567 11 7.5s1.567 3.5 3.5 3.5S18 9.433 18 7.5 16.433 4 14.5 4z" fill="rgba(252,161,71,1)"></path></svg>',
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="rgba(66,193,110,1)" d="M20.083 15.2l1.202.721a.5.5 0 0 1 0 .858l-8.77 5.262a1 1 0 0 1-1.03 0l-8.77-5.262a.5.5 0 0 1 0-.858l1.202-.721L12 20.05l8.083-4.85zm0-4.7l1.202.721a.5.5 0 0 1 0 .858L12 17.65l-9.285-5.571a.5.5 0 0 1 0-.858l1.202-.721L12 15.35l8.083-4.85zm-7.569-9.191l8.771 5.262a.5.5 0 0 1 0 .858L12 13 2.715 7.429a.5.5 0 0 1 0-.858l8.77-5.262a1 1 0 0 1 1.03 0zM12 3.332L5.887 7 12 10.668 18.113 7 12 3.332z"></path></svg>',
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="rgba(220,91,183,1)" d="M12 20h8v2h-8C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10a9.956 9.956 0 0 1-2 6h-2.708A8 8 0 1 0 12 20zm0-10a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm-4 4a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm8 0a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm-4 4a2 2 0 1 1 0-4 2 2 0 0 1 0 4z"></path></svg>',
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="rgba(15,23,42,1)" d="M7 4h10a2 2 0 0 1 2 2v12.5a1.5 1.5 0 0 1-2.56 1.06L12 15.12l-4.44 4.44A1.5 1.5 0 0 1 5 18.5V6a2 2 0 0 1 2-2zm0 2v10.38l4.29-4.3a1 1 0 0 1 1.42 0L17 16.38V6H7z"></path></svg>',
    ]

    items = []
    for idx, row in enumerate(rows):
        theme_index = (idx % 5) + 1
        retailer_url = get_retailer_url(row["store"])
        store_name = escape(row["store"])
        star_rating = normalize_star_rating(row.get("star_rating"))
        empty_star_class = " star-rating--empty" if star_rating == 0 else ""
        star_icons = "".join(
            f'<span class="star{" star--filled" if position <= star_rating else ""}">★</span>'
            for position in range(1, 6)
        )
        star_rating_text = f"{star_rating}/5" if star_rating else "Not yet rated"
        star_rating_markup = (
            f'<div class="star-rating{empty_star_class}" '
            f'aria-label="{escape(star_rating_text)}">'
            '<span class="star-rating__label"><strong>Star rating:</strong></span>'
            f'<span class="star-rating__icons">{star_icons}</span>'
            f'<span class="star-rating__text">{escape(star_rating_text)}</span>'
            '</div>'
        )
        store_markup = store_name
        visit_link_markup = ""
        item_classes = f"item item--{theme_index}"
        item_interaction_attrs = ""

        if retailer_url:
            safe_url = escape(retailer_url, quote=True)
            item_classes += " clickable"
            item_interaction_attrs = (
                f' role="link" tabindex="0" '
                f'onclick="window.open(\'{safe_url}\', \'_blank\', \'noopener,noreferrer\');" '
                f'onkeydown="if(event.key===\'Enter\' || event.key===\' \'){{event.preventDefault();window.open(\'{safe_url}\', \'_blank\', \'noopener,noreferrer\');}}"'
            )
            store_markup = (
                f'<a class="store-link" href="{safe_url}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation();">'
                f'{store_name} <span class="store-link__icon">↗</span></a>'
            )
            visit_link_markup = (
                f'<a class="visit-link" href="{safe_url}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation();">'
                'Visit official site</a>'
            )

        items.append(
            f'''
            <div class="{item_classes}"{item_interaction_attrs}>
              {icons[idx % len(icons)]}
              <span class="quantity">{store_markup}</span>
              <span class="metric-badge">Mentions: {escape(str(row.get("mention_count", 1)))}</span>
              {star_rating_markup}
              {visit_link_markup}
              <span class="text text--{theme_index}">Age: {escape(str(row["age"]))} • Gender: {escape(row["gender"])}</span>
              <span class="meta"><strong>Province:</strong> {escape(row["province"])}</span>
              <span class="meta"><strong>City:</strong> {escape(row["city"])}</span>
              <span class="meta"><strong>Town:</strong> {escape(row["town"])}</span>
              <span class="meta"><strong>Service feedback:</strong> {escape(row["satisfaction"])}</span>
              <span class="meta"><strong>Decision driver:</strong> {escape(row["decision_driver"])}</span>
              <span class="meta"><strong>Improvement requested:</strong> {escape(row["suggestion"])}</span>
              <span class="meta"><strong>Submitted:</strong> {escape(row["submitted_at"])}</span>
            </div>
            '''
        )

    return f'''
    <html>
      <body>
        <div class="card">{"".join(items)}</div>
      </body>
      <style>
        body {{
          margin: 0;
          padding: 0;
          background: transparent;
          font-family: Arial, sans-serif;
        }}

        .card {{
          width: 100%;
          color: #0f172a;
          display: grid;
          grid-template-columns: 1fr;
          gap: 8px;
          overflow-y: auto;
          padding-right: 4px;
          box-sizing: border-box;
        }}

        .card .item {{
          position: relative;
          border-radius: 16px;
          width: 100%;
          min-height: 240px;
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          justify-content: flex-start;
          text-align: left;
          padding: 16px 14px;
          box-sizing: border-box;
          border-left: 6px solid rgba(255, 255, 255, 0.95);
          box-shadow: 0 14px 28px rgba(15, 23, 42, 0.18);
          overflow: hidden;
          transition: transform 0.25s ease, box-shadow 0.25s ease, filter 0.25s ease;
        }}

        .card .item::before {{
          content: "";
          position: absolute;
          inset: 0;
          background: linear-gradient(140deg, rgba(255,255,255,0.18), rgba(255,255,255,0.02));
          pointer-events: none;
        }}

        .item:hover,
        .item.clickable:focus-visible {{
          transform: translateY(-4px) scale(1.01);
          box-shadow: 0 20px 34px var(--item-hover-shadow);
          filter: saturate(1.04);
          outline: none;
        }}

        .item.clickable {{ cursor: pointer; }}

        .item svg {{
          width: 34px;
          height: 34px;
          margin-bottom: 8px;
        }}

        .item > * {{
          position: relative;
          z-index: 1;
        }}

        .item--1 {{
          background: linear-gradient(135deg, #ce1126 0%, #ef4444 100%);
          color: #fff8eb;
          --item-hover-shadow: rgba(206, 17, 38, 0.34);
          --store-hover-color: #fff1b5;
          --visit-bg: rgba(255, 248, 235, 0.96);
          --visit-text: #7f1d1d;
          --visit-hover-bg: #111827;
          --visit-hover-text: #fff8eb;
        }}

        .item--2 {{
          background: linear-gradient(135deg, #002395 0%, #2563eb 100%);
          color: #eff6ff;
          --item-hover-shadow: rgba(0, 35, 149, 0.30);
          --store-hover-color: #bfdbfe;
          --visit-bg: rgba(239, 246, 255, 0.96);
          --visit-text: #002395;
          --visit-hover-bg: #ffb612;
          --visit-hover-text: #111827;
        }}

        .item--3 {{
          background: linear-gradient(135deg, #007a4d 0%, #16a34a 100%);
          color: #f0fdf4;
          --item-hover-shadow: rgba(0, 122, 77, 0.30);
          --store-hover-color: #dcfce7;
          --visit-bg: rgba(240, 253, 244, 0.96);
          --visit-text: #065f46;
          --visit-hover-bg: #002395;
          --visit-hover-text: #ffffff;
        }}

        .item--4 {{
          background: linear-gradient(135deg, #ffb612 0%, #f59e0b 100%);
          color: #1f2937;
          --item-hover-shadow: rgba(255, 182, 18, 0.32);
          --store-hover-color: #002395;
          --visit-bg: rgba(17, 24, 39, 0.92);
          --visit-text: #fff8eb;
          --visit-hover-bg: #ce1126;
          --visit-hover-text: #ffffff;
        }}

        .item--5 {{
          background: linear-gradient(135deg, #111827 0%, #000000 100%);
          color: #f8fafc;
          --item-hover-shadow: rgba(17, 24, 39, 0.36);
          --store-hover-color: #ffdd57;
          --visit-bg: rgba(255, 182, 18, 0.94);
          --visit-text: #111827;
          --visit-hover-bg: #007a4d;
          --visit-hover-text: #ffffff;
        }}

        .quantity {{
          font-size: 20px;
          font-weight: 700;
          line-height: 1.3;
          word-break: break-word;
        }}

        .store-link {{
          color: inherit;
          text-decoration: none;
          border-bottom: 1px solid currentColor;
          padding-bottom: 1px;
        }}

        .store-link:hover {{
          opacity: 1;
          color: var(--store-hover-color);
        }}

        .store-link__icon {{
          font-size: 14px;
        }}

        .metric-badge {{
          margin-top: 8px;
          padding: 4px 10px;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.18);
          color: inherit;
          font-size: 11px;
          font-weight: 700;
          border: 1px solid rgba(255,255,255,0.22);
        }}

        .star-rating {{
          margin-top: 8px;
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          line-height: 1.4;
        }}

        .star-rating__label {{
          font-size: 11px;
        }}

        .star-rating__icons {{
          display: inline-flex;
          gap: 1px;
        }}

        .star {{
          color: rgba(255, 255, 255, 0.38);
          font-size: 15px;
          text-shadow: 0 1px 3px rgba(17, 24, 39, 0.16);
        }}

        .item--4 .star {{
          color: rgba(17, 24, 39, 0.24);
        }}

        .star--filled {{
          color: #ffec8b;
        }}

        .item--4 .star--filled {{
          color: #111827;
        }}

        .star-rating__text {{
          font-weight: 700;
        }}

        .star-rating--empty .star-rating__text {{
          opacity: 0.9;
        }}

        .visit-link {{
          margin-top: 8px;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 5px 10px;
          border-radius: 999px;
          background: var(--visit-bg);
          color: var(--visit-text);
          text-decoration: none;
          font-size: 11px;
          font-weight: 700;
          transition: transform 0.2s ease, background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
        }}

        .visit-link:hover {{
          background: var(--visit-hover-bg);
          color: var(--visit-hover-text);
          transform: translateY(-1px);
          box-shadow: 0 10px 18px rgba(17, 24, 39, 0.18);
        }}

        .text {{
          font-size: 13px;
          font-weight: 700;
          margin-top: 8px;
        }}

        .text--1, .text--2, .text--3, .text--5 {{ color: rgba(255,255,255,0.95); }}
        .text--4 {{ color: rgba(17,24,39,0.9); }}

        .meta {{
          font-size: 11px;
          line-height: 1.45;
          color: inherit;
          opacity: 0.96;
          margin-top: 4px;
          overflow-wrap: anywhere;
        }}

        .meta strong {{
          color: inherit;
        }}
      </style>
    </html>
    '''


def show_transition_loader(title, message, duration_seconds=1):
    loader_html = """
    <div style="display:flex;justify-content:center;padding:0.5rem 0 0.25rem;">
      <div class="loader">
        <div class="inner_loader"></div>
      </div>
    </div>
    <style>
    .loader {
      width: 200px;
      height: 10px;
      background: linear-gradient(90deg, rgba(17, 24, 39, 0.98) 0%, rgba(0, 35, 149, 0.90) 100%);
      border-radius: 50px;
      overflow: hidden;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08), 0 10px 18px rgba(15, 23, 42, 0.12);
    }

    .inner_loader {
      width: 60%;
      height: 100%;
      background: linear-gradient(90deg, #ce1126 0%, #002395 38%, #007a4d 70%, #ffb612 100%);
      border-radius: 50px;
      animation: moveLeftRight 3s ease-in-out infinite;
      box-shadow: 0 0 14px rgba(255, 182, 18, 0.35);
    }

    @keyframes moveLeftRight {
      0% {
        transform: translateX(calc(-100% + 10px));
      }

      50% {
        transform: translateX(calc(200px - 10px));
      }

      100% {
        transform: translateX(calc(-100% + 10px));
      }
    }
    </style>
    """

    with st.container(border=True):
        st.markdown(f"#### {title}")
        st.caption(message)
        components.html(loader_html, height=50)

    time.sleep(duration_seconds)


def show_submission_notification(title="Congratulations", subtitle="your response was submitted"):
    notification_html = f"""
    <div class="card">
      <svg height="180px" width="200px" version="1.1" id="Layer_1" viewBox="0 0 512 512" xml:space="preserve" class="metal">
        <path style="fill: #ffc61b" d="M256,512c-76.231,0-138.249-62.018-138.249-138.249c0-76.232,62.018-138.25,138.249-138.25 c23.8,0,47.273,6.151,67.886,17.79c7.033,3.971,9.515,12.892,5.544,19.927c-3.971,7.033-12.896,9.515-19.927,5.544 c-16.232-9.166-34.733-14.009-53.503-14.009c-60.102,0-108.999,48.898-108.999,109S195.899,482.751,256,482.751 s108.999-48.896,108.999-108.999c0-8.077,6.549-14.625,14.625-14.625c8.076,0,14.625,6.548,14.625,14.625 C394.249,449.982,332.231,512,256,512z"></path>
        <path style="fill: #fee187" d="M256,424.249c-27.845,0-50.498-22.653-50.498-50.498s22.653-50.499,50.498-50.499 s50.498,22.654,50.498,50.499C306.498,401.596,283.845,424.249,256,424.249z"></path>
        <g>
          <path style="fill: #ffc61b" d="M256,438.874c-35.909,0-65.123-29.214-65.123-65.123s29.215-65.125,65.123-65.125 s65.123,29.215,65.123,65.124S291.908,438.874,256,438.874z M256,337.877c-19.781,0-35.873,16.092-35.873,35.874 c0,19.781,16.092,35.873,35.873,35.873s35.873-16.092,35.873-35.873C291.873,353.969,275.781,337.877,256,337.877z"></path>
          <path style="fill: #ffc61b" d="M316.661,280.679c-2.437,0-4.905-0.61-7.178-1.893c-16.262-9.182-34.757-14.036-53.483-14.036 s-37.221,4.853-53.483,14.036c-6.986,3.943-15.846,1.525-19.857-5.423l-58.24-100.876c-4.039-6.995-1.642-15.94,5.353-19.978 c6.995-4.038,15.94-1.642,19.978,5.353l51.383,88.997c17.255-7.462,35.969-11.359,54.868-11.359s37.613,3.899,54.868,11.359 l49.423-85.604V29.25h-25.8c-8.076,0-14.625-6.548-14.625-14.625S326.416,0,334.492,0h40.426c8.076,0,14.625,6.548,14.625,14.625 v150.55c0,2.567-0.676,5.09-1.96,7.313l-58.24,100.876C326.632,278.053,321.717,280.679,316.661,280.679z"></path>
        </g>
        <path style="fill: #fee187" d="M256,250.126c0.41,0,0.812,0.026,1.22,0.031V14.625H137.084v150.55l58.242,100.876 C213.253,255.929,233.942,250.126,256,250.126z"></path>
        <path style="fill: #ffc61b" d="M195.338,280.679c-5.057,0-9.971-2.625-12.679-7.314l-58.24-100.876 c-1.284-2.223-1.96-4.746-1.96-7.313V14.625C122.459,6.548,129.008,0,137.084,0H257.22c8.076,0,14.625,6.548,14.625,14.625v235.531 c0,3.905-1.562,7.648-4.338,10.396c-2.776,2.747-6.511,4.291-10.441,4.23c-0.309-0.003-0.616-0.013-0.923-0.023l-0.211-0.007 c-18.662,0-37.155,4.854-53.417,14.037C200.243,280.069,197.774,280.679,195.338,280.679z M151.709,161.256l49.423,85.604 c13.161-5.691,27.171-9.309,41.462-10.706V29.25h-90.885V161.256L151.709,161.256z"></path>
      </svg>
      <span class="text-1">{escape(title)}</span>
      <span class="text-2">{escape(subtitle)}</span>
    </div>

    <style>
      body {{
        margin: 0;
        padding: 0;
        background: transparent;
        display: flex;
        justify-content: center;
        align-items: center;
        font-family: Arial, sans-serif;
      }}

      .card {{
        color: #090909;
        height: 12rem;
        width: min(20rem, 96vw);
        border-radius: 1rem;
        background: linear-gradient(135deg, #111827 0%, #002395 28%, #007a4d 62%, #ffb612 82%, #ce1126 100%);
        border: 1px solid rgba(255, 255, 255, 0.35);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-end;
        box-sizing: border-box;
        box-shadow: 0 22px 40px rgba(17, 24, 39, 0.18), 0 12px 24px rgba(0, 35, 149, 0.14);
      }}

      .text-1 {{
        margin: 0;
        font-family: fantasy;
        font-size: 30px;
        padding: 0 12px 5px;
        color: transparent;
        -webkit-text-stroke: 1px #fff;
        text-align: center;
        line-height: 1.1;
      }}

      .text-2 {{
        margin: 0;
        padding: 0 12px 1.8rem;
        font-family: fantasy;
        font-size: 20px;
        color: #f8fafc;
        text-shadow: 0 2px 10px rgba(17, 24, 39, 0.35);
        text-align: center;
        line-height: 1.2;
      }}

      .text-1,
      .text-2 {{
        animation: scaling 5s infinite;
      }}

      @keyframes scaling {{
        0% {{
          transform: scale(1);
          opacity: 1;
        }}

        50% {{
          transform: scale(1.1);
          opacity: 0.8;
        }}
      }}

      .metal {{
        margin-top: 10px;
        width: 60px;
        animation: spin 5.4s cubic-bezier(0, 0.2, 0.8, 1) infinite;
      }}

      @keyframes spin {{
        0% {{
          transform: rotateY(0deg);
        }}

        100% {{
          transform: rotateY(1800deg);
          animation-timing-function: cubic-bezier(0, 0.5, 0.5, 1);
        }}
      }}
    </style>
    """

    with st.container():
        components.html(notification_html, height=230, scrolling=False)

    time.sleep(1.3)


with st.sidebar:
    st.title("Tourist Attractions")
    components.html(build_sidebar_link_buttons_html(TOURIST_LINKS), height=220, scrolling=False)


# --- AUTHENTICATION ---
def authenticate():
    st.title("Welcome to National Dialog SA")
    st.markdown("#### Please enter your details to proceed:")
    with st.form("auth_form"):
        name = st.text_input("Name", key="auth_name")
        gender = st.selectbox("Gender", GENDER_OPTIONS, key="auth_gender")
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
            st.session_state["user"] = {
                "name": name,
                "gender": gender,
                "phone": phone,
                "email": email,
            }
            # Save to JSON/CSV
            user_row = {
                "name": name,
                "gender": gender,
                "phone": phone,
                "email": email,
                "timestamp": datetime.now().isoformat(),
            }
            # JSON
            users = load_json_list(JSON_PATH)
            users.append(user_row)
            save_json_list(JSON_PATH, users)
            # CSV
            df = pd.DataFrame(users)
            df.to_csv(CSV_PATH, index=False)
            show_submission_notification(
                "Welcome",
                "your profile is ready",
            )
            st.rerun()
    st.stop()


if "user" not in st.session_state:
    authenticate()

if "blog_feed_loader_pending" not in st.session_state:
    st.session_state["blog_feed_loader_pending"] = True

# --- BLOG DATA ---
blog_data = load_json_list(BLOG_PATH)

# --- QUESTIONS (from web search and scope) ---
FORM_QUESTIONS = [
    {
        "title": "Retail & Consumer Insights",
        "poll_fields": {
            "store": "Which retail brand or chain do you spend with most often?",
            "satisfaction": "How would you rate the overall in-store service, cleanliness, and stock availability?",
            "decision_driver": "Which factor most influences where you shop?",
            "suggestion": "What one improvement would increase your spending or loyalty?",
        },
        "questions": [
            ("Which retail brand or chain do you spend with most often?", "select", ["Shoprite", "Pick n Pay", "Woolworths", "Checkers", "SPAR", "Truworths", "Jet", "Mr Price", "Pep", "Clicks", "Dis-Chem", "Other"]),
            ("How would you rate the overall in-store service, cleanliness, and stock availability?", "select", ["Excellent", "Good", "Average", "Poor", "Very Poor"]),
            ("Which factor most influences where you shop?", "select", ["Price", "Product quality", "Location convenience", "Promotions", "Staff service", "Product range", "Credit availability"]),
            ("What one improvement would increase your spending or loyalty?", "textarea")
        ]
    },
    {
        "title": "Public Service Delivery",
        "questions": [
            ("Which public service do you rely on most for your household, commute, or small business?", "select", ["Transport", "Electricity", "Water", "Clinics", "Licensing services", "Schools", "Libraries", "Waste removal", "Other"]),
            ("How would you rate the consistency and reliability of this service?", "select", ["Excellent", "Good", "Average", "Poor", "Very Poor"]),
            ("Which service issue has the biggest economic impact on you?", "textarea"),
            ("What operational improvement should be prioritised first?", "textarea")
        ]
    },
    {
        "title": "Customer Spending Behaviour",
        "questions": [
            ("Where do you complete most of your purchases?", "select", ["In-store", "Online", "Both equally", "Social commerce / WhatsApp", "Marketplace apps"]),
            ("What most influences your buying decision before checkout?", "select", ["Price", "Quality", "Delivery speed", "Brand trust", "Customer service", "Flexible payment options"]),
            ("Which brand or retailer currently earns the most trust from you, and why?", "textarea"),
            ("How important are promotions, loyalty rewards, and bundled offers to repeat purchases?", "select", ["Very Important", "Important", "Moderately Important", "Low Importance", "Not Important"])
        ]
    },
    {
        "title": "Tourism & Hospitality Experience",
        "questions": [
            ("Which tourist attraction, venue, or destination would you recommend most?", "text"),
            ("What service, business, or experience made it stand out?", "textarea"),
            ("Upload a photo or short video of the place (optional)", "file"),
            ("What should operators improve to attract more visitors and spending?", "textarea")
        ]
    },
    {
        "title": "Banking & Financial Services",
        "questions": [
            ("Which bank or financial provider do you use most often?", "select", ["ABSA", "TymeBank", "Capitec", "Standard Bank", "FNB", "Nedbank", "African Bank", "Old Mutual", "Other"]),
            ("Which banking service do you use most frequently?", "select", ["Daily transactions", "Savings", "Loans or credit", "Insurance", "Business banking", "Digital wallet / transfers", "Investments"]),
            ("How would you rate the reliability of the app, branch, ATM network, or customer support?", "select", ["Excellent", "Good", "Average", "Poor", "Very Poor"]),
            ("What is the main issue that affects your banking experience?", "textarea"),
            ("What would make you move more of your money or business to this provider?", "textarea")
        ]
    },
    {
        "title": "Cellphone Networks & Data Services",
        "questions": [
            ("Which cellphone network do you use most often?", "select", ["MTN", "Vodacom", "Cell-C", "Rain", "Telkom", "Other"]),
            ("Which service do you use most frequently on this network?", "select", ["Voice calls", "Prepaid airtime", "Data bundles", "Monthly contract", "Home internet / router", "Business connectivity"]),
            ("How would you rate signal coverage, call quality, and internet speed?", "select", ["Excellent", "Good", "Average", "Poor", "Very Poor"]),
            ("What usage issue affects you most often?", "textarea"),
            ("What pricing, coverage, or service improvement would make you spend more with this network?", "textarea")
        ]
    }
]

# --- POLL DATA ---
poll_data = load_json_list(POLL_PATH)

# --- ADS DATA ---
ads_data = load_json_list(ADS_PATH)
ads_data, ads_data_changed = prepare_ads_data(ads_data)
if ads_data_changed:
    save_json_list(ADS_PATH, ads_data)

# --- MAIN UI ---
apply_south_africa_theme()
st.title("National Dialog: South Africa")
st.caption("A national platform to understand public preferences, retail habits, and service experiences across South Africa.")

# --- TOP AD SHOWCASE (Foldable) ---
if ads_data:
    with st.expander("📢 Featured Community Ads", expanded=True):
        st.components.v1.html(build_ad_showcase_html(ads_data), height=280)

# --- AD SPACE ---
st.markdown("---")
st.subheader("Ad Space / Advertise")
ad_form_col, ad_preview_col = st.columns([1, 2])

with ad_form_col:
    st.caption("Create a small ad that can appear between public blog posts.")
    with st.form("ad_submission_form"):
        ad_title = st.text_input("Ad title")
        ad_gender_default = st.session_state.get("user", {}).get("gender", GENDER_OPTIONS[0])
        ad_gender_index = GENDER_OPTIONS.index(ad_gender_default) if ad_gender_default in GENDER_OPTIONS else 0
        ad_gender = st.selectbox("Gender", GENDER_OPTIONS, index=ad_gender_index, key="ad_gender")
        ad_description = st.text_area("Short ad description", max_chars=240)
        ad_price = st.text_input("Price or offer")
        ad_location = st.text_input("Business location")
        ad_whatsapp = st.text_input("WhatsApp number")
        ad_link = st.text_input("Optional website link")
        ad_media = st.file_uploader(
            "Upload an image or video",
            type=["png", "jpg", "jpeg", "mp4", "mov", "webm"],
            key="ad_media",
        )
        ad_submit = st.form_submit_button("Post Ad")

    if ad_submit:
        ad_errors = []
        if not ad_title.strip():
            ad_errors.append("Ad title is required.")
        if not ad_description.strip():
            ad_errors.append("Please add a short description for the ad.")
        if ad_media is None:
            ad_errors.append("Please upload an image or video for the ad.")
        if ad_whatsapp and not is_valid_sa_phone(ad_whatsapp):
            ad_errors.append("Enter a valid South African WhatsApp number (e.g., 0821234567 or +27821234567).")
        if ad_link and not ad_link.startswith(("http://", "https://")):
            ad_errors.append("Website link must start with http:// or https://")

        if ad_errors:
            for error in ad_errors:
                st.error(error)
        else:
            ad_entry = {
                "ad_id": f"ad-{uuid4().hex[:10]}",
                "title": ad_title.strip(),
                "description": ad_description.strip(),
                "gender": ad_gender,
                "price": ad_price.strip(),
                "location": ad_location.strip(),
                "whatsapp": ad_whatsapp.strip(),
                "link": ad_link.strip(),
                "media": save_uploaded_media(ad_media, AD_MEDIA_DIR),
                "author": st.session_state["user"]["name"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            ads_data.append(ad_entry)
            save_json_list(ADS_PATH, ads_data)
            show_submission_notification(
                "Success",
                "your ad was published",
            )
            st.session_state["blog_feed_loader_pending"] = True
            st.rerun()

with ad_preview_col:
    st.caption("Current ads with grid-based layout for better screen visibility")
    if ads_data:
        components.html(build_ad_showcase_html(ads_data), height=600, scrolling=True)
    else:
        render_empty_state("No ads yet. Use the form to publish the first ad.")

st.markdown("---")

# --- FORMS (Cyclable Cards) ---
form_tab = st.tabs([f"Form {i+1}: {f['title']}" for i, f in enumerate(FORM_QUESTIONS)])
for idx, (tab, form) in enumerate(zip(form_tab, FORM_QUESTIONS)):
    with tab:
        with st.form(f"form_{idx}"):
            responses = {}
            # New demographic fields
            default_gender = st.session_state.get("user", {}).get("gender", GENDER_OPTIONS[0])
            gender_index = GENDER_OPTIONS.index(default_gender) if default_gender in GENDER_OPTIONS else 0
            gender = st.selectbox("Gender", GENDER_OPTIONS, index=gender_index, key=f"gender_{idx}")
            age = st.number_input("Your Age", min_value=10, max_value=120, key=f"age_{idx}")
            province = st.text_input("Province", key=f"province_{idx}")
            city = st.text_input("City", key=f"city_{idx}")
            town = st.text_input("Town", key=f"town_{idx}")
            st.markdown(f"**{SERVICE_STAR_RATING_LABEL}**")
            feedback_val = st.feedback("stars", key=f"service_rating_{idx}")
            service_rating = (feedback_val + 1) if feedback_val is not None else None
            responses["Gender"] = gender
            responses["Age"] = age
            responses["Province"] = province
            responses["City"] = city
            responses["Town"] = town
            if service_rating is not None:
                responses[SERVICE_STAR_RATING_LABEL] = format_star_rating_text(service_rating)
            for q_idx, (q, qtype, *opts) in enumerate(form["questions"]):
                if qtype == "text":
                    responses[q] = st.text_input(q, key=f"q_{idx}_{q_idx}")
                elif qtype == "textarea":
                    responses[q] = st.text_area(q, key=f"q_{idx}_{q_idx}")
                elif qtype == "select":
                    responses[q] = st.selectbox(q, opts[0], key=f"q_{idx}_{q_idx}")
                elif qtype == "file":
                    responses[q] = st.file_uploader(q, type=["jpg", "jpeg", "png", "mp4", "mov"], key=f"q_{idx}_{q_idx}")
            submit = st.form_submit_button("Submit")
        if submit:
            if service_rating is None:
                st.warning("Please choose a star rating before submitting this form.")
            else:
                serialized_responses = {
                    question: serialize_response_value(answer)
                    for question, answer in responses.items()
                }
                entry = {
                    "user": st.session_state["user"],
                    "form": form["title"],
                    "responses": serialized_responses,
                    "timestamp": datetime.now().isoformat()
                }
                # Save to blog
                blog_data.append(entry)
                save_json_list(BLOG_PATH, blog_data)
                # Poll update (for establishments)
                poll_fields = form.get("poll_fields")
                if poll_fields and responses.get(poll_fields["store"]):
                    poll_data.append({
                        "store": responses[poll_fields["store"]],
                        "age": age,
                        "gender": gender,
                        "province": province,
                        "city": city,
                        "town": town,
                        "star_rating": service_rating,
                        "satisfaction": responses.get(poll_fields["satisfaction"]),
                        "decision_driver": responses.get(poll_fields["decision_driver"]),
                        "suggestion": responses.get(poll_fields["suggestion"]),
                        "submitted_at": entry["timestamp"],
                    })
                    save_json_list(POLL_PATH, poll_data)
                show_submission_notification(
                    "Thank You",
                    "your response was submitted",
                )
                st.session_state["blog_feed_loader_pending"] = True
                st.rerun()

# --- BLOG DISPLAY ---
st.markdown("---")
st.subheader("Public Blog: Responses from Across South Africa")
recent_blog_entries = list(reversed(blog_data[-20:]))

if st.session_state.get("blog_feed_loader_pending"):
    show_transition_loader(
        "Loading blog posts",
        "Preparing the latest public responses for you.",
        duration_seconds=2,
    )
    st.session_state["blog_feed_loader_pending"] = False

if recent_blog_entries:
    for idx, entry in enumerate(recent_blog_entries):
        blog_card_html, blog_card_height = build_blog_post_card_html(entry)
        components.html(blog_card_html, height=blog_card_height, scrolling=False)

        if ads_data and idx < len(recent_blog_entries) - 1 and idx % 2 == 0:
            ad_index = (idx // 2) % len(ads_data)
            ad = ads_data[ad_index]
            st.markdown(f'<div id="ad-{escape(ad.get("ad_id", ""), quote=True)}"></div>', unsafe_allow_html=True)
            components.html(build_blog_ad_card_html(ad), height=650, scrolling=False)

    if ads_data:
        used_count = min(len(ads_data), max(0, len(recent_blog_entries) // 2))
        remaining_ads = ads_data[used_count:]
        for ad in remaining_ads:
            st.markdown(f'<div id="ad-{escape(ad.get("ad_id", ""), quote=True)}"></div>', unsafe_allow_html=True)
            components.html(build_blog_ad_card_html(ad), height=650, scrolling=False)
else:
    if ads_data:
        st.caption("No blog posts yet, but sponsored ads are already available below.")
        for ad in reversed(ads_data):
            st.markdown(f'<div id="ad-{escape(ad.get("ad_id", ""), quote=True)}"></div>', unsafe_allow_html=True)
            components.html(build_blog_ad_card_html(ad), height=650, scrolling=False)
    else:
        render_empty_state("No public responses yet. Submit a form to start the conversation.")

# --- POLL DISPLAY ---
st.sidebar.subheader("Popular Retail Establishments (Poll)")
retail_poll_entries = build_retail_poll_entries(blog_data, poll_data)
if retail_poll_entries:
    st.sidebar.caption(f"{len(retail_poll_entries)} retail submissions with detailed poll data")
    with st.sidebar:
        components.html(
            build_poll_cards_html(retail_poll_entries),
            height=900,
            scrolling=True,
        )
else:
    with st.sidebar:
        render_empty_state("No poll data yet. Fill in the forms to see popular places!", sidebar=True)

# --- FOOTER ---
st.markdown(
    "<div class='sa-footer'>Developed by <strong>Thapelo Kgothatso Thooe</strong> &nbsp;|&nbsp; <a href='mailto:kgothatsothooe@gmail.com'>kgothatsothooe@gmail.com</a> &nbsp;|&nbsp; <a href='https://github.com/ybadk' target='_blank'>github.com/ybadk</a></div>",
    unsafe_allow_html=True,
)
