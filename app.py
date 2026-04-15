"""
Name: Fiza Raju
CS230: Section XXX
Data: Starbucks in the USA
URL: Link to your web application on Streamlit Cloud (if posted)

Description:
This program is an interactive Streamlit data explorer for Starbucks locations in the United States.
Users can explore store patterns by state, city, and ownership type using filters, charts, summary
statistics, and a detailed PyDeck map. The app includes a state-level overview, city-level analysis,
ownership type breakdowns, and a searchable table of locations.

References:
- Streamlit documentation: https://docs.streamlit.io/
- PyDeck documentation: https://deckgl.readthedocs.io/
"""
# Code generated with help from ChatGPT. See AI use report section 1.

from pathlib import Path
import pandas as pd
import streamlit as st
import pydeck as pdk
import matplotlib.pyplot as plt


st.set_page_config(
    page_title="Starbucks USA Explorer",
    page_icon="☕",
    layout="wide"
)


#[FUNC2P]
@st.cache_data
def load_data(file_path="usa_starbucks (1).csv", only_us=True):
    """Load and clean the Starbucks data."""
    df = pd.read_csv(file_path)

    #[COLUMNS]
    keep_cols = [
        "Store Name", "Ownership Type", "Street Address", "City",
        "State/Province", "Country", "Postcode", "Longitude", "Latitude"
    ]
    df = df[keep_cols].copy()

    if only_us:
        #[FILTER1]
        df = df[df["Country"] == "US"].copy()

    # #[LAMBDA]
    df["City"] = df["City"].fillna("").apply(lambda x: str(x).strip().title())
    df["State/Province"] = df["State/Province"].fillna("").apply(lambda x: str(x).strip().upper())
    df["Ownership Type"] = df["Ownership Type"].fillna("Unknown").apply(lambda x: str(x).strip().title())

    #[FILTER1]
    df = df.dropna(subset=["Latitude", "Longitude"])

    return df


#[FUNC2P]
def filter_data(df, state, ownership_types=None, city_search=""):
    """Filter the data by state, ownership type, and optional city text."""
    #[FILTER1]
    filtered = df[df["State/Province"] == state].copy()

    if ownership_types:
        #[FILTER2]
        filtered = filtered[filtered["Ownership Type"].isin(ownership_types)].copy()

    city_search = city_search.strip()
    if city_search:
        #[FILTER2]
        filtered = filtered[filtered["City"].str.contains(city_search, case=False, na=False)].copy()

    return filtered


#[FUNCRETURN2]
def get_state_summary(df, state):
    """Return the filtered state data and a small summary dictionary."""
    state_df = df[df["State/Province"] == state].copy()
    summary = {
        "stores": int(len(state_df)),
        "cities": int(state_df["City"].nunique()),
        "ownership_types": int(state_df["Ownership Type"].nunique())
    }
    return state_df, summary


#[FUNC2P]
def get_top_cities(df, top_n=10):
    """Return the top cities by store count."""
    city_counts = (
        df.groupby("City")
        .size()
        .reset_index(name="Store Count")
    )

    #[SORT]
    city_counts = city_counts.sort_values("Store Count", ascending=False).head(top_n)
    return city_counts


#[FUNC2P]
def get_top_states(df, top_n=10):
    """Return the top states by store count."""
    state_counts = (
        df.groupby("State/Province")
        .size()
        .reset_index(name="Store Count")
    )

    #[SORT]
    state_counts = state_counts.sort_values("Store Count", ascending=False).head(top_n)
    return state_counts


#[FUNCCALL2]
def make_summary_lines(summary_dict):
    """Turn summary stats into readable lines for display."""
    lines = []
    #[ITERLOOP]
    for key, value in summary_dict.items():
        label = key.replace("_", " ").title()
        lines.append(f"- {label}: {value}")
    return lines


def find_extremes(df):
    """Find max/min summary values for the selected data."""
    counts = df.groupby("City").size().reset_index(name="Store Count")
    if counts.empty:
        return None, None

    #[MAXMIN]
    max_row = counts.loc[counts["Store Count"].idxmax()]
    #[MAXMIN]
    min_row = counts.loc[counts["Store Count"].idxmin()]

    return max_row, min_row


def build_map_df(df):
    """Prepare a smaller DataFrame for the map."""
    map_df = df.copy()
    map_df["tooltip_label"] = (
        map_df["Store Name"]
        + " | " + map_df["City"]
        + " | " + map_df["Ownership Type"]
    )
    return map_df


def detect_csv_file():
    """Try to find the Starbucks CSV automatically if the exact name changes."""
    possible_files = [
        "usa_starbucks (1).csv",
        "usa_starbucks.csv",
        "starbucks.csv"
    ]

    #[LISTCOMP]
    existing = [name for name in possible_files if Path(name).exists()]
    if existing:
        return existing[0]

    for path in Path(".").glob("*.csv"):
        if "starbucks" in path.name.lower():
            return str(path)

    return None


def main():
    st.title("☕ Starbucks in the USA Explorer")
    st.sidebar.image("starbucks.jpeg", width=150)

    st.write(
        "Use the filters in the sidebar to explore Starbucks store locations, compare cities, "
        "states, and ownership patterns across the United States."
    )

    csv_file = detect_csv_file()
    if not csv_file:
        st.error("Starbucks CSV file not found. Put the CSV in the same folder as this app.")
        st.stop()

    df = load_data(csv_file)

    # #[PIVOTTABLE]
    state_ownership_pivot = pd.pivot_table(
        df,
        index="State/Province",
        columns="Ownership Type",
        values="Store Name",
        aggfunc="count",
        fill_value=0
    )

    # #[DICTMETHOD]
    state_counts_dict = {}
    #[ITERLOOP]
    for state_name, count in df["State/Province"].value_counts().items():
        state_counts_dict[state_name] = int(count)
    top_state = max(state_counts_dict, key=state_counts_dict.get)

    st.sidebar.header("Filters and Controls")

    # #[ST1]
    state_options = sorted(df["State/Province"].dropna().unique())
    selected_state = st.sidebar.selectbox("Choose a state", state_options)

    state_df, summary = get_state_summary(df, selected_state)

    ownership_options = sorted(state_df["Ownership Type"].dropna().unique())

    # #[ST1]
    selected_ownership = st.sidebar.multiselect(
        "Choose ownership type(s)",
        ownership_options,
        default=ownership_options
    )

    # #[ST2]
    top_n = st.sidebar.slider("How many top states/cities should be shown?", 3, 20, 10)

    city_search = st.sidebar.text_input("Search for a city name (optional)")

    # #[ST3]
    st.sidebar.markdown("---")
    st.sidebar.caption("Built with Streamlit, Pandas, Matplotlib, and PyDeck")

    filtered_df = filter_data(state_df, selected_state, selected_ownership, city_search)

    # #[FUNCCALL2]
    summary_lines = make_summary_lines(summary)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Selected State", selected_state)
    col2.metric("Stores in State", summary["stores"])
    col3.metric("Cities in State", summary["cities"])
    col4.metric("Top State Overall", top_state)

    with st.expander("Quick summary"):
        st.markdown("\n".join(summary_lines))
        st.write(f"After applying the filters, {len(filtered_df)} store(s) remain.")

    st.subheader("Top States by Number of Starbucks Stores")
    top_states = get_top_states(df, top_n)

    fig0, ax0 = plt.subplots(figsize=(10, 5))
    ax0.bar(top_states["State/Province"], top_states["Store Count"], edgecolor="black")
    ax0.set_title(f"Top {top_n} States by Number of Stores")
    ax0.set_xlabel("State")
    ax0.set_ylabel("Number of Stores")
    ax0.tick_params(axis="x", rotation=45)
    st.pyplot(fig0)

    if filtered_df.empty:
        st.warning("No stores match your current filters.")
        st.stop()

    st.subheader(f"Store Table for {selected_state}")
    st.dataframe(
        filtered_df.sort_values(["City", "Store Name"]).reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )

    # #[CHART1]
    st.subheader("Top Cities by Number of Stores in Selected State")
    top_cities = get_top_cities(filtered_df, top_n)

    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.bar(top_cities["City"], top_cities["Store Count"], edgecolor="black")
    ax1.set_title(f"Top {top_n} Cities in {selected_state}")
    ax1.set_xlabel("City")
    ax1.set_ylabel("Number of Stores")
    ax1.tick_params(axis="x", rotation=45)
    st.pyplot(fig1)

    # #[CHART2]
    st.subheader("Ownership Type Breakdown")
    ownership_counts = filtered_df["Ownership Type"].value_counts()

    fig2, ax2 = plt.subplots(figsize=(7, 7))
    ax2.pie(
        ownership_counts.values,
        labels=ownership_counts.index,
        autopct="%1.1f%%",
        startangle=90
    )
    ax2.set_title(f"Ownership Type Share in {selected_state}")
    st.pyplot(fig2)

    st.subheader("Map of Starbucks Locations")

    map_df = build_map_df(filtered_df)

    # #[MAP]
    view_state = pdk.ViewState(
        latitude=float(map_df["Latitude"].mean()),
        longitude=float(map_df["Longitude"].mean()),
        zoom=6,
        pitch=35
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[Longitude, Latitude]",
        get_radius=12000,
        get_fill_color=[180, 60, 60, 160],
        pickable=True,
    )

    tooltip = {
        "html": "<b>{Store Name}</b><br/>{City}<br/>{Ownership Type}<br/>{Street Address}",
        "style": {"backgroundColor": "white", "color": "black"}
    }

    st.pydeck_chart(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[layer],
            tooltip=tooltip
        )
    )

    st.subheader("More Insights")

    max_row, min_row = find_extremes(filtered_df)
    if max_row is not None and min_row is not None:
        st.write(
            f"The city with the most Starbucks stores in the filtered data is **{max_row['City']}** "
            f"with **{int(max_row['Store Count'])}** store(s)."
        )
        st.write(
            f"The city with the fewest Starbucks stores in the filtered data is **{min_row['City']}** "
            f"with **{int(min_row['Store Count'])}** store(s)."
        )

    st.subheader("Pivot Table: State vs Ownership Type")
    st.dataframe(state_ownership_pivot, use_container_width=True)

    # #[DICTMETHOD]
    st.subheader("State Totals Dictionary Sample")
    sample_items = dict(list(state_counts_dict.items())[:10])
    st.write("This sample dictionary stores state codes as keys and store totals as values:")
    st.json(sample_items)


if __name__ == "__main__":
    main()
