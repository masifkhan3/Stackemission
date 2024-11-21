import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from IPython.display import display

class EmissionsCalculator:
    def __init__(self):
        # Steam capacity ranges
        self.steam_ranges = {
            'low': (0, 10),      # 0-10 TPH
            'medium': (11, 50),  # 11-50 TPH
            'high': (51, 150)    # 51-150 TPH
        }

        # Emission factors by fuel type and load range
        self.factors = {
            'coal': {
        'low': {
            'oxygen': 2,                   # %
            'carbon_dioxide':  0.5,           # %
            'carbon_monoxide': 90,         # mg/nm3
            'sulphur_dioxide': 180,         # mg/nm3
            'nitrogen_dioxide': 12,        # mg/nm3
            'nitrogen_oxide': 20,           # mg/nm3
            'nox': 130,                     # mg/nm3
            'particulate_matter': 50       # mg/nm3
        },
        'medium': {
            'oxygen': .4,                   # %
            'carbon_dioxide': 0.1,            # %
            'carbon_monoxide': 17,         # mg/nm3
            'sulphur_dioxide': 35,         # mg/nm3
            'nitrogen_dioxide': 3,        # mg/nm3
            'nitrogen_oxide': 5,           # mg/nm3
            'nox': 25,                     # mg/nm3
            'particulate_matter': 11       # mg/nm3
        },
        'high': {
            'oxygen': .13,                   # %
            'carbon_dioxide': .035,            # %
            'carbon_monoxide': 7,         # mg/nm3
            'sulphur_dioxide': 13,        # mg/nm3
            'nitrogen_dioxide': 20,        # mg/nm3
            'nitrogen_oxide': 25,          # mg/nm3
            'nox': 10,                     # mg/nm3
            'particulate_matter': 4       # mg/nm3
        }
    },
    'biomass': {
        'low': {
            'oxygen': 0.5,                   # %
            'carbon_dioxide': 3,            # %
            'carbon_monoxide': 85,         # mg/nm3
            'sulphur_dioxide': 180,         # mg/nm3
            'nitrogen_dioxide': 12,        # mg/nm3
            'nitrogen_oxide': 25,           # mg/nm3
            'nox': 125,                     # mg/nm3
            'particulate_matter': 55       # mg/nm3
        },
        'medium': {
            'oxygen': 0.36,                   # %
            'carbon_dioxide': .08,            # %
            'carbon_monoxide': 17,         # mg/nm3
            'sulphur_dioxide': 35,         # mg/nm3
            'nitrogen_dioxide': 2.4,        # mg/nm3
            'nitrogen_oxide': 5,           # mg/nm3
            'nox': 25,                     # mg/nm3
            'particulate_matter': 11       # mg/nm3
        },
        'high': {
            'oxygen': 0.13,                   # %
            'carbon_dioxide': .026,            # %
            'carbon_monoxide': 5.6,         # mg/nm3
            'sulphur_dioxide': 11,        # mg/nm3
            'nitrogen_dioxide': 0.8,        # mg/nm3
            'nitrogen_oxide': 1.47,          # mg/nm3
            'nox': 8.35,                     # mg/nm3
            'particulate_matter': 3.65       # mg/nm3
        }
    }
}

        self.peqs_limits = {
            'carbon_monoxide': 800,      # mg/nm3
            'sulphur_dioxide': 1700,     # mg/nm3
            'nox': 1200,                 # mg/nm3
            'particulate_matter': 500    # mg/nm3
        }

    def get_load_range(self, steam_load):
        for range_name, (min_load, max_load) in self.steam_ranges.items():
            if min_load <= steam_load <= max_load:
                return range_name
        return 'high'

    def calculate_emissions(self, steam_load, fuel_type, fuel_mix=None):
        load_range = self.get_load_range(steam_load)

        if fuel_type == 'mixed' and fuel_mix:
            coal_emissions = {param: value * (fuel_mix['coal']/100)
                            for param, value in self.factors['coal'][load_range].items()}
            biomass_emissions = {param: value * (fuel_mix['biomass']/100)
                               for param, value in self.factors['biomass'][load_range].items()}

            emissions = {param: coal_emissions[param] + biomass_emissions[param]
                        for param in coal_emissions.keys()}
        else:
            emissions = self.factors[fuel_type][load_range].copy()

        # Adjust emissions based on steam load
        _, range_max = self.steam_ranges[load_range]
        load_factor = steam_load / range_max

        for param in emissions:
            emissions[param] *= load_factor * steam_load

        return emissions, load_range

    def validate_input(self, steam_load, fuel_type, fuel_mix=None):
        if steam_load <= 0:
            raise ValueError("Steam load must be greater than 0 TPH")
        if steam_load > 300:
            st.warning("Steam load exceeds typical range (>300 TPH). Results may be less accurate.")

        if fuel_type not in ['coal', 'biomass', 'mixed']:
            raise ValueError("Invalid fuel type. Must be 'coal', 'biomass', or 'mixed'")

        if fuel_type == 'mixed' and fuel_mix:
            if fuel_mix['coal'] + fuel_mix['biomass'] != 100:
                raise ValueError("Fuel mix percentages must sum to 100%")

        return True

    def display_results(self, emissions, steam_load, load_range, fuel_type, fuel_mix=None):
        st.write(f"\nOperating Parameters:")
        st.write(f"Steam Load: {steam_load:.2f} TPH")
        st.write(f"Load Range: {load_range.upper()}")
        st.write(f"Fuel Type: {fuel_type.upper()}")
        if fuel_mix:
            st.write(f"Fuel Mix: Coal {fuel_mix['coal']}%, Biomass {fuel_mix['biomass']}%")

        results_df = pd.DataFrame({
            'Parameter': [
                'Oxygen (%)',
                'Carbon Dioxide (%)',
                'Carbon Monoxide (mg/nm³)',
                'Sulphur Dioxide (mg/nm³)',
                'Nitrogen Dioxide (mg/nm³)',
                'Nitrogen Oxide (mg/nm³)',
                'NOx (mg/nm³)',
                'Particulate Matter (mg/nm³)'
            ],
            'Value': [
                round(emissions['oxygen'], 2),
                round(emissions['carbon_dioxide'], 2),
                round(emissions['carbon_monoxide'], 2),
                round(emissions['sulphur_dioxide'], 2),
                round(emissions['nitrogen_dioxide'], 2),
                round(emissions['nitrogen_oxide'], 2),
                round(emissions['nox'], 2),
                round(emissions['particulate_matter'], 2)
            ]
        })

        st.write("\nEmissions Results:")
        st.dataframe(results_df)

        comparison_df = self.compare_with_peqs(emissions)
        st.write("\nPEQS Compliance Status:")
        st.dataframe(comparison_df)

    def compare_with_peqs(self, emissions):
        comparison = []
        for parameter, limit in self.peqs_limits.items():
            calculated = emissions[parameter]
            status = "✓ Compliant" if calculated <= limit else "❌ Exceeded"
            percentage = (calculated / limit) * 100

            comparison.append({
                'Parameter': parameter.replace('_', ' ').title(),
                'Calculated Value (mg/nm³)': round(calculated, 2),
                'PEQS Limit (
