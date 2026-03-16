import base64
import json
import mimetypes
import os
import re
import time
from datetime import datetime
from html import escape
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


def is_valid_sa_phone(phone):
    # Accepts 0[6-8]XXXXXXXX or +27[6-8]XXXXXXXX
    return bool(re.fullmatch(r"(0[6-8][0-9]{8}|\+27[6-8][0-9]{8})", phone))


def is_valid_email(email):
    # Simple email regex
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


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


def render_ad_card(ad):
    with st.container(border=True):
        st.caption("Sponsored")
        st.markdown(f"#### {ad['title']}")
        render_saved_media(ad.get("media"), caption=ad["title"])
        if ad.get("description"):
            st.write(ad["description"])
        if ad.get("link"):
            st.markdown(f"[Visit advertiser]({ad['link']})")
        st.caption(f"Posted by {ad.get('author', 'Community member')} • {ad['timestamp']}")


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
    fallback_media = """
    <div class="card-image-container">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="video-icon">
        <path d="M464 384.39a32 32 0 01-13-2.77 15.77 15.77 0 01-2.71-1.54l-82.71-58.22A32 32 0 01352 295.7v-79.4a32 32 0 0113.58-26.16l82.71-58.22a15.77 15.77 0 012.71-1.54 32 32 0 0145 29.24v192.76a32 32 0 01-32 32zM268 400H84a68.07 68.07 0 01-68-68V180a68.07 68.07 0 0168-68h184.48A67.6 67.6 0 01336 179.52V332a68.07 68.07 0 01-68 68z"></path>
      </svg>
    </div>
    """
    action_icon = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" class="play-icon">
      <path d="M73 39c-14.8-9.1-33.4-9.4-48.5-.9S0 62.6 0 80V432c0 17.4 9.4 33.4 24.5 41.9s33.7 8.1 48.5-.9L361 297c14.3-8.7 23-24.2 23-41s-8.7-32.2-23-41L73 39z"></path>
    </svg>
    """

    for ad in reversed(ads):
        media_kind, media_uri = get_media_data_uri(ad.get("media"))
        if media_uri and media_kind == "video":
            media_markup = (
                f'<div class="card-image-container"><video class="card-media" '
                f'controls muted playsinline preload="metadata" src="{media_uri}"></video></div>'
            )
        elif media_uri:
            media_markup = (
                f'<div class="card-image-container"><img class="card-media" '
                f'src="{media_uri}" alt="{escape(ad.get("title", "Ad"))}"></div>'
            )
        else:
            media_markup = fallback_media

        action_text = "Visit Advertiser" if ad.get("link") else "Sponsored Ad"
        button_tag = "a" if ad.get("link") else "div"
        link_attrs = ""
        if ad.get("link"):
            safe_link = escape(ad["link"], quote=True)
            link_attrs = f' href="{safe_link}" target="_blank" rel="noopener noreferrer"'

        cards.append(
            f'''
            <div class="card">
              {media_markup}
              <p class="card-title">{escape(ad.get("title", "Sponsored Ad"))}</p>
              <p class="card-des">{escape(ad.get("description", "Community promotion"))}</p>
              <{button_tag} class="card-btn"{link_attrs}>
                {action_icon}
                <span class="card-btn-text">{action_text}</span>
              </{button_tag}>
            </div>
            '''
        )

    return f'''
    <html>
      <body>
        <div class="ad-scroll-wrap">{"".join(cards)}</div>
      </body>
      <style>
        body {{
          margin: 0;
          padding: 0;
          font-family: Arial, sans-serif;
          background: transparent;
        }}

        .ad-scroll-wrap {{
          display: flex;
          gap: 16px;
          overflow-x: auto;
          padding: 8px 6px 16px;
          scroll-behavior: smooth;
        }}

        .card {{
          display: flex;
          flex-direction: column;
          flex: 0 0 250px;
          min-height: 315px;
          background-color: #ffffff;
          border-radius: 10px;
          box-shadow: 0px 10px 12px rgba(0, 0, 0, 0.08),
            -4px -4px 12px rgba(0, 0, 0, 0.08);
          overflow: hidden;
          transition: all 0.3s;
          cursor: pointer;
          box-sizing: border-box;
          padding: 10px;
        }}

        .card:hover {{
          transform: translateY(-10px);
          box-shadow: 0px 20px 20px rgba(0, 0, 0, 0.1),
            -4px -4px 12px rgba(0, 0, 0, 0.08);
        }}

        .card-image-container {{
          width: 100%;
          height: 180px;
          border-radius: 10px;
          margin-bottom: 12px;
          overflow: hidden;
          background-color: rgb(165, 165, 165);
          display: flex;
          align-items: center;
          justify-content: center;
        }}

        .card-media {{
          width: 100%;
          height: 100%;
          object-fit: cover;
        }}

        .video-icon {{
          width: 40px;
          height: 40px;
          color: #ffffff;
        }}

        .card-title {{
          margin: 0 0 6px;
          font-size: 17px;
          font-weight: 600;
          color: #1797b8;
          overflow: hidden;
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 1;
          line-clamp: 1;
        }}

        .card-des {{
          margin: 0;
          min-height: 34px;
          font-size: 13px;
          color: #1797b8;
          overflow: hidden;
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 2;
          line-clamp: 2;
        }}

        .card-btn {{
          margin-top: auto;
          text-decoration: none;
          font-size: 15px;
          color: #fff;
          display: flex;
          justify-content: center;
          align-items: center;
          background-color: #12bde7;
          width: 34px;
          height: 34px;
          border-radius: 10px;
          overflow: hidden;
          transition: all ease-in-out 0.5s;
          gap: 1px;
          box-sizing: border-box;
          padding-left: 6px;
        }}

        .card-btn:hover {{
          width: 100%;
          gap: 10px;
          padding: 0;
        }}

        .play-icon {{
          width: 14px;
          height: 14px;
          fill: currentColor;
        }}

        .card-btn-text {{
          opacity: 0;
          font-size: 1px;
          font-weight: 500;
          transition: all ease-in-out 0.5s;
          white-space: nowrap;
        }}

        .card-btn:hover > .card-btn-text {{
          opacity: 1;
          font-size: 14px;
        }}
      </style>
    </html>
    '''


def build_blog_post_card_html(entry):
    user = entry.get("user", {})
    form_name = escape(str(entry.get("form", "Community Response")))
    timestamp = escape(str(entry.get("timestamp", "")))
    name = escape(str(user.get("name", "Community member")))
    email = escape(str(user.get("email", "No email provided")))
    phone = escape(str(user.get("phone", "No phone provided")))

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
                f'<li><span class="label">{safe_key}</span><span class="value">{safe_value}</span></li>'
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
              background: #ffffff;
              width: 100%;
              box-sizing: border-box;
              transition: all 0.48s cubic-bezier(0.23, 1, 0.32, 1);
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
              color: #0a3cff;
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
              padding: 10px 12px;
              border-radius: 14px;
              background: #f8fafc;
            }}

            .label {{
              font-size: 11px;
              font-weight: 700;
              color: #0a3cff;
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
              background: #f8fafc;
              border-radius: 16px;
              padding: 14px;
            }}

            .media-label {{
              margin: 0 0 10px;
              color: #0a3cff;
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
              background: linear-gradient(to right, #0a3cff, #0a3cff);
              transform-origin: center;
              animation: moving 4.8s linear infinite paused;
              transition: all 0.88s cubic-bezier(0.23, 1, 0.32, 1);
            }}

            .card:hover::before {{
              animation-play-state: running;
              width: 20%;
            }}

            .card:hover {{
              box-shadow: 0rem 6px 13px rgba(10, 60, 255, 0.1),
                0rem 24px 24px rgba(10, 60, 255, 0.09),
                0rem 55px 33px rgba(10, 60, 255, 0.05),
                0rem 97px 39px rgba(10, 60, 255, 0.01),
                0rem 152px 43px rgba(10, 60, 255, 0);
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
    for link in links:
        buttons.append(
            f'''
            <a class="sidebar-link" href="{escape(link["url"], quote=True)}" target="_blank" rel="noopener noreferrer">
              <button>{escape(link["label"])}</button>
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

        button {{
          background-color: #eee;
          border: none;
          padding: 1rem;
          font-size: 1rem;
          width: 100%;
          border-radius: 1rem;
          color: lightcoral;
          box-shadow: 0 0.4rem #dfd9d9;
          cursor: pointer;
        }}

        button:active {{
          color: white;
          box-shadow: 0 0.2rem #dfd9d9;
          transform: translateY(0.2rem);
        }}

        button:hover {{
          background: lightcoral;
          color: white;
          text-shadow: 0 0.1rem #bcb4b4;
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

    if isinstance(entry, str):
        store_name = format_store_name(entry, "Unknown Store")
        return {
            "store": store_name,
            "province": "Unknown Province",
            "city": "Unknown City",
            "town": "Unknown Town",
            "age": "Unknown Age",
            "satisfaction": "Not provided",
            "decision_driver": "Not provided",
            "suggestion": "Not provided",
            "submitted_at": "Unknown Date",
        }

    if not isinstance(entry, dict):
        return None

    age_value = entry.get("age")
    if age_value in (None, ""):
        age_text = "Unknown Age"
    else:
        age_text = str(age_value)

    return {
        "store": format_store_name(entry.get("store"), "Unknown Store"),
        "province": format_location(entry.get("province"), "Unknown Province"),
        "city": format_location(entry.get("city"), "Unknown City"),
        "town": format_location(entry.get("town"), "Unknown Town"),
        "age": age_text,
        "satisfaction": clean_text(entry.get("satisfaction"), "Not provided"),
        "decision_driver": clean_text(entry.get("decision_driver"), "Not provided"),
        "suggestion": clean_text(entry.get("suggestion"), "Not provided"),
        "submitted_at": clean_text(entry.get("submitted_at") or entry.get("timestamp"), "Unknown Date"),
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

    for blog_entry in blog_entries:
        responses = blog_entry.get("responses", {})
        store_value = get_first_response_value(responses, store_keys)
        if store_value is None:
            continue

        normalized = normalize_poll_entry(
            {
                "store": store_value,
                "age": responses.get("Age"),
                "province": responses.get("Province"),
                "city": responses.get("City"),
                "town": responses.get("Town"),
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
            normalized["province"].lower(),
            normalized["city"].lower(),
            normalized["town"].lower(),
        )
        if signature not in detailed_signatures:
            detailed_entries.append(normalized)

    return list(reversed(detailed_entries))


def build_poll_cards_html(rows):
    icons = [
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="rgba(149,149,255,1)" d="M17 15.245v6.872a.5.5 0 0 1-.757.429L12 20l-4.243 2.546a.5.5 0 0 1-.757-.43v-6.87a8 8 0 1 1 10 0zm-8 1.173v3.05l3-1.8 3 1.8v-3.05A7.978 7.978 0 0 1 12 17a7.978 7.978 0 0 1-3-.582zM12 15a6 6 0 1 0 0-12 6 6 0 0 0 0 12z"></path></svg>',
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M16 16c1.657 0 3 1.343 3 3s-1.343 3-3 3-3-1.343-3-3 1.343-3 3-3zM6 12c2.21 0 4 1.79 4 4s-1.79 4-4 4-4-1.79-4-4 1.79-4 4-4zm10 6c-.552 0-1 .448-1 1s.448 1 1 1 1-.448 1-1-.448-1-1-1zM6 14c-1.105 0-2 .895-2 2s.895 2 2 2 2-.895 2-2-.895-2-2-2zm8.5-12C17.538 2 20 4.462 20 7.5S17.538 13 14.5 13 9 10.538 9 7.5 11.462 2 14.5 2zm0 2C12.567 4 11 5.567 11 7.5s1.567 3.5 3.5 3.5S18 9.433 18 7.5 16.433 4 14.5 4z" fill="rgba(252,161,71,1)"></path></svg>',
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="rgba(66,193,110,1)" d="M20.083 15.2l1.202.721a.5.5 0 0 1 0 .858l-8.77 5.262a1 1 0 0 1-1.03 0l-8.77-5.262a.5.5 0 0 1 0-.858l1.202-.721L12 20.05l8.083-4.85zm0-4.7l1.202.721a.5.5 0 0 1 0 .858L12 17.65l-9.285-5.571a.5.5 0 0 1 0-.858l1.202-.721L12 15.35l8.083-4.85zm-7.569-9.191l8.771 5.262a.5.5 0 0 1 0 .858L12 13 2.715 7.429a.5.5 0 0 1 0-.858l8.77-5.262a1 1 0 0 1 1.03 0zM12 3.332L5.887 7 12 10.668 18.113 7 12 3.332z"></path></svg>',
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="rgba(220,91,183,1)" d="M12 20h8v2h-8C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10a9.956 9.956 0 0 1-2 6h-2.708A8 8 0 1 0 12 20zm0-10a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm-4 4a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm8 0a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm-4 4a2 2 0 1 1 0-4 2 2 0 0 1 0 4z"></path></svg>',
    ]

    items = []
    for idx, row in enumerate(rows):
        theme_index = (idx % 4) + 1
        items.append(
            f'''
            <div class="item item--{theme_index}">
              {icons[idx % len(icons)]}
              <span class="quantity">{escape(row["store"])}</span>
              <span class="text text--{theme_index}">Age: {escape(str(row["age"]))}</span>
              <span class="meta"><strong>Province:</strong> {escape(row["province"])}</span>
              <span class="meta"><strong>City:</strong> {escape(row["city"])}</span>
              <span class="meta"><strong>Town:</strong> {escape(row["town"])}</span>
              <span class="meta"><strong>Service rating:</strong> {escape(row["satisfaction"])}</span>
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
          border-radius: 12px;
          width: 100%;
          min-height: 210px;
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          justify-content: flex-start;
          text-align: left;
          padding: 14px 12px;
          box-sizing: border-box;
        }}

        .item:hover {{
          transform: scale(0.98);
          transition: all 0.3s;
        }}

        .item svg {{
          width: 34px;
          height: 34px;
          margin-bottom: 8px;
        }}

        .item--1 {{ background: #c7c7ff; }}
        .item--2 {{ background: #ffd8be; }}
        .item--3 {{ background: #a9ecbf; }}
        .item--4 {{ background: #f3bbe1; }}

        .quantity {{
          font-size: 20px;
          font-weight: 700;
          line-height: 1.3;
          word-break: break-word;
        }}

        .text {{
          font-size: 13px;
          font-weight: 700;
          margin-top: 4px;
        }}

        .text--1 {{ color: rgba(149,149,255,1); }}
        .text--2 {{ color: rgba(252,161,71,1); }}
        .text--3 {{ color: rgba(66,193,110,1); }}
        .text--4 {{ color: rgba(220,91,183,1); }}

        .meta {{
          font-size: 11px;
          line-height: 1.45;
          color: #334155;
          margin-top: 4px;
          overflow-wrap: anywhere;
        }}

        .meta strong {{
          color: #0f172a;
        }}
      </style>
    </html>
    '''


def show_transition_loader(title, message):
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
      background: #004643;
      border-radius: 50px;
      overflow: hidden;
    }

    .inner_loader {
      width: 60%;
      height: 100%;
      background: #f9bc60;
      border-radius: 50px;
      animation: moveLeftRight 3s ease-in-out infinite;
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

    time.sleep(1)


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
        background: radial-gradient(circle, rgba(63, 94, 251, 1) 0%, rgba(252, 70, 223, 1) 100%);
        border: 1px solid #e8e8e8;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-end;
        box-sizing: border-box;
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
        color: #fff;
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
    }
]

# --- POLL DATA ---
poll_data = load_json_list(POLL_PATH)

# --- ADS DATA ---
ads_data = load_json_list(ADS_PATH)

# --- MAIN UI ---
st.title("National Dialog: South Africa")
st.caption("A national platform to understand public preferences, retail habits, and service experiences across South Africa.")

# --- AD SPACE ---
st.markdown("---")
st.subheader("Ad Space")
ad_form_col, ad_preview_col = st.columns([1, 2])

with ad_form_col:
    st.caption("Create a small ad that can appear between public blog posts.")
    with st.form("ad_submission_form"):
        ad_title = st.text_input("Ad title")
        ad_description = st.text_area("Short ad description", max_chars=240)
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
        if ad_link and not ad_link.startswith(("http://", "https://")):
            ad_errors.append("Website link must start with http:// or https://")

        if ad_errors:
            for error in ad_errors:
                st.error(error)
        else:
            ad_entry = {
                "title": ad_title.strip(),
                "description": ad_description.strip(),
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
            st.rerun()

with ad_preview_col:
    st.caption("Current ad cards")
    if ads_data:
        components.html(build_ad_showcase_html(ads_data), height=380, scrolling=False)
        st.caption("Scroll sideways to browse image and video ads.")
    else:
        st.info("No ads yet. Use the form to publish the first ad.")

st.markdown("---")

# --- FORMS (Cyclable Cards) ---
form_tab = st.tabs([f"Form {i+1}: {f['title']}" for i, f in enumerate(FORM_QUESTIONS)])
for idx, (tab, form) in enumerate(zip(form_tab, FORM_QUESTIONS)):
    with tab:
        with st.form(f"form_{idx}"):
            responses = {}
            # New demographic fields
            age = st.number_input("Your Age", min_value=10, max_value=120, key=f"age_{idx}")
            province = st.text_input("Province", key=f"province_{idx}")
            city = st.text_input("City", key=f"city_{idx}")
            town = st.text_input("Town", key=f"town_{idx}")
            responses["Age"] = age
            responses["Province"] = province
            responses["City"] = city
            responses["Town"] = town
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
                    "province": province,
                    "city": city,
                    "town": town,
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
            st.rerun()

# --- BLOG DISPLAY ---
st.markdown("---")
st.subheader("Public Blog: Responses from Across South Africa")
recent_blog_entries = list(reversed(blog_data[-20:]))

if recent_blog_entries:
    for idx, entry in enumerate(recent_blog_entries):
        blog_card_html, blog_card_height = build_blog_post_card_html(entry)
        components.html(blog_card_html, height=blog_card_height, scrolling=False)

        if ads_data and idx < len(recent_blog_entries) - 1 and idx % 2 == 0:
            ad_index = (idx // 2) % len(ads_data)
            render_ad_card(ads_data[ad_index])
else:
    st.info("No public responses yet. Submit a form to start the conversation.")

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
    st.sidebar.info("No poll data yet. Fill in the forms to see popular places!")

# --- FOOTER ---
st.markdown("<center>Developed by Thapelo Kgothatso Thooe | kgothatsothooe@gmail.com | github.com/ybadk</center>", unsafe_allow_html=True)
