"""
data_manager.py
---------------
Manages all simulation DataFrames for the Hill AFB Discrete Event Simulation (DES).

This module creates, updates, and processes simulation data.
It acts as the main data engine that powers part life cycles,
distribution sampling, mission needs, and MICAP tracking.

Main responsibilities:
    1. Build parameter tables and apply user edits.
    2. Generate simulation data for each part.
    3. Run the simulation loop and log MICAPs.
"""

import pandas as pd
import numpy as np
import streamlit as st


class DFManager:
    """Manages all simulation-related DataFrames."""

    # Mapping of UI-friendly names to column names
    STAGE_LABEL_MAP = {
        # Stage One
        "Stage One Dist": "stage_one_dist",
        "Stage One Param 1": "stage_one_dist_value_1",
        "Stage One Param 2": "stage_one_dist_value_2",

        # Stage Two
        "Stage Two Dist": "stage_two_dist",
        "Stage Two Param 1": "stage_two_dist_value_1",
        "Stage Two Param 2": "stage_two_dist_value_2",

        # Stage Three
        "Stage Three Dist": "stage_three_dist",
        "Stage Three Param 1": "stage_three_dist_value_1",
        "Stage Three Param 2": "stage_three_dist_value_2",

        # Stage Four
        "Stage Four Dist": "stage_four_dist",
        "Stage Four Param 1": "stage_four_dist_value_1",
        "Stage Four Param 2": "stage_four_dist_value_2",
    }

    # ------------------------------------------------------------------
    # 1. INITIAL SETUP
    # ------------------------------------------------------------------
    def __init__(
        self,
        sim_time: int,
        total_parts: int,
        mission_need: int,
        stage_dists: list,
        stage_param1: list | None = None,
        stage_param2: list | None = None,
        custom_params: list | None = None,
    ):
        """
        Initialize a DFManager to manage simulation data.

        Parameters
        ----------
        sim_time : int
            Total number of periods (days/ticks) to simulate.
        n_total_parts : int
            Total number of parts in the system.
        mission_need : int
            Required number of active parts each period.
        stage_dist : list of str
            Names of distributions for each of the four stages.
        stage_dist_value_1, stage_dist_value_2 : list of float, optional
            Parameters for each distribution (shape, scale, etc.).
        custom_params : list of dict, optional
            List of user edits to override parameters at specific periods.
        """
        self.sim_time = sim_time
        self.n_total_parts = total_parts
        self.mission_need = mission_need
        self.stage_dist = stage_dists
        self.stage_dist_value_1 = stage_param1 or []
        self.stage_dist_value_2 = stage_param2 or []
        self.custom_params = custom_params or []
        self.params_df: pd.DataFrame | None = None
        self.mission_need_overrides = {}

    # ------------------------------------------------------------------
    # 2. PARAMETER MANAGEMENT
    # ------------------------------------------------------------------
    def create_params_df(self) -> pd.DataFrame:
        """
        Build the base parameter table for all simulation periods.

        Returns
        -------
        pandas.DataFrame
            A DataFrame with all stage distributions and parameters for each period.
        """
        df = pd.DataFrame({
            "period": range(1, self.sim_time + 1),
            "n_total_parts": self.n_total_parts,
            "stage_one_dist": self.stage_dist[0],
            "stage_one_dist_value_1": self.stage_dist_value_1[0],
            "stage_one_dist_value_2": self.stage_dist_value_2[0],
            "stage_two_dist": self.stage_dist[1],
            "stage_two_dist_value_1": self.stage_dist_value_1[1],
            "stage_two_dist_value_2": self.stage_dist_value_2[1],
            "stage_three_dist": self.stage_dist[2],
            "stage_three_dist_value_1": self.stage_dist_value_1[2],
            "stage_three_dist_value_2": self.stage_dist_value_2[2],
            "stage_four_dist": self.stage_dist[3],
            "stage_four_dist_value_1": self.stage_dist_value_1[3],
            "stage_four_dist_value_2": self.stage_dist_value_2[3],
        })

        # Apply any user-defined overrides
        if self.custom_params:
            df = self._apply_custom_params(df)

        self.params_df = df
        return df

    def _apply_custom_params(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply user-defined parameter changes to the parameter table.

        Each custom parameter edit contains:
            - "period": int — when the change occurs
            - "stage": str — which parameter to modify
            - "value": float — the new value

        Returns
        -------
        pandas.DataFrame
            Updated parameter DataFrame with overrides applied.
        """
        for edit in self.custom_params:
            stage = edit.get("stage")
            period = int(edit.get("period", 0))
            value = edit.get("value")

            if stage == "Mission Need":
                self.mission_need_overrides[period] = value
            else:
                stage_col = self.STAGE_LABEL_MAP.get(stage)
                if stage_col in df.columns:
                    df.loc[df["period"] == period, stage_col] = value

        return df

    def get_params_for_period(self, period: int) -> pd.Series:
        """Return the row of parameters for a specific simulation period."""
        period = max(1, min(period, self.sim_time))
        return self.params_df[self.params_df["period"] == period].iloc[0]

    # ------------------------------------------------------------------
    # 3. SIMULATION SETUP
    # ------------------------------------------------------------------
    def create_initial_sim_df(self) -> pd.DataFrame:
        """
        Create the initial simulation DataFrame.

        Each part receives a randomly sampled duration for all four stages.
        Start and end times are calculated sequentially.

        Returns
        -------
        pandas.DataFrame
            Initial simulation state for all parts.
        """
        sim_df = pd.DataFrame({
            "part_id": range(1, self.n_total_parts + 1),
            "cycle": 1,
            "condemn": "no"
        })

        for stage in ["one", "two", "three", "four"]:
            dist = self.params_df[f"stage_{stage}_dist"].iloc[0]
            p1 = self.params_df[f"stage_{stage}_dist_value_1"].iloc[0]
            p2 = self.params_df[f"stage_{stage}_dist_value_2"].iloc[0]
            sim_df[f"stage_{stage}_duration"] = [
                self._sample_duration(dist, p1, p2) for _ in range(self.n_total_parts)
            ]

        # Calculate start and end times per part
        for i, stage in enumerate(["one", "two", "three", "four"]):
            if i == 0:
                sim_df[f"stage_{stage}_start"] = 1.0
            else:
                prev = ["one", "two", "three", "four"][i - 1]
                sim_df[f"stage_{stage}_start"] = sim_df[f"stage_{prev}_end"]
            sim_df[f"stage_{stage}_end"] = (
                sim_df[f"stage_{stage}_start"] + sim_df[f"stage_{stage}_duration"]
            )

        return sim_df

    def create_active_parts_df(self, sim_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get the most recent record for each active part.

        Removes condemned parts and keeps the latest entry.
        """
        active_parts_df = (
            sim_df[sim_df["condemn"] == "no"]
            .sort_values(["part_id", "stage_four_end"])
            .groupby("part_id", as_index=False)
            .tail(1)
            .copy()
        )
        active_parts_df["stage_four_end"] = active_parts_df["stage_four_end"].round()
        return active_parts_df

    # ------------------------------------------------------------------
    # 4. SUPPORT FUNCTIONS
    # ------------------------------------------------------------------
    def _sample_duration(self, dist_name: str, val1: float, val2: float) -> float:
        """Draw one random duration from a supported distribution."""
        if dist_name == "normal":
            return max(0, np.random.normal(loc=val1, scale=val2))
        elif dist_name == "weibull":
            return max(0, np.random.weibull(a=val1) * val2)
        else:
            raise ValueError(f"Unsupported distribution '{dist_name}'.")
        np.random.seed(123)

    # ------------------------------------------------------------------
    # 5. MAIN SIMULATION PROCESS
    # ------------------------------------------------------------------
    def process_simulation(self, params_df: pd.DataFrame,
                           sim_time: int, sim_df: pd.DataFrame,
                           active_parts_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Run the full simulation over time.

        This loop updates part states for each period, tracks active parts,
        applies mission need overrides, and logs MICAP events.

        Returns
        -------
        tuple[pandas.DataFrame, pandas.DataFrame]
            Updated simulation data and MICAP log.
        """
        micap_log = []
        progress_text = st.empty()
        progress_bar = st.progress(0)

        for period in params_df["period"]:
            micap_entry, sim_df, active_parts_df = self._simulate_period(
                period, params_df, sim_time, sim_df, active_parts_df
            )
            micap_log.append(micap_entry)

            percent = int(period / sim_time * 100)
            progress_bar.progress(percent)
            progress_text.text(f"Simulating day {period} of {sim_time}... ({percent}%)")

        return sim_df, pd.DataFrame(micap_log)

    def _simulate_period(self, period: int, params_df: pd.DataFrame,
                         sim_time: int, sim_df: pd.DataFrame,
                         active_parts_df: pd.DataFrame) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
        """
        Simulate a single period and return updates.

        Handles part cycling, active counts, and MICAP calculations.
        """
        # Determine mission need for this period
        current_need = self.mission_need_overrides.get(period, self.mission_need)

        # Count active parts
        active_stage_one = sim_df[
            (sim_df["stage_one_start"] <= period)
            & (sim_df["stage_one_end"] > period)
            & (sim_df["condemn"] == "no")
        ]
        active_count = len(active_stage_one)
        micap = max(0, current_need - active_count)

        micap_entry = {
            "period": period,
            "active_stage_one": active_count,
            "mission_need": current_need,
            "micap": micap,
        }

        # Get all parts that just finished a cycle
        ending_parts = active_parts_df[active_parts_df["stage_four_end"] == period]
        if not ending_parts.empty:
            new_rows = [self._generate_new_cycle(i, period, sim_time, params_df, sim_df)
                        for i in ending_parts["part_id"]]
            sim_df = pd.concat([sim_df, pd.DataFrame(new_rows)], ignore_index=True)

        # Update active parts
        active_parts_df = (
            sim_df[sim_df["condemn"] == "no"]
            .sort_values(["part_id", "stage_four_end"])
            .groupby("part_id", as_index=False)
            .tail(1)
            .copy()
        )
        active_parts_df["stage_four_end"] = active_parts_df["stage_four_end"].round()

        return micap_entry, sim_df, active_parts_df

    def _generate_new_cycle(self, part_id: int, period: int,
                            sim_time: int, params_df: pd.DataFrame,
                            sim_df: pd.DataFrame) -> dict:
        """
        Generate a new life cycle for one part after completing its last stage.
        """
        part_row = sim_df[sim_df["part_id"] == part_id].iloc[-1]
        period_params = params_df.loc[params_df["period"] == period].iloc[0]
        start_time = part_row["stage_four_end"]
        cycle = part_row["cycle"] + 1
        condemn = part_row["condemn"]

        # Sample durations for all 4 stages
        durations = {
            f"d{i}": self._sample_duration(
                period_params[f"stage_{i}_dist"],
                period_params[f"stage_{i}_dist_value_1"],
                period_params[f"stage_{i}_dist_value_2"],
            )
            for i in ["one", "two", "three", "four"]
        }

        # Build new lifecycle
        s1_start = start_time
        s1_end = s1_start + durations["done"]
        s2_start, s2_end = s1_end, s1_end + durations["dtwo"]
        s3_start, s3_end = s2_end, s2_end + durations["dthree"]
        s4_start, s4_end = s3_end, s3_end + durations["dfour"]
        if s4_end > sim_time:
            s4_end = np.nan

        return {
            "period": period,
            "part_id": part_id,
            "stage_one_duration": durations["done"],
            "stage_two_duration": durations["dtwo"],
            "stage_three_duration": durations["dthree"],
            "stage_four_duration": durations["dfour"],
            "stage_one_start": s1_start,
            "stage_one_end": s1_end,
            "stage_two_start": s2_start,
            "stage_two_end": s2_end,
            "stage_three_start": s3_start,
            "stage_three_end": s3_end,
            "stage_four_start": s4_start,
            "stage_four_end": s4_end,
            "cycle": cycle,
            "condemn": condemn,
        }
