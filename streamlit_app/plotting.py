from plotnine import ggplot, aes, geom_line, theme_minimal, labs, geom_smooth

def plot_results(sim_output, micap_log):
    micap_plot = (
        ggplot(micap_log, aes(x = "period", y = "micap")) +
        geom_line(color="#b0b0b0", size=1) +
        labs(
            x = "Day",
            y = "MICAPs",
            title = "When did MICAPs occur?",
            subtitle = "MICAP is defined as mission need > available stage one parts"
        ) +
        theme_minimal()
    )

    agg_df = (sim_output.groupby("period", as_index=False)[["stage_one_duration", "stage_two_duration", "stage_three_duration", "stage_four_duration"]].mean())

    mean_duration_one = agg_df["stage_one_duration"].mean()
    mean_duration_two = agg_df["stage_two_duration"].mean()
    mean_duration_three = agg_df["stage_three_duration"].mean()
    mean_duration_four = agg_df["stage_four_duration"].mean()

    wip_fleet_plot = (
        ggplot(agg_df, aes(x="period", y="stage_one_duration")) +
        geom_line(color="#b0b0b0", size=1) +
        geom_smooth(method="lm", color="red", se=False, linetype="dashed") +
        labs(
            x = "Day",
            y = "Average Duration",
            title = "What is the Average Time a Part Spends in Fleet?",
            subtitle = f"Average duration in fleet == {mean_duration_one:.2f} days"
        ) +
        theme_minimal()
    )

    wip_conf_plot = (
        ggplot(agg_df, aes(x="period", y="stage_two_duration")) +
        geom_line(color="#b0b0b0", size=1) +
        geom_smooth(method="lm", color="red", se=False, linetype="dashed") +
        labs(
            x = "Day",
            y = "Average Duration",
            title = "What is the Average Time a Part Spends in Condition F?",
            subtitle = f"Average duration in fleet == {mean_duration_two:.2f} days"
        ) +
        theme_minimal()
    )

    wip_depot_plot = (
        ggplot(agg_df, aes(x="period", y="stage_three_duration")) +
        geom_line(color="#b0b0b0", size=1) +
        geom_smooth(method="lm", color="red", se=False, linetype="dashed") +
        labs(
            x = "Day",
            y = "Average Duration",
            title = "What is the Average Time a Part Spends in the Depot?",
            subtitle = f"Average duration in fleet == {mean_duration_three:.2f} days"
        ) +
        theme_minimal()
    )

    wip_cona_plot = (
        ggplot(agg_df, aes(x="period", y="stage_four_duration")) +
        geom_line(color="#b0b0b0", size=1) +
        geom_smooth(method="lm", color="red", se=False, linetype="dashed") +
        labs(
            x = "Day",
            y = "Average Duration",
            title = "What is the Average Time a Part Spends in Condition A?",
            subtitle = f"Average duration in fleet == {mean_duration_four:.2f} days"
        ) +
        theme_minimal()
    )

    return micap_plot, wip_fleet_plot, wip_conf_plot, wip_depot_plot, wip_cona_plot