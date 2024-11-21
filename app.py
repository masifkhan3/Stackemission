import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

class EmissionsCalculator:
    def __init__(self):
        self.steam_ranges = {
            'low': (0, 10),      
            'medium': (11, 50),  
            'high': (51, 150)    
        }

        self.factors = {
            'coal': {
                'low': {'oxygen': 2, 'carbon_dioxide': 0.5, 'carbon_monoxide': 90, 'sulphur_dioxide': 180, 'nitrogen_dioxide': 12, 'nitrogen_oxide': 20, 'nox': 130, 'particulate_matter': 50},
                'medium': {'oxygen': 0.4, 'carbon_dioxide': 0.1, 'carbon_monoxide': 17, 'sulphur_dioxide': 35, 'nitrogen_dioxide': 3, 'nitrogen_oxide': 5, 'nox': 25, 'particulate_matter': 11},
                'high': {'oxygen': 0.13, 'carbon_dioxide': 0.035, 'carbon_monoxide': 7, 'sulphur_dioxide': 13, 'nitrogen_dioxide': 20, 'nitrogen_oxide': 25, 'nox': 10, 'particulate_matter': 4}
            },
            'biomass': {
                'low': {'oxygen': 0.5, 'carbon_dioxide': 3, 'carbon_monoxide': 85, 'sulphur_dioxide': 180, 'nitrogen_dioxide': 12, 'nitrogen_oxide': 25, 'nox': 125, 'particulate_matter': 55},
                'medium': {'oxygen': 0.36, 'carbon_dioxide': 0.08, 'carbon_monoxide': 17, 'sulphur_dioxide': 35, 'nitrogen_dioxide': 2.4, 'nitrogen_oxide': 5, 'nox': 25, 'particulate_matter': 11},
                'high': {'oxygen': 0.13, 'carbon_dioxide': 0.026, 'carbon_monoxide': 5.6, 'sulphur_dioxide': 11, 'nitrogen_dioxide': 0.8, 'nitrogen_oxide': 1.47, 'nox': 8.35, 'particulate_matter': 3.65}
            }
        }

        self.peqs_limits = {
            'carbon_monoxide': 800,      
            'sulphur_dioxide': 1700,     
            'nox': 1200,                 
            'particulate_matter': 500    
        }

    def get_load_range(self, steam_load):
        for range_name, (min_load, max_load) in self.steam_ranges.items():
            if min_load <= steam_load <= max_load:
                return range_name
        return 'high'

    def calculate_emissions(self, steam_load, fuel_type, fuel_mix=None):
        load_range = self.get_load_range(steam_load)

        if fuel_type == 'mixed' and fuel_mix:
            coal_emissions = {param: value * (fuel_mix['coal'] / 100) for param, value in self.factors['coal'][load_range].items()}
            biomass_emissions = {param: value * (fuel_mix['biomass'] / 100) for param, value in self.factors['biomass'][load_range].items()}
            emissions = {param: coal_emissions[param] + biomass_emissions[param] for param in coal_emissions.keys()}
        else:
            emissions = self.factors[fuel_type][load_range].copy()

        _, range_max = self.steam_ranges[load_range]
        load_factor = steam_load / range_max
        for param in emissions:
            emissions[param] *= load_factor * steam_load

        return emissions, load_range

    def compare_with_peqs(self, emissions):
        comparison = []
        for parameter, limit in self.peqs_limits.items():
            calculated = emissions[parameter]
            status = "Compliant" if calculated <= limit else "Exceeded"
            percentage = (calculated / limit) * 100
            comparison.append({
                'Parameter': parameter.replace('_', ' ').title(),
                'Value (mg/nm³)': round(calculated, 2),
                'PEQS Limit (mg/nm³)': limit,
                'Percentage of Limit': f"{percentage:.1f}%",
                'Status': status
            })

        return pd.DataFrame(comparison)

def main():
    st.title("Emissions Calculator")
    st.sidebar.header("Input Parameters")

    steam_load = st.sidebar.number_input("Steam Load (TPH)", min_value=0.1, max_value=300.0, step=0.1)
    fuel_type = st.sidebar.selectbox("Fuel Type", ["coal", "biomass", "mixed"])

    fuel_mix = None
    if fuel_type == "mixed":
        coal_percent = st.sidebar.slider("Coal Percentage (%)", 0, 100, 50)
        biomass_percent = 100 - coal_percent
        fuel_mix = {"coal": coal_percent, "biomass": biomass_percent}

    calculator = EmissionsCalculator()

    if st.sidebar.button("Calculate Emissions"):
        emissions, load_range = calculator.calculate_emissions(steam_load, fuel_type, fuel_mix)
        st.subheader("Results")
        st.write(f"Steam Load: {steam_load:.2f} TPH")
        st.write(f"Load Range: {load_range.title()}")
        st.write(f"Fuel Type: {fuel_type.title()}")
        if fuel_type == "mixed":
            st.write(f"Fuel Mix: {fuel_mix['coal']}% Coal, {fuel_mix['biomass']}% Biomass")

        emissions_df = pd.DataFrame(list(emissions.items()), columns=["Parameter", "Value (mg/nm³)"])
        st.write("Emissions:", emissions_df)

        comparison_df = calculator.compare_with_peqs(emissions)
        st.write("Compliance with PEQS Limits:", comparison_df)

        fig, ax = plt.subplots()
        comparison_df.plot.bar(x="Parameter", y=["Value (mg/nm³)", "PEQS Limit (mg/nm³)"], ax=ax)
        st.pyplot(fig)

if __name__ == "__main__":
    main()
