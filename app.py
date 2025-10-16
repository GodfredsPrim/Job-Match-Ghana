import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from geopy.distance import geodesic
from datetime import datetime
import os
import base64
import imghdr

# =========================
# CONFIG
# =========================
town_coords = {
    'Accra': (5.6037, -0.1870), 'Tamale': (9.4034, -0.8424), 'Madina': (5.6825, -0.1668),
    'Teshie': (5.5833, -0.1000), 'Kumasi': (6.6885, -1.6244), 'Zebilla': (10.9167, -0.5167),
    'Jasikan': (7.4167, 0.4333), 'Busunu': (9.1167, -1.9667), 'Langbinsi': (10.4000, -0.1333),
    'Amanten': (7.3167, -0.9167), 'Sui': (6.3167, -2.7167), 'Twifo Praso': (5.6167, -1.5500),
    'Wa': (10.0607, -2.5090), 'Dambai': (8.0667, 0.1833), 'Bole': (9.0333, -2.4833),
    'Tarkwa': (5.3038, -1.9897), 'Nobewam': (6.7667, -1.3167), 'Paga': (10.9833, -1.1167),
    'Worawora': (7.5000, 0.3833), 'Konongo': (6.6167, -1.2167), 'Nkawkaw': (6.5500, -0.7667),
    'Kpeve': (6.6833, 0.3167), 'Mim': (7.0500, -2.0167), 'Elmina': (5.0833, -1.3500),
    'Yendi': (9.4333, -0.0167), 'Prestea': (5.4333, -2.1500), 'Bawku': (11.0667, -0.2333)
}

nearby_regions = {
    'Greater Accra': ['Central', 'Volta', 'Eastern'], 'Ashanti': ['Brong-Ahafo', 'Eastern', 'Western'],
    'Northern': ['Upper East', 'Upper West', 'Brong-Ahafo'], 'Central': ['Greater Accra', 'Western', 'Eastern'],
    'Volta': ['Greater Accra', 'Eastern'], 'Eastern': ['Greater Accra', 'Ashanti', 'Central', 'Volta'],
    'Western': ['Central', 'Ashanti'], 'Brong-Ahafo': ['Ashanti', 'Northern', 'Western'],
    'Upper East': ['Northern', 'Upper West'], 'Upper West': ['Northern', 'Upper East'],
    'Oti': ['Volta', 'Northern'], 'Savannah': ['Northern', 'Upper West'], 'North East': ['Northern', 'Upper East'],
    'Bono': ['Brong-Ahafo', 'Ashanti'], 'Bono East': ['Brong-Ahafo', 'Ashanti'], 'Ahafo': ['Ashanti', 'Western'],
    'Western North': ['Western', 'Ashanti']
}

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    df = pd.read_csv('D:\\Daakye_Job_Match - Copy\\jobs_dataset_expanded_updated.csv')
    df['salary'] = df['salary'].replace(r'[₵,\s]', '', regex=True).fillna(0).astype(float)
    df['coords'] = df['town'].map(town_coords)
    return df

# =========================
# SCORING
# =========================
def score_job(job, user_prefs, user_location=None, user_town=None):
    score = 0
    if user_prefs['preferred_job_categories'] and 'Any' not in user_prefs['preferred_job_categories']:
        if job['job_title'].lower() in [cat.lower() for cat in user_prefs['preferred_job_categories']]:
            score += 40
    else:
        score += 40

    if user_prefs['skill_level'].lower() != 'no skill' and job['category'].lower() == user_prefs['skill_level'].lower():
        score += 30
    elif user_prefs['skill_level'].lower() == 'no skill':
        score += 30

    try:
        salary = float(job['salary'])
        if salary >= user_prefs['min_salary']:
            score += 20 * (salary / max(user_prefs['min_salary'], 1))
    except (ValueError, TypeError):
        pass

    selected_regions = [r.lower() for r in user_prefs['preferred_regions']]
    if job['region'].lower() in selected_regions:
        score += 10
    elif job['region'].lower() in [r.lower() for region in user_prefs['preferred_regions'] for r in nearby_regions.get(region, [])]:
        score += 5

    if user_town and job['town'].lower() == user_town.lower():
        score += 15  # Prioritize local jobs

    if user_location and job['coords'] is not None:
        try:
            distance = geodesic(user_location, job['coords']).km
            score += 10 * (1 - distance / 100) if distance < 100 else 0
        except:
            pass
    return score

# =========================
# MATCH JOBS
# =========================
def match_jobs(df, user_prefs, user_location=None, user_town=None):
    selected_regions = [r.lower() for r in user_prefs['preferred_regions']]
    allowed_regions = selected_regions.copy()
    for region in user_prefs['preferred_regions']:
        if region in nearby_regions:
            allowed_regions.extend([r.lower() for r in nearby_regions[region] if r.lower() not in allowed_regions])

    df = df[df['region'].str.lower().isin(allowed_regions)]
    if user_prefs['preferred_job_categories'] and 'Any' not in user_prefs['preferred_job_categories']:
        cats = [c.lower() for c in user_prefs['preferred_job_categories']]
        df = df[df['job_title'].str.lower().isin(cats)]

    df['score'] = df.apply(lambda x: score_job(x, user_prefs, user_location, user_town), axis=1)
    return df[df['score'] > 0].sort_values(by='score', ascending=False)

# =========================
# PDF GENERATOR
# =========================
def generate_pdf_report(name, age, skill_level, matched_jobs, user_prefs):
    pdf_filename = f"Daakye_Job_Match_Report_{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    logo_path = r"D:\Daakye_Job_Match - Copy\daakye.png"
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(logo, 50, 750, width=100, height=50, preserveAspectRatio=True)

    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0, 0.42, 0.25)  # Green (#006B3F)
    c.drawString(200, 760, "Daakye Job Match Report")
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0, 0)
    y = 710
    c.drawString(50, y, f"Name: {name}"); y -= 20
    c.drawString(50, y, f"Age: {age}"); y -= 20
    c.drawString(50, y, f"Skill Level: {skill_level}"); y -= 20
    c.drawString(50, y, f"Preferred Regions: {', '.join(user_prefs['preferred_regions'])}"); y -= 20
    c.drawString(50, y, f"Min Salary: ₵{user_prefs['min_salary']:.2f}"); y -= 20
    c.drawString(50, y, "Mission: Empowering Ghanaian youth with sustainable jobs to reduce illegal mining."); y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0.42, 0.25)
    c.drawString(50, y, "Matched Jobs"); y -= 20
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0, 0, 0)
    if matched_jobs.empty:
        c.drawString(50, y, "No jobs matched your criteria.")
    else:
        for _, job in matched_jobs.head(5).iterrows():
            c.setFillColorRGB(0.96, 0.76, 0.07)  # Gold (#F5C211)
            c.drawString(50, y, f"{job['job_title']} - {job['company']}"); y -= 20
            c.setFillColorRGB(0, 0, 0)
            c.drawString(50, y, f"{job['town']}, {job['region']} | ₵{job['salary']:.2f}"); y -= 20
            c.drawString(50, y, f"Contact: {job['contact_person']} ({job['phone_number']})"); y -= 30
            if y < 80:
                c.showPage(); y = 750; c.setFont("Helvetica", 12); c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColorRGB(0.78, 0.06, 0.18)  # Red (#C8102E)
    c.drawString(50, 30, "Powered by Daakye Job Match - Connecting Ghanaians to Opportunities")
    c.save()
    return pdf_filename

# =========================
# SLIDESHOW
# =========================
def get_slideshow_images(folder=r"D:\Daakye_Job_Match - Copy\slides", limit=5):
    imgs = []
    if not os.path.exists(folder):
        st.sidebar.warning(f"Slides folder not found: {os.path.abspath(folder)}")
        return imgs
    files = sorted([f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))])
    max_limit = min(len(files), 16)  # Cap at 16 images
    limit = min(limit, max_limit)  # Respect user-selected limit
    files = files[:limit]
    for f in files:
        path = os.path.join(folder, f)
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
                mime = f"image/{imghdr.what(None, h=raw) or 'jpeg'}"
                b64 = base64.b64encode(raw).decode()
                imgs.append((b64, mime, f))
        except Exception as e:
            st.sidebar.warning(f"Failed to load {f}: {e}")
    return imgs

def inject_slideshow(images):
    if not images:
        return
    total_duration = len(images) * 8
    slides_html = "".join(
        f"<div class='slide'></div>"
        for _ in images
    )
    css = f"""
    <style>
    .stApp {{ background: transparent; min-height: 100vh; }}
    .slideshow {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        overflow: hidden;
    }}
    .slide {{
        position: absolute;
        width: 100%;
        height: 100%;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        opacity: 0;
        will-change: opacity;
        animation: fade {total_duration}s infinite;
        animation-fill-mode: forwards;
    }}
    {"".join(f".slide:nth-child({i+1}) {{ background-image: linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.35)), url(data:{mime};base64,{b64}); animation-delay: {i*8}s; }}" for i, (b64, mime, _) in enumerate(images))}
    @keyframes fade {{
        0% {{ opacity: 0; }}
        5% {{ opacity: 1; }}
        20% {{ opacity: 1; }}
        25% {{ opacity: 0; }}
        100% {{ opacity: 0; }}
    }}
    .main .block-container {{
        position: relative;
        z-index: 10;
        background: rgba(255,255,255,0.92);
        border-radius: 10px;
        padding: 2rem;
        max-width: 900px;
        margin: 2rem auto;
        border: 2px solid #006B3F;
        min-height: 500px;
    }}
    h1 {{
        color: #FFFFFF;
        -webkit-text-stroke: 0.8px #000000;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        text-align: center;
        font-family: 'Roboto', sans-serif;
    }}
    h2, label, .stMarkdown p {{
        color: #FFFFFF;
        -webkit-text-stroke: 0.5px #000000;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }}
    .stButton>button {{
        background-color: #006B3F;
        color: #FFFFFF;
        border-radius: 5px;
        border: 2px solid #F5C211;
    }}
    .stButton>button:hover {{
        background-color: #C8102E;
        color: #FFFFFF;
    }}
    .stTextInput>div>input, .stNumberInput>div>input, .stSelectbox>div>select, .stMultiSelect>div>select {{
        background-color: #FFFFFF;
        border: 1px solid #006B3F;
        border-radius: 5px;
        color: #000000;
    }}
    </style>
    <div class="slideshow">{slides_html}</div>
    """
    st.markdown("".join(f"<img src='data:{mime};base64,{b64}' style='display:none;' />" for b64, mime, _ in images), unsafe_allow_html=True)
    st.markdown(css, unsafe_allow_html=True)

# =========================
# MAIN APP
# =========================
def main():
    st.set_page_config(page_title="Daakye Job Match", layout="centered")

    # Sidebar settings
    st.sidebar.title("Daakye Job Match Settings")
    slideshow_enabled = st.sidebar.checkbox("Enable Background Slideshow", value=True)
    slide_limit = st.sidebar.slider("Number of Slideshow Images", min_value=1, max_value=16, value=5, step=1)

    # Load slideshow images
    slides = []
    if slideshow_enabled:
        slides = get_slideshow_images(r"D:\Daakye_Job_Match - Copy\slides", limit=slide_limit)
        if slides:
            inject_slideshow(slides)
        else:
            st.markdown("""
            <style>
            .stApp { background-color: #FFFFFF; min-height: 100vh; }
            .main .block-container {
                position: relative;
                z-index: 10;
                background: rgba(255,255,255,0.92);
                border-radius: 10px;
                padding: 2rem;
                max-width: 900px;
                margin: 2rem auto;
                border: 2px solid #006B3F;
                min-height: 500px;
            }
            h1 {
                color: #006B3F;
                text-align: center;
                font-family: 'Roboto', sans-serif;
            }
            h2, label, .stMarkdown p {
                color: #000000;
            }
            .stButton>button {
                background-color: #006B3F;
                color: #FFFFFF;
                border-radius: 5px;
                border: 2px solid #F5C211;
            }
            .stButton>button:hover {
                background-color: #C8102E;
                color: #FFFFFF;
            }
            .stTextInput>div>input, .stNumberInput>div>input, .stSelectbox>div>select, .stMultiSelect>div>select {
                background-color: #FFFFFF;
                border: 1px solid #006B3F;
                border-radius: 5px;
                color: #000000;
            }
            </style>
            """, unsafe_allow_html=True)

    logo_path = r"D:\Daakye_Job_Match - Copy\daakye.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=150)
    else:
        st.warning("Logo file 'daakye.png' not found in D:\\Daakye_Job_Match - Copy\\")

    st.title("Daakye Job Match")
    st.write("Find job opportunities tailored to your skills and preferences in Ghana.")
    st.markdown("**Our Mission**: Empowering Ghanaian youth with sustainable job opportunities to reduce illegal mining and build better futures.")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=16, max_value=100, step=1)
        skill = st.selectbox("Skill Level", ["Basic", "Skilled", "Professional", "No Skill"])
    with col2:
        df = load_data()
        regions = st.multiselect("Preferred Regions", sorted(df['region'].unique()), default=["Greater Accra"])
        min_salary = st.number_input("Minimum Salary (₵)", min_value=0, step=100)

    categories = st.multiselect("Preferred Job Categories", sorted(df['job_title'].unique()), default=["Farmhand", "Science Teacher", "Electrician"])
    town = st.text_input("Your Town (optional)")

    if st.button("Find Jobs"):
        if name and age and regions and categories:
            prefs = {
                'skill_level': skill,
                'preferred_regions': regions,
                'min_salary': min_salary,
                'preferred_job_categories': categories
            }
            location = town_coords.get(town, None) if town else None
            matched = match_jobs(df, prefs, location, town)
            st.subheader("Matched Jobs")
            if matched.empty:
                st.info("No jobs matched your criteria.")
            else:
                st.dataframe(matched[['job_title', 'region', 'town', 'salary', 'company', 'phone_number', 'score']])
                pdf = generate_pdf_report(name, age, skill, matched, prefs)
                with open(pdf, "rb") as f:
                    st.download_button("Download Job Match Report", f, file_name=pdf, mime="application/pdf")
        else:
            st.error("Please fill in all required fields!")

    # Add upskilling resources
    st.sidebar.subheader("Upskilling Resources")
    st.sidebar.markdown("[Ghana Youth Employment Agency](https://www.yea.gov.gh/)")
    st.sidebar.markdown("[National Vocational Training Institute](https://www.nvtighana.org/)")
    st.sidebar.markdown("[University of Ghana Career Services](https://www.ug.edu.gh/careerservices/)")
    st.sidebar.markdown("[Kumasi Technical University Job Portal](https://www.ktu.edu.gh/)")

if __name__ == "__main__":
    main()