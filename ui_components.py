import streamlit as st
import pandas as pd

def init_ui():
    n_total_parts, sim_time, mission_need = load_sidebar()
    stage_dists, stage_param1, stage_param2 = load_distribution_configuration()
    load_custom_parameters()

    return n_total_parts, sim_time, mission_need, stage_dists, stage_param1, stage_param2
    
def load_main_screen():
    st.title("Sim Results")

def load_sidebar():
    st.sidebar.title("Sim Configuration")
    n_total_parts = st.sidebar.number_input("Total Parts", 0, 1000000)
    sim_time = st.sidebar.number_input("Sim Time (days)", 100, 1000000)
    mission_need = st.sidebar.number_input("Mission Need (parts)", 0, 1000000)
    return n_total_parts, sim_time, mission_need

def load_distribution_configuration():
    with st.sidebar.expander("Distribution Configuration"):
        # Constants
        dist_param_map = {
            "Normal": [("Mean", 30.0), ("Standard Deviation", 10.0)],
            "Weibull": [("Shape", 2.0), ("Scale", 10.0)]
        }
        stage_dists = []
        stage_param1 = []
        stage_param2 = []
        # Expander Setup
        for i, stage_label in enumerate(["Fleet", "Condition F", "Depot", "Condition A"], start=1):
            st.markdown(f"#### {stage_label}")
            dist_choice = st.selectbox(
                f"{stage_label} Distribution",
                options=list(dist_param_map.keys()),
                key=f"{stage_label}_dist"
            )
            stage_dists.append(dist_choice.lower())

            # Show the appropriate parameter inputs dynamically
            params = dist_param_map[dist_choice]
            p1_label, p1_default = params[0]
            p2_label, p2_default = params[1]

            param1 = st.number_input(f"{stage_label} {p1_label}", value=p1_default, key=f"{stage_label}_p1")
            param2 = st.number_input(f"{stage_label} {p2_label}", value=p2_default, key=f"{stage_label}_p2")

            stage_param1.append(param1)
            stage_param2.append(param2)
    return stage_dists, stage_param1, stage_param2

def load_custom_parameters():
    use_custom = st.sidebar.toggle("Enable Custom Parameters")
    if use_custom:
        st.sidebar.markdown("#### Add Parameter Override")

        period = st.sidebar.number_input("Period", 0)

        param_options = [
            "Mission Need",
            "Stage One Param 1", "Stage One Param 2",
            "Stage Two Param 1", "Stage Two Param 2",
            "Stage Three Param 1", "Stage Three Param 2",
            "Stage Four Param 1", "Stage Four Param 2"
        ]
        selected_param = st.sidebar.selectbox("Parameter to Change", options=param_options)

        new_value = st.sidebar.number_input("New Value", value=10.0)

        if "custom_params" not in st.session_state:
            st.session_state.custom_params = []

        if st.sidebar.button("Add Override"):
            st.session_state.custom_params.append({
                "period": period,
                "stage": selected_param,
                "value": new_value
            })
            st.success(f"Added override: {selected_param} = {new_value} (Period {period})")

        if st.session_state.custom_params:
            st.sidebar.markdown("#### Current Overrides")
            st.sidebar.dataframe(pd.DataFrame(st.session_state.custom_params))