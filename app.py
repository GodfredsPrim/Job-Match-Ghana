import streamlit as st
import pandas as pd
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
except ModuleNotFoundError:
    st.error("Error: 'reportlab' module not installed. Please ensure it is included in requirements.txt.")
    st.stop()
from geopy.distance import geodesic
from datetime import datetime
import os
import base64
from PIL import Image
import io

# Town coordinates for distance-based job matching (example subset, expand as needed)
town_coords = {
    "Zebilla": (10.9167, -0.5167), "Jasikan": (7.4092, 0.4433), "Tarkwa": (5.3038, -1.9896),
    "Busunu": (9.3167, -1.9333), "Nobewam": (6.7167, -1.4167), "Amanten": (7.6833, -0.6333),
    "Twifo Praso": (5.6167, -1.5667), "Sui": (5.9333, -2.3167), "Wa": (10.0607, -2.5099),
    "Dambai": (8.0667, 0.1833)
}

# Nearby regions for regional job matching
nearby_regions = {
    "Upper East": ["Northern", "North East"], "Oti": ["Volta", "Bono East"],
    "Western": ["Western North", "Central"], "Savannah": ["Northern", "North East"],
    "Ahafo": ["Bono", "Ashanti"], "Bono East": ["Oti", "Bono"], "Central": ["Western", "Eastern"],
    "Western North": ["Western", "Ahafo"]
}

@st.cache_data
def load_data():
    dataset_path = 'jobs_dataset_expanded_updated.csv'
    if not os.path.exists(dataset_path):
        st.error(f"Dataset file not found at: {dataset_path}")
        st.stop()
    try:
        df = pd.read_csv(dataset_path, usecols=['job_title', 'category', 'region', 'district', 'town', 'salary', 'company', 'phone_number', 'description'])
        df['salary'] = df['salary'].replace(r'[₵,\s]', '', regex=True).fillna(0).astype(float)
        df['coords'] = df['town'].map(town_coords)
        return df
    except Exception as e:
        st.error(f"Error loading dataset: {str(e)}")
        st.stop()

def get_slideshow_images(folder="slides", limit=10):
    imgs = []
    if not os.path.exists(folder):
        st.sidebar.warning(f"Slides folder not found: {os.path.abspath(folder)}")
        return imgs
    files = sorted([f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png"))])
    max_limit = min(len(files), 10)  # Cap at 10 images
    limit = min(limit, max_limit)
    files = files[:limit]
    for f in files:
        path = os.path.join(folder, f)
        try:
            # Use Pillow to detect image format
            with Image.open(path) as img:
                format = img.format.lower()  # e.g., 'jpeg', 'png'
                mime = f"image/{format if format in ['jpeg', 'png'] else 'jpeg'}"
            with open(path, "rb") as fh:
                raw = fh.read()
                b64 = base64.b64encode(raw).decode()
                imgs.append((b64, mime, f))
        except Exception as e:
            st.sidebar.warning(f"Failed to load {f}: {e}")
    return imgs

def match_jobs(df, user_skill, user_regions, min_salary, user_categories, user_town):
    filtered_df = df[df['category'].isin([user_skill] if user_skill != "Any" else df['category'].unique())]
    if user_regions:
        region_mask = df['region'].isin(user_regions) | df['region'].isin(sum([nearby_regions.get(r, []) for r in user_regions], []))
        filtered_df = filtered_df[region_mask]
    if min_salary:
        filtered_df = filtered_df[filtered_df['salary'] >= min_salary]
    if user_categories:
        filtered_df = filtered_df[filtered_df['job_title'].isin(user_categories)]
    
    filtered_df = filtered_df.copy()
    filtered_df['score'] = 0
    if user_town and user_town in town_coords and filtered_df['coords'].notna().any():
        filtered_df.loc[filtered_df['town'] == user_town, 'score'] += 15
        user_coords = town_coords[user_town]
        filtered_df['distance'] = filtered_df['coords'].apply(
            lambda x: geodesic(user_coords, x).kilometers if pd.notna(x) else float('inf')
        )
        filtered_df['score'] += filtered_df['distance'].apply(lambda x: max(0, 10 - x / 10))
    
    return filtered_df.sort_values(by=['score', 'salary'], ascending=[False, False]).drop(columns=['coords', 'score'] + (['distance'] if 'distance' in filtered_df.columns else []))

def generate_pdf(user_info, matched_jobs):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0, 0.42, 0.25)  # Green #006B3F
    c.drawString(100, 750, "Daakye Job Match Report")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(100, 730, f"Generated for: {user_info['name']}")
    c.drawString(100, 710, f"Date: {user_info['date']}")
    c.setFillColorRGB(1, 0.07, 0.18)  # Red #C8102E
    c.drawString(100, 50, "Daakye Job Match - Connecting Ghanaian Youth to Opportunities")
    c.setFillColorRGB(0, 0, 0)
    c.drawString(100, 690, "Mission: Empowering Ghanaian youth with sustainable job opportunities to reduce illegal mining and build better futures.")
    
    y = 670
    c.setFillColorRGB(0.96, 0.76, 0.07)  # Gold #F5C211
    c.drawString(100, y, "Matched Jobs:")
    y -= 20
    c.setFillColorRGB(0, 0, 0)
    for _, job in matched_jobs.head(10).iterrows():
        c.drawString(100, y, f"{job['job_title']} - {job['company']} ({job['town']}, {job['region']})")
        c.drawString(100, y - 15, f"Salary: ₵{job['salary']:,.0f} | Contact: {job['phone_number']}")
        c.drawString(100, y - 30, f"Description: {job['description'][:100]}...")
        y -= 50
        if y < 100:
            c.showPage()
            y = 750
    
    c.save()
    buffer.seek(0)
    return buffer

def main():
    st.set_page_config(page_title="Daakye Job Match", page_icon="daakye.png", layout="wide")
    
    # Load logo
    if os.path.exists("daakye.png"):
        st.image("daakye.png", width=150)
    else:
        st.warning("Logo file 'daakye.png' not found!")
    
    # Mission statement
    st.markdown(
        """
        <div style='background-color: rgba(255, 255, 255, 0.7); padding: 10px; border: 2px solid #006B3F; border-radius: 5px;'>
            <h2 style='color: white; text-shadow: 1px 1px 2px black, 0 0 25px black, 0 0 5px black;'>
                Welcome to Daakye Job Match
            </h2>
            <p style='color: white; text-shadow: 1px 1px 2px black;'>
                Empowering Ghanaian youth with sustainable job opportunities to reduce illegal mining and build better futures.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Slideshow
    slideshow_images = get_slideshow_images()
    if slideshow_images:
        slide_index = st.session_state.get("slide_index", 0)
        interval = st.sidebar.slider("Slideshow interval (seconds)", min_value=5, max_value=20, value=8, step=1) * 1000
        placeholder = st.empty()
        with placeholder.container():
            b64, mime, fname = slideshow_images[slide_index % len(slideshow_images)]
            st.image(f"data:{mime};base64,{b64}", caption=fname, use_column_width=True)
        st.markdown(
            f"""
            <script>
                setInterval(function() {{
                    fetch('/_stcore/streamlit_internal/button_click?button_id=next_slide').then(() => {{
                        window.location.reload();
                    }});
                }}, {interval});
            </script>
            """,
            unsafe_allow_html=True
        )
        if st.button("Next Slide", key="next_slide"):
            st.session_state.slide_index = (slide_index + 1) % len(slideshow_images)
    
    # Sidebar for upskilling resources
    st.sidebar.title("Upskilling Resources")
    st.sidebar.markdown("""
        - [Ghana Youth Employment Agency](https://www.yea.gov.gh/)
        - [NVTI](https://www.nvti.gov.gh/)
        - [University of Ghana Job Portal](https://www.ug.edu.gh/careers)
        - [KNUST Career Services](https://www.knust.edu.gh/students/career-services)
    """)
    
    # User input form
    st.header("Find Your Job")
    with st.form("job_form"):
        name = st.text_input("Full Name")
        age = st.number_input("Age", min_value=16, max_value=35, value=25)
        skill_level = st.selectbox("Skill Level", ["No Skill", "Skilled", "Professional", "Any"])
        regions = st.multiselect("Preferred Regions", [
            'Greater Accra', 'Ashanti', 'Central', 'Eastern', 'Volta', 'Western', 'Northern', 
            'Upper East', 'Upper West', 'Oti', 'Savannah', 'North East', 'Bono', 'Bono East', 
            'Ahafo', 'Western North'
        ])
        min_salary = st.number_input("Minimum Salary (₵)", min_value=0, value=0)
        job_categories = st.multiselect("Job Categories", [
            'Okada Rider', 'Mobile Money Agent', 'Farmhand', 'Waste Collector', 'Solar Technician', 
            'Bead Maker', 'Electrician', 'Software Developer', 'Renewable Energy Engineer', 
            'Data Analyst', 'Science Teacher', 'Community Nurse'
        ])
        town = st.text_input("Preferred Town (Optional)")
        submitted = st.form_submit_button("Find Jobs")
    
    if submitted and name and age:
        df = load_data()
        matched_jobs = match_jobs(df, skill_level, regions, min_salary, job_categories, town)
        if not matched_jobs.empty:
            st.write("### Matched Jobs")
            st.dataframe(matched_jobs)
            pdf_buffer = generate_pdf({"name": name, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, matched_jobs)
            st.download_button(
                label="Download Job Report",
                data=pdf_buffer,
                file_name=f"Daakye_Job_Match_Report_{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("No jobs found matching your criteria.")
    elif submitted:
        st.error("Please enter your name and age.")

if __name__ == "__main__":
    main()
