import pandas as pd
import random
import os

# Ensure the output directory exists
output_dir = r"D:\Daakye_Job_Match - Copy"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Define regions and small towns/districts
regions = [
    'Greater Accra', 'Ashanti', 'Central', 'Eastern', 'Volta', 'Western', 'Northern', 'Upper East',
    'Upper West', 'Oti', 'Savannah', 'North East', 'Bono', 'Bono East', 'Ahafo', 'Western North'
]
small_towns = {
    'Greater Accra': [('Adenta', 'Adenta District'), ('Dansoman', 'Ablekuma West District'), ('Teshie', 'Ledzokuku District'), ('Madina', 'La Nkwantanang District')],
    'Ashanti': [('Konongo', 'Asante Akim Central District'), ('Fomena', 'Adansi North District'), ('Juaso', 'Asante Akim South District'), ('Obuasi', 'Obuasi Municipal')],
    'Central': [('Twifo Praso', 'Twifo Atti-Morkwa District'), ('Swedru', 'Agona West District'), ('Elmina', 'KEEA District'), ('Cape Coast', 'Cape Coast Metro')],
    'Eastern': [('Nkawkaw', 'Kwahu West District'), ('Akim Oda', 'Birim Central District'), ('Nsawam', 'Nsawam Adoagyiri District'), ('Kade', 'Kwaebibirem District')],
    'Volta': [('Ho', 'Ho Municipal'), ('Kpando', 'Kpando District'), ('Kpeve', 'South Dayi District'), ('Anloga', 'Anloga District')],
    'Western': [('Tarkwa', 'Tarkwa Nsuaem District'), ('Prestea', 'Prestea-Huni Valley District'), ('Axim', 'Nzema East District'), ('Bogoso', 'Prestea-Huni Valley District')],
    'Northern': [('Tamale', 'Tamale Metro'), ('Yendi', 'Yendi Municipal'), ('Bimbilla', 'Nanumba North District'), ('Gushegu', 'Gushegu District')],
    'Upper East': [('Zebilla', 'Bawku West District'), ('Paga', 'Kassena Nankana West District'), ('Bawku', 'Bawku Municipal'), ('Navrongo', 'Kassena Nankana East District')],
    'Upper West': [('Wa', 'Wa Municipal'), ('Jirapa', 'Jirapa District'), ('Lambussie', 'Lambussie District'), ('Nandom', 'Nandom District')],
    'Oti': [('Jasikan', 'Jasikan District'), ('Dambai', 'Krachi East District'), ('Worawora', 'Biakoye District'), ('Nkwanta', 'Nkwanta South District')],
    'Savannah': [('Busunu', 'West Gonja District'), ('Bole', 'Bole District'), ('Sawla', 'Sawla-Tuna-Kalba District'), ('Damongo', 'West Gonja District')],
    'North East': [('Langbinsi', 'East Mamprusi District'), ('Nalerigu', 'North East District'), ('Chereponi', 'Chereponi District'), ('Gambaga', 'East Mamprusi District')],
    'Bono': [('Mim', 'Asunafo North District'), ('Dormaa', 'Dormaa West District'), ('Wamfie', 'Dormaa East District'), ('Sunyani', 'Sunyani Municipal')],
    'Bono East': [('Amanten', 'Atebubu-Amanten District'), ('Kwame Danso', 'Sene West District'), ('Busunya', 'Nkoranza North District'), ('Kintampo', 'Kintampo North District')],
    'Ahafo': [('Goaso', 'Asunafo North District'), ('Nobewam', 'Asutifi North District'), ('Kukuom', 'Asutifi South District'), ('Hwidiem', 'Asutifi South District')],
    'Western North': [('Sui', 'Sui District'), ('Bibiani', 'Bibiani-Anhwiaso-Bekwai District'), ('Enchi', 'Aowin District'), ('Dadieso', 'Suaman District')],
}

# Expanded job titles by category
basic_jobs = [
    'Farmhand', 'Market Porter', 'Laborer', 'Street Vendor', 'Cleaner', 'Cook Assistant', 'Security Guard', 'Loader', 
    'Janitor', 'Construction Helper', 'Okada Rider', 'Mobile Money Agent', 'Petty Trader', 'Fishmonger', 'Charcoal Seller',
    'Water Vendor', 'Reforestation Worker', 'Waste Collector', 'Delivery Boy/Girl', 'Market Assistant'
]
skilled_jobs = [
    'Carpenter', 'Plumber', 'Painter', 'Tailor', 'Hairdresser', 'Barber', 'Driver', 'Auto Mechanic', 'Welder', 'Electrician',
    'Mason', 'Solar Technician', 'Refrigeration Technician', 'Caterer', 'Graphic Designer', 'Drone Operator', 
    'Phone Repair Technician', 'Bead Maker', 'Batik Maker', 'Mechanized Farming Operator'
]
professional_jobs = [
    'Science Teacher', 'Community Nurse', 'Civil Engineer', 'ICT Trainer', 'Agricultural Extension Officer', 'Accountant', 
    'English Teacher', 'Health Assistant', 'Environmental Officer', 'Business Analyst', 'Software Developer', 
    'Data Analyst', 'Renewable Energy Engineer', 'Project Manager', 'Logistics Coordinator', 'Public Health Specialist',
    'Rural Development Planner', 'Financial Advisor', 'Marketing Specialist', 'Agricultural Economist'
]

# Expanded companies and contacts
companies = [
    'Zebilla Community School', 'Jasikan Health Clinic', 'Tarkwa Infrastructure Co', 'Amanten Fashion Co-op', 
    'Sui Youth Tech Hub', 'Twifo Praso Agro Co-op', 'Wa Rural Garage', 'Dambai Community Bank', 
    'Nobewam Construction Works', 'Paga Eco-Tourism Group', 'Ahafo Youth Empowerment NGO', 
    'Busunu Rural Electrification', 'Konongo Skill Academy', 'Worawora Farmers Union', 'Bawku Tech Solutions',
    'Prestea Sustainable Farms', 'Nkawkaw Vocational Training', 'Elmina Community Works', 'Yendi Rural Development',
    'Kpeve Women’s Co-op', 'Tamale Digital Hub', 'Axim Fisheries Co-op', 'Bole Renewable Energy Ltd', 
    'Nkwanta Market Ventures', 'Sawla Microfinance Group'
]
names = [
    'Kofi Amoah', 'Akosua Mensah', 'Yaw Osei', 'Adwoa Boateng', 'Kwame Asante', 'Ama Nkrumah', 'Owusu Kwarteng', 
    'Abena Gyamfi', 'Esi Darko', 'Ama Boateng', 'Kojo Mensah', 'Efua Agyeman', 'Kwesi Appiah', 'Afua Osei', 
    'Yaw Boateng', 'Nana Adjei', 'Akua Owusu', 'Kwadwo Antwi', 'Maame Serwaa', 'Kwabena Yeboah'
]

# Generate 600 rows
rows = []
mining_regions = ['Western', 'Ashanti', 'Ahafo', 'Eastern', 'Central']  # 40% in mining-affected regions
for i in range(600):
    # Prioritize mining regions for 40% of jobs
    if i < 240:  # 40% of 600
        region = random.choice(mining_regions)
    else:
        region = random.choice(regions)
    town, district = random.choice(small_towns.get(region, [('Unknown', 'Unknown District')]))
    # Ensure 70% in small towns (avoid urban centers like Accra, Kumasi for 70%)
    if random.random() < 0.3 and region in ['Greater Accra', 'Ashanti']:
        town, district = random.choice([('Accra', 'Accra Metro'), ('Kumasi', 'Kumasi Metro')])
    # Category distribution: 50% Basic, 30% Skilled, 20% Professional
    category = random.choice(['Basic'] * 50 + ['Skilled'] * 30 + ['Professional'] * 20)
    job_title = (random.choice(basic_jobs) if category == 'Basic' else
                 random.choice(skilled_jobs) if category == 'Skilled' else
                 random.choice(professional_jobs))
    # Salaries based on category and Ghana’s 2023–2025 rural/urban scales
    salary = round(random.uniform(800, 6000) if category == 'Basic' else
                   random.uniform(4000, 12000) if category == 'Skilled' else
                   random.uniform(8000, 25000), 0)
    company = random.choice(companies)
    contact_person = random.choice(names)
    phone_number = f"02{random.randint(10000000, 99999999)}"
    description = (f"{job_title} role in {town}. {'Entry-level job for youth, no experience needed' if category == 'Basic' else
                   'Skilled role for vocational graduates' if category == 'Skilled' else
                   'Professional role for university/college graduates'}. Supports rural development and provides sustainable alternatives to illegal mining. {'Training provided' if category == 'Basic' else 'Apply your skills to make a community impact'}.")
    rows.append([job_title, category, region, district, town, salary, company, contact_person, phone_number, description])

# Create DataFrame and save
df = pd.DataFrame(rows, columns=['job_title', 'category', 'region', 'district', 'town', 'salary', 'company', 'contact_person', 'phone_number', 'description'])
output_path = os.path.join(output_dir, 'jobs_dataset_expanded_updated.csv')
df.to_csv(output_path, index=False)
print(f"Generated 600-row dataset saved to '{output_path}'")