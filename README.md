# National Dialog SA

National Dialog SA is a Streamlit-based public feedback and community insight platform for collecting, displaying, and reviewing responses from users across South Africa.

The app combines business-oriented survey forms, a public blog-style response feed, advertising cards, and a sidebar poll experience into a single lightweight Python application.

Developed by **Thapelo Kgothatso Thooe**, a **Python developer from Pretoria, South Africa**.

## Overview

This project was built to gather structured feedback in a simple, visual format. Users can:

- register with their details before accessing the app
- complete multiple business and community-oriented forms
- submit retail, banking, public service, tourism, and customer behavior feedback
- view published responses in a blog-style public feed
- browse custom ad cards between public posts
- see detailed retail poll data in the sidebar
- access tourism links from custom-styled sidebar buttons

## Main features

### User access
- simple access form with validation for name, phone number, and email
- local storage of user access records in JSON and CSV format

### Business-oriented feedback forms
- Retail & Consumer Insights
- Public Service Delivery
- Customer Spending Behaviour
- Tourism & Hospitality Experience
- Banking & Financial Services

### Public blog feed
- every successful submission is saved and displayed in a public blog section
- blog posts use custom animated cards
- posts can include uploaded images or short videos

### Advertising support
- ad submission form for sponsored content
- image and video ads are rendered as custom horizontal cards
- ads are interleaved with blog content

### Sidebar poll
- detailed retail poll cards show full saved submission information
- supports legacy poll records and richer data from current submissions

### UI enhancements
- light Streamlit theme
- custom sidebar tourism buttons
- animated success notification cards after form submissions

## Tech stack

- Python
- Streamlit
- Pandas
- Local JSON / CSV storage
- Custom HTML/CSS components rendered inside Streamlit

## Project structure

```text
National_Dialog/
├── national_dialog_app.py
├── requirements.txt
├── README.md
├── .streamlit/config.toml
└── user_data_store/
```

## Data storage

The app stores data locally inside `user_data_store/`:

- `blog.json` — public form submissions
- `polls.json` — retail poll data
- `users.json` / `users.csv` — access/user records
- `media/` — uploaded blog and ad files

## Getting started

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd National_Dialog
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run national_dialog_app.py
```

## Usage notes

- the app is designed for local JSON-based persistence
- uploaded media is stored locally on disk
- sidebar poll cards are generated from retail submission data
- blog cards, ad cards, and notifications use embedded custom HTML/CSS

## Recommended future improvements

- move storage from JSON files to a database
- add admin moderation tools
- add analytics dashboards for form responses
- separate runtime user data from version-controlled sample data
- deploy the app to Streamlit Community Cloud or another hosting platform

## Developer credit

**Thapelo Kgothatso Thooe**  
Python Developer  
Pretoria, South Africa  
GitHub: [ybadk](https://github.com/ybadk)
