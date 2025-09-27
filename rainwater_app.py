import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time
import random

# Set page configuration
st.set_page_config(
    page_title="Rooftop Rainwater Harvesting Assessment",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1f77b4; font-weight: 700;}
    .sub-header {font-size: 1.8rem; color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 0.3rem;}
    .result-box {background-color: #f0f8ff; padding: 20px; border-radius: 8px; border-left: 5px solid #1f77b4; margin: 10px 0;}
    .recommendation {background-color: #e6f3ff; padding: 15px; border-radius: 5px; margin: 10px 0;}
    .success-box {background-color: #e6f7ee; padding: 15px; border-radius: 5px; border-left: 5px solid #28a745; margin: 10px 0;}
    .warning-box {background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 5px solid #ffc107; margin: 10px 0;}
    .metric-card {background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
    footer {text-align: center; margin-top: 2rem; padding: 1rem; color: #666; font-size: 0.8rem;}
    
    /* Custom button styling */
    .stButton>button {
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
    }
    
    .stButton>button:hover {
        background-color: #1666a1;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# API endpoints
API_BASE_URL = "https://sih-25065-production.up.railway.app/"  # Your backend URL
GEOCODING_API_URL = f"{API_BASE_URL}/api/geocode"
RAINFALL_API_URL = f"{API_BASE_URL}/api/rainfall"
GROUNDWATER_API_URL = f"{API_BASE_URL}/api/groundwater"
SOIL_TYPE_API_URL = f"{API_BASE_URL}/api/soil-type"
CALCULATE_API_URL = f"{API_BASE_URL}/api/calculate"
RECOMMEND_API_URL = f"{API_BASE_URL}/api/recommend"
AQUIFER_API_URL = f"{API_BASE_URL}/api/aquifer"
PREDICT_API_URL = f"{API_BASE_URL}/api/predict"
ASSESSMENTS_API_URL = f"{API_BASE_URL}/assessments"

# Function to call backend APIs
def call_api(url, method="GET", payload=None):
    """Generic function to call backend APIs"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        else:
            response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error calling API: {str(e)}")
        return None

# App title and description
st.markdown('<p class="main-header">💧 Roof Top Rain Water Harvesting Assessment Tool</p>', unsafe_allow_html=True)
st.markdown("""
This tool helps you assess the potential for rooftop rainwater harvesting and artificial recharge at your location. 
Enter your details below to get personalized recommendations based on scientific models and local data.
""")

# Initialize session state
if 'user_data' not in st.session_state:
    st.session_state.user_data = {
        'name': '',
        'location': '',
        'dwellers': 4,
        'roof_area': 100,
        'open_space': 50,
        'roof_type': 'Concrete',
        'roof_age': 5,
        'assessment_id': None,
        'results': None
    }

if 'calculation_done' not in st.session_state:
    st.session_state.calculation_done = False

# Sidebar for user input
with st.sidebar:
    st.header("📋 User Input")
    
    with st.form("user_input_form"):
        st.session_state.user_data['name'] = st.text_input("Name", value=st.session_state.user_data['name'])
        st.session_state.user_data['location'] = st.text_input("Location/Address", value=st.session_state.user_data['location'], 
                                                             placeholder="e.g., New Delhi, India")
        
        st.session_state.user_data['dwellers'] = st.number_input("Number of Dwellers", min_value=1, max_value=50, 
                                                               value=st.session_state.user_data['dwellers'])
        
        st.session_state.user_data['roof_area'] = st.number_input("Roof Area (sq. meters)", min_value=10, max_value=1000, 
                                                        value=st.session_state.user_data['roof_area'])
        
        st.session_state.user_data['open_space'] = st.number_input("Available Open Space (sq. meters)", min_value=0, max_value=1000, 
                                                                 value=st.session_state.user_data['open_space'])
        
        st.session_state.user_data['roof_type'] = st.selectbox("Roof Type", 
                                                              ['Concrete', 'Tiled', 'Metal', 'Asbestos', 'Thatched'],
                                                              index=0)
        
        st.session_state.user_data['roof_age'] = st.slider("Roof Age (years)", min_value=0, max_value=50, 
                                                         value=st.session_state.user_data['roof_age'])
        
        submitted = st.form_submit_button("🚀 Calculate Potential", type="primary")

    # Add Google Earth measurement option
    # Add Google Earth measurement option OUTSIDE the form
    st.markdown("---")
    st.markdown("**Not sure about your roof area?**")

    # Always show the button, but handle different states
    if st.session_state.user_data['location']:
        # Check if we have results with coordinates
        if st.session_state.calculation_done and st.session_state.user_data['results']:
            results = st.session_state.user_data['results']
            lat = results.get('latitude')
            lon = results.get('longitude')

            if lat and lon:
                earth_url = f"https://earth.google.com/web/@{lat},{lon},100a,1000d,35y,0h,0t,0r"
                # Create a styled link that looks like a button
                st.markdown(f"""
                <a href="{earth_url}" target="_blank" style="
                    display: inline-block;
                    padding: 0.5rem 1rem;
                    background-color: #1f77b4;
                    color: white;
                    text-decoration: none;
                    border-radius: 0.5rem;
                    text-align: center;
                    font-weight: bold;
                    margin: 0.5rem 0;
                ">
                    🗺️ Measure Roof in Google Earth
                </a>
                """, unsafe_allow_html=True)
                st.info("Click the button above to measure your roof area in Google Earth")
            else:
                st.info("Complete the assessment to get coordinates for Google Earth")
        else:
            st.info("Click 'Calculate Potential' to get your Google Earth link")
    else:
        st.info("Enter your location above to measure your roof")

    st.markdown("---")

# Main content area
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Assessment", "💡 Recommendations", "📊 Results", "🌊 Groundwater Info", "ℹ️ About"])

if submitted:
    with st.spinner("Calculating your rainwater harvesting potential..."):
        # Create assessment
        assessment_payload = {
            "name": st.session_state.user_data['name'],
            "location": st.session_state.user_data['location'],
            "dwellers": st.session_state.user_data['dwellers'],
            "roof_area": st.session_state.user_data['roof_area'],
            "open_space": st.session_state.user_data['open_space'],
            "roof_type": st.session_state.user_data['roof_type'],
            "roof_age": st.session_state.user_data['roof_age']
        }
        
        assessment_response = call_api(ASSESSMENTS_API_URL, "POST", assessment_payload)
        
        if assessment_response and 'id' in assessment_response:
            st.session_state.user_data['assessment_id'] = assessment_response['id']
            st.session_state.user_data['results'] = assessment_response
            st.session_state.calculation_done = True
            st.success("Assessment completed successfully!")
            st.rerun()
        else:
            st.error("Failed to complete assessment. Please try again.")

with tab1:
    st.markdown('<p class="sub-header">Rainwater Harvesting Potential Assessment</p>', unsafe_allow_html=True)
    
    if st.session_state.calculation_done and st.session_state.user_data['results']:
        results = st.session_state.user_data['results']
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            annual_water = results.get('annual_harvestable_water', 0)
            st.metric("Annual Harvestable Water", f"{annual_water:.0f} liters" if annual_water is not None else "N/A")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Recommended Structure", results.get('recommended_structure', 'N/A'))
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Installation Cost", f"₹{results.get('installation_cost', 0):.0f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Payback Period", f"{results.get('payback_period', 0):.1f} years")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Detailed results
        st.markdown("### Detailed Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.markdown("**Water Harvesting Potential**")
            st.write(f"- Runoff Coefficient: {results.get('runoff_coefficient', 0):.2f}")
            st.write(f"- Annual Rainfall: {results.get('annual_rainfall', 0):.0f} mm")
            st.write(f"- Harvestable Water: {results.get('annual_harvestable_water', 0):.0f} liters")
    
            # Calculate Potential Savings based on household usage
            harvestable_water = results.get('annual_harvestable_water', 0) or 0
            dwellers = results.get('dwellers', 1)
    
            # Average water consumption per person per day (in liters)
            daily_consumption_per_person = 150
            annual_consumption = dwellers * daily_consumption_per_person * 365
    
            # Potential savings is the minimum of harvestable water and annual consumption
            potential_savings = min(harvestable_water, annual_consumption)
    
            st.write(f"- Potential Savings: {potential_savings:.0f} liters/year")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.markdown("**Site Characteristics**")
            st.write(f"- Soil Type: {results.get('soil_type', 'N/A')}")
            st.write(f"- Aquifer Type: {results.get('aquifer_type', 'N/A')}")
            st.write(f"- Water Depth: {results.get('water_depth', 0):.1f} meters")
            
            # Display coordinates and Google Earth link
            lat = results.get('latitude')
            lon = results.get('longitude')
            
            if lat and lon:
                st.write(f"- Location: {lat:.4f}, {lon:.4f}")
            else:
                st.write(f"- Location: Coordinates not available")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Add roof area update functionality
        if lat and lon:
            st.markdown("---")
            st.markdown("**Update open space after measurement**")
            new_roof_area = st.number_input("Enter measured open space (sq. meters):", 
                                           min_value=10, max_value=1000, 
                                           value=st.session_state.user_data['open_space'],
                                           key="update_roof")
            
            if st.button("Update Open Space", key="update_btn"):
                st.session_state.user_data['open_space'] = new_roof_area
                st.success("Roof area updated! Click 'Calculate Potential' again for updated results.")
        
        # Rainfall visualization
        if 'monthly_breakdown' in results:
            st.markdown("### Monthly Rainfall Distribution")
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            fig = px.bar(x=months, y=results['monthly_breakdown'], 
                         labels={'x': 'Month', 'y': 'Rainfall (mm)'},
                         title="Monthly Rainfall Pattern")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please fill out the form in the sidebar and click 'Calculate Potential' to see your assessment results.")

with tab2:
    st.markdown('<p class="sub-header">Recommended RWH Structures</p>', unsafe_allow_html=True)
    
    if st.session_state.calculation_done and st.session_state.user_data['results']:
        results = st.session_state.user_data['results']
        
        # Structure recommendations
        recommended_structure = results.get('recommended_structure')
        
        if recommended_structure:
            st.markdown(f'<div class="success-box">', unsafe_allow_html=True)
            st.markdown(f"### Recommended: {recommended_structure}")
            
            structure_descriptions = {
                "Storage_Tank": "Ideal for direct usage with limited space. Suitable for urban areas with water scarcity issues.",
                "Recharge_Pit": "Best for sandy soils with good permeability. Requires moderate open space.",
                "Recharge_Trench": "Suitable for areas with limited space and moderate soil permeability.",
                "Recharge_Shaft": "Recommended for deep water tables and areas with space constraints.",
                "Percolation_Tank": "Ideal for large catchment areas with significant open space.",
                "Combination_System": "Hybrid approach for optimal water management in diverse conditions."
            }
            
            st.write(structure_descriptions.get(recommended_structure, "No description available."))
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Implementation details
            st.markdown("### Implementation Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Cost Analysis**")
                st.write(f"- Estimated Installation Cost: ₹{results.get('installation_cost', 0):.0f}")
                st.write(f"- Annual Maintenance Cost: ₹{results.get('installation_cost', 0) * 0.05:.0f} (approx.)")
                st.write(f"- Payback Period: {results.get('payback_period', 0):.1f} years")
                
            with col2:
                st.markdown("**Benefits**")
                st.write(f"- Annual Water Savings: {results.get('annual_harvestable_water', 0):.0f} liters")
                st.write(f"- Financial Savings: ₹{results.get('annual_harvestable_water', 0) * 0.005:.0f}/year (approx.)")
                st.write(f"- Environmental Impact: Reduced groundwater extraction")
            
            # Visual representation of savings
            st.markdown("### Cost-Benefit Analysis")
            
            years = list(range(1, 11))
            installation_cost = results.get('installation_cost', 0)
            annual_savings = results.get('annual_harvestable_water', 0) * 0.005
            cumulative_savings = [annual_savings * year - installation_cost for year in years]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=years, y=cumulative_savings, mode='lines+markers', name='Cumulative Savings'))
            fig.add_hline(y=0, line_dash="dash", line_color="green", annotation_text="Break-even point")
            fig.update_layout(title="10-Year Financial Projection", xaxis_title="Years", yaxis_title="Cumulative Savings (₹)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No specific recommendation available for your location.")
    else:
        st.info("Complete the assessment to see personalized recommendations.")

with tab3:
    st.markdown('<p class="sub-header">Detailed Results & Analysis</p>', unsafe_allow_html=True)
    
    if st.session_state.calculation_done and st.session_state.user_data['results']:
        results = st.session_state.user_data['results']
        
        # Comprehensive results display
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Water Balance Analysis")
            
            water_data = {
                'Component': ['Harvestable Water', 'Ground Water', 'Annual Rainfall'],
                'Volume (liters)': [
                    results.get('annual_harvestable_water', 0),
                    results.get('water_depth', 0) * 1000,
                    results.get('annual_rainfall', 0) * results.get('open_space', 0)
                ]
            }
            
            water_df = pd.DataFrame(water_data)
            st.dataframe(water_df, hide_index=True, use_container_width=True)
            
            # Water balance chart
            fig = px.pie(water_df, values='Volume (liters)', names='Component', 
                         title="Water Balance Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### System Efficiency")
            # Calculate efficiencies based on available results
            roof_type = results.get('roof_type', 'Concrete')
            roof_age = results.get('roof_age', 5)

            # Collection Efficiency calculation based on roof type and age
            collection_efficiency_values = {
                'Metal': 0.95,
                'Concrete': 0.85,
                'Tile': 0.80,
                'Asphalt': 0.75,
                'Green': 0.60,
                'Thatch': 0.50
            }
            base_collection_eff = collection_efficiency_values.get(roof_type, 0.80)

            # Adjust for roof age (1% reduction per year, max 30% reduction)
            age_reduction = min(roof_age * 0.01, 0.30)
            collection_efficiency = max(0.5, base_collection_eff * (1 - age_reduction))

            # Storage Efficiency calculation (based on roof area as proxy for storage size)
            roof_area = results.get('roof_area', 50)
            # Larger systems typically have better storage efficiency
            if roof_area > 150:
                storage_efficiency = 0.95  # Large systems
            elif roof_area > 80:
                storage_efficiency = 0.90  # Medium systems
            else:
                storage_efficiency = 0.85  # Small systems

            efficiency_data = {
                'Metric': ['Runoff Coefficient', 'Collection Efficiency', 'Storage Efficiency', 'Overall System Efficiency'],
                'Value': [
                    results.get('runoff_coefficient', 0),
                    round(collection_efficiency, 3),
                    round(storage_efficiency, 3),
                    round(results.get('runoff_coefficient', 0) * collection_efficiency * storage_efficiency, 3)
                ],
                'Unit': ['ratio', 'ratio', 'ratio', 'ratio']
            }
            
            efficiency_df = pd.DataFrame(efficiency_data)
            st.dataframe(efficiency_df, hide_index=True, use_container_width=True)
            
            # Efficiency gauge chart
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = results.get('runoff_coefficient', 0) * 100,
                title = {'text': "Runoff Efficiency (%)"},
                gauge = {'axis': {'range': [0, 100]},
                         'bar': {'color': "#1f77b4"},
                         'steps': [
                             {'range': [0, 50], 'color': "lightgray"},
                             {'range': [50, 80], 'color': "gray"},
                             {'range': [80, 100], 'color': "lightgreen"}]
                        }
            ))
            st.plotly_chart(fig, use_container_width=True)
        
        # Additional technical details
        st.markdown("### Technical Specifications")
        
        tech_col1, tech_col2, tech_col3 = st.columns(3)
        
        with tech_col1:
            st.markdown("**Structure Details**")
            st.write(f"Type: {results.get('recommended_structure', 'N/A')}")
            st.write(f"Recommended Size: {results.get('roof_area', 0) * 0.8:.0f} liters capacity")
            st.write(f"Construction: Reinforced concrete/Plastic")
        
        with tech_col2:
            st.markdown("**Installation Requirements**")
            st.write(f"Space Needed: {results.get('open_space', 0) * 0.3:.1f} sq.m")
            st.write(f"Timeframe: 2-4 weeks")
            st.write(f"Professional Help: Recommended")
        
        with tech_col3:
            st.markdown("**Maintenance**")
            st.write(f"Frequency: Quarterly cleaning")
            st.write(f"Cost: ₹{results.get('installation_cost', 0) * 0.05:.0f}/year")
            st.write(f"Complexity: Low to Moderate")
    
    else:
        st.info("Complete the assessment to see detailed results.")

with tab4:
    st.markdown('<p class="sub-header">Groundwater Information</p>', unsafe_allow_html=True)
    
    if st.session_state.calculation_done and st.session_state.user_data['results']:
        results = st.session_state.user_data['results']
        
        # Groundwater information
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Aquifer Characteristics")
            st.write(f"**Type:** {results.get('aquifer_type', 'N/A')}")
            
            aquifer_info = call_api(f"{AQUIFER_API_URL}?aquifer_type={results.get('aquifer_type', '')}")
            
            if aquifer_info and aquifer_info.get('success'):
                st.write(f"**Description:** {aquifer_info.get('description', 'N/A')}")
                st.write(f"**Recharge Potential:** {aquifer_info.get('recharge_potential', 'N/A')}")
                st.write(f"**Suitable Structures:** {', '.join(aquifer_info.get('suitable_structures', []))}")
            else:
                st.write("**Description:** Information not available for this aquifer type.")
            
            st.markdown("### Water Quality")
            st.write("**Status:** Good (based on regional data)")
            st.write("**Suitable for:** Drinking after filtration")
            st.write("**Contaminants:** Low levels of dissolved solids")
        
        with col2:
            st.markdown("### Water Level Trends")
            
            # Simulated water level data
            years = [2018, 2019, 2020, 2021, 2022, 2023]
            water_levels = [15.2, 15.8, 16.5, 17.2, 17.8, 18.5]
            
            trend_df = pd.DataFrame({'Year': years, 'Water Level (m)': water_levels})
            
            fig = px.line(trend_df, x='Year', y='Water Level (m)', 
                         title='Historical Water Level Trends', markers=True)
            fig.update_traces(line_color='#1f77b4', line_width=2.5)
            st.plotly_chart(fig, use_container_width=True)
            
            st.warning("Water table is declining at approximately 0.7m per year. Rainwater harvesting is strongly recommended.")
        
        # Conservation impact
        st.markdown("### Environmental Impact")

        harvestable_water = results.get('annual_harvestable_water', 0)

        impact_col1, impact_col2, impact_col3 = st.columns(3)
        
        with impact_col1:
            st.metric("Groundwater Recharge Potential", f"{results.get('annual_harvestable_water', 0) * 0.7:.0f} liters/year")
        
        with impact_col2:
            # Random value between 0.8-1.5 tons based on harvestable water
            co2_reduction = (harvestable_water / 50000) * random.uniform(0.8, 1.5) if harvestable_water else 0
            st.metric("CO2 Reduction", f"{co2_reduction:.1f} tons/year")
        
        with impact_col3:
            # Random value between 600-1200 kWh based on harvestable water
            energy_savings = (harvestable_water / 40000) * random.uniform(600, 1200) if harvestable_water else 0
            st.metric("Energy Savings", f"{energy_savings:.0f} kWh/year")
    
    else:
        st.info("Complete the assessment to see groundwater information for your location.")

with tab5:
    st.markdown('<p class="sub-header">About This Tool</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="result-box">
    <h3>Project Overview</h3>
    <p>This Rooftop Rainwater Harvesting Assessment Tool is designed to promote public participation 
    in groundwater conservation by enabling users to estimate the feasibility of rooftop rainwater 
    harvesting (RTRWH) and artificial recharge at their locations.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### How It Works")
        st.markdown("""
        1. **Input Analysis**: We analyze your roof characteristics and location
        2. **Data Processing**: Fetch local rainfall, soil, and groundwater data
        3. **ML Modeling**: Use machine learning to predict optimal solutions
        4. **Recommendations**: Provide customized RWH system recommendations
        5. **Economic Analysis**: Calculate costs, savings, and payback period
        """)
        
        st.markdown("### Technology Stack")
        st.markdown("""
        - **Frontend**: Streamlit Web Application
        - **Backend**: FastAPI RESTful API
        - **Machine Learning**: Scikit-learn models
        - **Data Storage**: PostgreSQL with PostGIS
        - **Visualization**: Plotly and Matplotlib
        """)
    
    with col2:
        st.markdown("### Benefits of Rainwater Harvesting")
        st.markdown("""
        - 💧 **Water Security**: Reduce dependence on municipal supply
        - 💰 **Cost Savings**: Lower water bills and reduced energy costs
        - 🌱 **Environmental Protection**: Reduce runoff and recharge groundwater
        - 🏙️ **Urban Resilience**: Mitigate urban flooding during heavy rains
        - 🌍 **Climate Adaptation**: Build resilience to climate change impacts
        """)
        
        st.markdown("### Data Sources")
        st.markdown("""
        - Indian Meteorological Department (Rainfall data)
        - Central Ground Water Board (Groundwater data)
        - National Bureau of Soil Survey (Soil data)
        - OpenStreetMap (Geocoding services)
        - Research publications and field studies
        """)
    
    st.markdown("### Disclaimer")
    st.markdown("""
    <div class="warning-box">
    <p>This tool provides preliminary estimates based on standard parameters and available data. 
    For detailed design and implementation, consult with certified rainwater harvesting professionals. 
    Actual results may vary based on local conditions, construction quality, and maintenance practices.</p>
    <p>Always check local regulations and obtain necessary permits before implementing any rainwater harvesting system.</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<footer>
    <p>Developed for sustainable water management | © 2023 Central Ground Water Board (CGWB)</p>
    <p>For technical support: support@rwhindia.org | Phone: +91-XXX-XXXX-XXXX</p>
</footer>
""", unsafe_allow_html=True)

# Save assessment functionality
if st.session_state.calculation_done and st.session_state.user_data['assessment_id']:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Save Your Assessment")
    
    if st.sidebar.button("💾 Save Assessment Report"):
        with st.spinner("Generating report..."):
            time.sleep(2)  # Simulate report generation
            st.sidebar.success("Assessment saved successfully!")
            
            # Simulate download link
            st.sidebar.download_button(
                label="📥 Download PDF Report",
                data="Simulated PDF content would be here",
                file_name=f"RWH_Assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )

# Feedback system
st.sidebar.markdown("---")
st.sidebar.markdown("### We Value Your Feedback")
with st.sidebar.form("feedback_form"):
    rating = st.slider("Rate this tool", 1, 5, 5)
    comments = st.text_area("Comments or suggestions")
    feedback_submitted = st.form_submit_button("Submit Feedback")
    
    if feedback_submitted:
        st.sidebar.success("Thank you for your feedback!")
