"""
main.py
-----------------
Streamlit entrypoint for the Hill AFB DES simulation interface.

This module handles UI flow and delegates logic to supporting modules:
    - `streamlit_ui`: user interface and parameter input
    - `simulation`: runs the DES core logic
    - `plotting`: handles visualizations

Usage
-----
Run 'run_streamlit_app.py' in root of directory
"""
import streamlit as st

from simulation_engine import run_simulation
from ui_components import init_ui
from plotting import plot_results

def main() -> None:
    st.title("Hill AFB Discrete Event Simulation")
    st.markdown("Configure simulation parameters in the sidebar and click **Run Simulation**.")

    # --- Get inputs from UI ---
    total_parts, sim_time, mission_need, stage_dists, stage_param1, stage_param2 = init_ui()
    
    # --- Run Simulation after clicking "Run Simulation" button ---
    run_button = st.sidebar.button("Run Simulation", type="primary")
    if run_button:
        with st.spinner("Running simulation..."):
            # --- Run Simulation ---
            sim_df, micap_log = run_simulation(sim_time, total_parts, mission_need, stage_dists, stage_param1, stage_param2, custom_params=st.session_state.get("custom_params", []))
            st.success("Simulation complete!")
            # --- Plot Results of Simulation ---
            micap_plot, wip_fleet_plot, wip_conf_plot, wip_depot_plot, wip_cona_plot = plot_results(sim_df, micap_log)
            # --- Display Plots ---
            st.pyplot(micap_plot.draw())
            col1, col2 = st.columns(2)
            with col1:
                st.pyplot(wip_fleet_plot.draw())
            with col2:
                st.pyplot(wip_conf_plot.draw())

            col3, col4 = st.columns(2)
            with col3:
                st.pyplot(wip_depot_plot.draw())
            with col4:
                st.pyplot(wip_cona_plot.draw())
    else:
        st.info("Adjust parameters and click Run Simulation.")

if __name__ == "__main__":
    main()