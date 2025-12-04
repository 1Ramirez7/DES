"""
main.py
-----------------
Streamlit entrypoint for the DES simulation interface.

This module handles UI flow and delegates logic to supporting modules:
    - ui_components: user interface and parameter input
    - data_manager: DataFrame structure management
    - simulation_engine: DES core logic
    - plotting: visualizations

Usage
-----
Run 'run_streamlit_app.py' in root of directory
"""
import streamlit as st
import numpy as np
import pandas as pd

import warnings # to silent future warnings, comment to test
warnings.simplefilter("ignore", category=FutureWarning)


from simulation_engine import SimulationEngine
from ui.ui_components import render_sidebar
from ui.downloads import render_download_section
from ui.stats import render_stats_tab
from utils import calculate_initial_allocation
from ui.dist_plots import render_duration_plots
from session_manager import SessionStateManager
from parameters import Parameters

# this is to clear cache in excel files when engine.run is re-ran
# need to figure out way for multi-runs see edit_id 754
from ui.downloads import generate_csv_zip, generate_excel 

def main() -> None:
    # Set page config - MUST be first Streamlit command
    st.set_page_config(
        page_title="Discrete Event Simulation",
        layout="wide",  # Use full screen width
        initial_sidebar_state="expanded"
    )
    
    st.title("Discrete Event Simulation")
    st.markdown("Configure simulation parameters in the sidebar and click **Run Simulation**.")

    # --- Initialize session state manager ---
    session_mgr = SessionStateManager()

    # --- Get inputs from UI and create Parameters object ---
    sidebar_params = render_sidebar()
    params = Parameters()
    params.set_all(sidebar_params)
    
    # --- Run Simulation after clicking "Run Simulation" button ---
    run_button = st.sidebar.button("Run Simulation", type="primary")
    
    if run_button:
        generate_csv_zip.clear() # edit_id 754
        generate_excel.clear() # edit_id 754
        # Create placeholders for progress updates
        progress_placeholder = st.empty()
        event_details = st.empty()
        
        with st.spinner("Running simulation..."):
            # Set random seed for reproducibility
            np.random.seed(params['random_seed'])
            
            # calculate initial conditions
            allocation = calculate_initial_allocation(params)
            
            # Create SimulationEngine (DataSets created internally during run())
            engine = SimulationEngine(
                params=params,
                allocation=allocation
            )
            
            # Define progress callback for live updates 777
            def update_progress(event_type, event_count, total_count):
                progress_placeholder.write(f"**Processing Events:** {total_count:,} total")
                event_details.caption(f"Latest: {event_type} (#{event_count})")
            
            # Run simulation with progress tracking
            validation_results = engine.run(progress_callback=update_progress) # progress_callback=update_progress 777
            # Get data sets for post data wrangling
            datasets = validation_results['datasets']
            
            # Clear progress displays
            progress_placeholder.empty()
            event_details.empty()
        
        # Store results using session manager (params are copied, not referenced)
        session_mgr.store_run(
            params=params,
            datasets=datasets,
            validation_results=validation_results,
            allocation=allocation
        )
        
        st.success("Simulation complete!")
    
    # --- Always render tabs (even before simulation runs) ---
    tab0, tab1, tab2, tab3 = st.tabs(["⚙️ Setup", "Cycle", "Simulation Results", "WIP Plots"])
    
    ############################
    # TAB 0 - Setup/Inputs (always visible)
    ############################
    with tab0:
        st.subheader("🔧 Additional Setup Options")
        st.write("This tab is for additional user inputs and configuration.")
        st.info("Sample placeholder text - add your inputs here!")
        
        # Example of what you could add:
        # col1, col2 = st.columns(2)
        # with col1:
        #     some_input = st.number_input("Example Input", value=100)
        # with col2:
        #     another_input = st.selectbox("Example Select", ["Option A", "Option B"])
    
    # --- Display results if simulation has been run ---
    if session_mgr.has_run():
        # Retrieve from session manager (these are the STORED values)
        run_data = session_mgr.get_run()
        datasets = run_data['datasets']
        validation_results = run_data['validation_results']
        allocation = run_data['allocation']
        stored_params = run_data['params']  # Use stored params, not current sidebar
        
        # Display event summary 777
        if 'event_counts' in validation_results:
            event_counts = validation_results['event_counts']

            ############################
            # TAB 1 
            ############################
            with tab1:
                st.subheader("📊 Event Processing Summary")
                st.write("Event count statistics")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Events", f"{event_counts['total']:,}")
                    st.metric("Depot Completions", f"{event_counts.get('depot_complete', 0):,}")
                with col2:
                    st.metric("Fleet Completions", f"{event_counts.get('fleet_complete', 0):,}")
                    st.metric("Part Fleet Ends", f"{event_counts.get('part_fleet_end', 0):,}")
                with col3:
                    st.metric("New Parts Arrived", f"{event_counts.get('new_part_arrives', 0):,}")
                    st.metric("Parts Condemned", f"{event_counts.get('part_condemn', 0):,}")
                
                render_stats_tab(datasets)

            ############################
            # TAB 2
            ############################
            with tab2:
                st.subheader("📊 Simulation Statistics")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("Part and Aircraft data exported from managers (need to update this section to include more proper information)")
                with col2:
                    st.metric("all_parts_df Rows", 
                            f"{len(datasets.all_parts_df):,}")
                with col3:
                    st.metric("all_ac_df Rows", 
                            f"{len(datasets.all_ac_df):,}")
                
                # --- Display Sample Data ---
                st.subheader("🔍 Sample Data")
                
                with st.expander("all_parts_df (Part Event Log) - First 10 Rows"):
                    st.dataframe(datasets.all_parts_df.head(10))
                
                with st.expander("all_ac_df (Aircraft Event Log) - First 10 Rows"):
                    st.dataframe(datasets.all_ac_df.head(10))

                ###########################
                # Render all duration plots 
                # from ui/dist_plots.py
                #############################
                if stored_params['render_plots']:
                    render_duration_plots(datasets.all_parts_df, allocation)
                

            ############################
            # TAB 3
            ############################
            with tab3:           
                # Plot WIP over time using new DataSets methods
                if stored_params['render_plots']:
                    if datasets.wip_df is not None and len(datasets.wip_df) > 0:
                        st.subheader("📈 Aircraft WIP Over Time (Combined)")
                        st.pyplot(datasets.plot_aircraft_wip_combined())
                        
                        st.subheader("📈 MICAP Over Time")
                        st.pyplot(datasets.plot_micap_over_time())
                        
                        st.subheader("📈 Fleet Over Time")
                        st.pyplot(datasets.plot_fleet_over_time())
                    else:
                        st.warning("No Aircraft WIP data available to plot.")
                    
                    # Condition A plot (separate from Aircraft WIP)
                    st.subheader("📈 Condition A Over Time")
                    st.pyplot(datasets.plot_condition_a_wip_over_time())
                else:
                    st.info("Plot rendering is disabled. Check 'Render Plots' in sidebar to enable.")

                # --- Download Results ---
                render_download_section(datasets)
            ############################
            # END OF TAB 3
            ############################
    
    else:
        # Show message in result tabs when simulation hasn't run yet
        with tab1:
            st.info("Run the simulation to see cycle statistics.")
        with tab2:
            st.info("Run the simulation to see results.")
        with tab3:
            st.info("Run the simulation to see WIP plots.")

if __name__ == "__main__":
    main()
