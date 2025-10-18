

import pandas as pd

from streamlit_app.data_manger import DFManager

def run_simulation(
    sim_time: int,
    total_parts: int,
    mission_need: int,
    stage_dist: list[str],
    stage_param1: list[float],
    stage_param2: list[float],
    custom_params: list[dict] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Execute the discrete-event simulation (DES) for the Hill AFB logistics model.

    This function initializes the DataFrame-based simulation environment using
    `DFManager`, generates all input parameter tables, and executes the main
    simulation loop. It returns the full simulation DataFrame and the MICAP
    (Mission Impaired Capability Awaiting Parts) event log.

    Parameters
    ----------
    sim_time : int
        Total number of simulation time units (e.g., days or ticks) to run.
    total_parts : int
        Total number of parts available in the inventory at simulation start.
    mission_need : int
        Required number of operational vehicles to meet mission readiness.
    stage_distributions : list of str
        Names of statistical distributions used for each repair stage
        (e.g., `["weibull", "gamma", "normal", "exponential"]`).
    stage_param1 : list of float
        First parameter (e.g., shape, mean) for each stage’s distribution.
        Must align by index with `stage_distributions`.
    stage_param2 : list of float
        Second parameter (e.g., scale, std dev) for each stage’s distribution.
    custom_params : list of dict, optional
        List of user-defined parameter modifications applied during simulation.
        Each dictionary in the list should include:
            - "period" (int): The simulation period or time tick when the change occurs.
            - "stage" (str): The name of the stage being modified (e.g., "fleet", "depot").
            - "value" (float): The new parameter value to apply.
        Example:
            [
                {"period": 50, "stage": "fleet", "value": 1.2},
                {"period": 120, "stage": "depot", "value": 0.8}
            ]

    Returns
    -------
    sim_df : pandas.DataFrame
        Main simulation output, containing time-indexed state of all vehicles
        and parts (e.g., active, repairing, queued, failed).
    micap_log : pandas.DataFrame
        Log of all MICAP events including timestamp, shortage cause, and backlog.

    Notes
    -----
    The function instantiates the `DFManager` class to manage internal DataFrame
    creation and state transitions. Core phases:
        1. Create simulation parameter table (`_create_params_df`)
        2. Initialize empty simulation record (`_create_initial_sim_df`)
        3. Activate starting parts (`_create_active_parts_df`)
        4. Process simulation events (`_process_sim_df`)

    Example
    -------
    >>> sim_df, micap_log = run_simulation(
    ...     sim_time=365,
    ...     total_parts=100,
    ...     mission_need=50,
    ...     stage_distributions=["weibull", "gamma", "normal", "exponential"],
    ...     stage_param1=[1.5, 10, 5, 2],
    ...     stage_param2=[500, 2, 1, 0.5]
    ... )
    >>> sim_df.head()
          time  active_vehicles  micap_count  repairing
    0         0               60            0         10
    1         1               59            1         11
    """

    # --- Initialize simulation environment ---
    df_manager = DFManager(
        sim_time=sim_time,
        total_parts=total_parts,
        mission_need=mission_need,
        stage_dists=stage_dist,
        stage_param1=stage_param1,
        stage_param2=stage_param2,
        custom_params=custom_params
    )

    # --- Setup simulation dataframes ---
    params_df = df_manager.create_params_df()
    sim_df = df_manager.create_initial_sim_df()
    active_parts_df = df_manager.create_active_parts_df(sim_df=sim_df)

    # --- Execute main loop ---
    sim_df, micap_log = df_manager.process_simulation(
        params_df=params_df,
        sim_time=sim_time,
        sim_df=sim_df,
        active_parts_df=active_parts_df
    )

    return sim_df, micap_log
