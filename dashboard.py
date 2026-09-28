import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import timedelta
from supabase import create_client


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="LEOS IPM310 SCADA",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_PATH = r"D:\MDB\energy_data.db"

# จำนวนจุดสูงสุดเฉพาะ "กราฟ"
# ตารางและ Database ไม่ถูกตัดข้อมูล
MAX_CHART_POINTS = 12000


# =========================================================
# PAGE CSS
# =========================================================

st.html("""
<style>

.stApp {
    background: #07111f;
    color: #eaf6ff;
}

.block-container {
    max-width: 1600px;
    padding-top: 20px;
    padding-bottom: 40px;
}


/* HEADER */

.scada-header {
    background: linear-gradient(
        135deg,
        #0b1c30,
        #102b45
    );
    border: 1px solid #1d4868;
    border-radius: 15px;
    padding: 24px 28px;
    margin-bottom: 20px;
}

.scada-title {
    font-size: 30px;
    font-weight: 700;
    color: #ffffff;
}

.scada-subtitle {
    margin-top: 8px;
    color: #8ca8c0;
    font-size: 15px;
}

.online {
    color: #00ff88;
    font-weight: 700;
}


/* SECTION */

.section-title {
    margin-top: 20px;
    margin-bottom: 12px;
    padding-left: 12px;
    border-left: 5px solid #00bfff;
    color: #ffffff;
    font-size: 22px;
    font-weight: 700;
}


/* MAIN CARD */

.main-card {
    background: linear-gradient(
        145deg,
        #0c1d30,
        #091625
    );
    border: 1px solid #1c405d;
    border-radius: 14px;
    padding: 20px;
    min-height: 145px;
}

.card-label {
    color: #8ca8c0;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 1px;
}

.card-number {
    color: #00d9ff;
    font-size: 36px;
    font-weight: 700;
    margin-top: 15px;
}

.card-unit {
    color: #8ca8c0;
    font-size: 18px;
}


/* STATUS */

.status-card {
    background: linear-gradient(
        145deg,
        #0c1d30,
        #091625
    );
    border: 1px solid #1c405d;
    border-radius: 14px;
    padding: 20px;
    min-height: 145px;
}

.status-online {
    color: #00ff88;
    font-size: 20px;
    font-weight: 700;
}

.status-offline {
    color: #ff4d4d;
    font-size: 20px;
    font-weight: 700;
}

.update-label {
    color: #8ca8c0;
    font-size: 14px;
    margin-top: 15px;
}

.update-value {
    color: #ffffff;
    font-size: 17px;
    margin-top: 5px;
}


/* PHASE */

.phase-card {
    background: #0b1a2b;
    border: 1px solid #1b405c;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}

.phase-label {
    color: #8ca8c0;
    font-size: 14px;
    font-weight: 600;
}

.phase-number {
    color: #ffffff;
    font-size: 28px;
    font-weight: 700;
    margin-top: 10px;
}


/* COMBINED PHASE */

.combined-phase-card {
    background: linear-gradient(
        145deg,
        #0c2135,
        #091827
    );
    border: 1px solid #00bfff;
    border-radius: 14px;
    padding: 22px;
    text-align: center;
    min-height: 190px;
}

.combined-phase-label {
    color: #00d9ff;
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 14px;
}

.combined-value {
    color: #ffffff;
    font-size: 24px;
    font-weight: 700;
    margin-top: 8px;
}

.combined-unit {
    color: #8ca8c0;
    font-size: 15px;
    font-weight: 500;
}


/* POWER */

.power-card {
    background: #0b1a2b;
    border: 1px solid #1b405c;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}

.power-label {
    color: #8ca8c0;
    font-size: 14px;
}

.power-number {
    color: #ffffff;
    font-size: 26px;
    font-weight: 700;
    margin-top: 10px;
}

.power-total {
    border: 1px solid #00bfff;
}


/* STATISTICS */

.stat-card {
    background: #0b1a2b;
    border: 1px solid #1b405c;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}

.stat-label {
    color: #8ca8c0;
    font-size: 13px;
    font-weight: 600;
}

.stat-number {
    color: #00d9ff;
    font-size: 28px;
    font-weight: 700;
    margin-top: 8px;
}


/* INFO */

.info-card {
    background: #0b1a2b;
    border: 1px solid #1b405c;
    border-radius: 12px;
    padding: 18px;
    margin-top: 15px;
}

.info-label {
    color: #8ca8c0;
    font-size: 13px;
}

.info-value {
    color: #ffffff;
    font-size: 22px;
    font-weight: 700;
    margin-top: 6px;
}


/* REMOVE DEFAULT */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

</style>
""")


# =========================================================
# SUPABASE CONNECTION
# =========================================================

SUPABASE_URL = "https://yjlgeqynwggnxvhgjtco.supabase.co"


def get_supabase_public_key():

    # Local development: use the Publishable/anon key only.
    key = os.environ.get("SUPABASE_PUBLIC_KEY")

    if key:
        return key

    # Streamlit Cloud: store the same public key in Secrets.
    try:
        key = st.secrets.get("SUPABASE_PUBLIC_KEY")
    except Exception:
        key = None

    return key


SUPABASE_PUBLIC_KEY = get_supabase_public_key()


if not SUPABASE_PUBLIC_KEY:

    st.error(
        "ไม่พบ SUPABASE_PUBLIC_KEY — กรุณาตั้งค่า Environment Variable "
        "หรือ Streamlit Secret ชื่อ SUPABASE_PUBLIC_KEY"
    )

    st.stop()


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_PUBLIC_KEY
)


# =========================================================
# SUPABASE DATA HELPERS
# =========================================================

SUPABASE_PAGE_SIZE = 1000


DATA_COLUMNS = [
    "id",
    "timestamp",
    "v1",
    "v2",
    "v3",
    "v12",
    "v23",
    "v31",
    "i1",
    "i2",
    "i3",
    "p1",
    "p2",
    "p3",
    "total_power",
    "power_factor",
    "frequency"
]


def normalize_data(data):

    if not data:
        return pd.DataFrame(columns=DATA_COLUMNS)

    df = pd.DataFrame(data)

    for column in DATA_COLUMNS:
        if column not in df.columns:
            df[column] = None

    df = df[DATA_COLUMNS].copy()

    # Supabase returns timestamptz in UTC.
    # Convert to Thailand time for the dashboard.
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
        utc=True
    ).dt.tz_convert("Asia/Bangkok")

    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    return df


def load_all_data():

    try:

        rows = []
        offset = 0

        while True:

            response = (
                supabase
                .table("energy_data")
                .select("*")
                .order("timestamp", desc=False)
                .range(
                    offset,
                    offset + SUPABASE_PAGE_SIZE - 1
                )
                .execute()
            )

            batch = response.data or []
            rows.extend(batch)

            if len(batch) < SUPABASE_PAGE_SIZE:
                break

            offset += SUPABASE_PAGE_SIZE

        return normalize_data(rows)

    except Exception as e:

        st.error(
            f"Supabase Error: {e}"
        )

        return pd.DataFrame(columns=DATA_COLUMNS)


def load_last_24h():

    try:

        latest_response = (
            supabase
            .table("energy_data")
            .select("timestamp")
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )

        latest_rows = latest_response.data or []

        if not latest_rows:
            return pd.DataFrame(columns=DATA_COLUMNS)

        max_timestamp = pd.to_datetime(
            latest_rows[0]["timestamp"],
            utc=True
        )

        min_timestamp = (
            max_timestamp - timedelta(hours=24)
        )

        rows = []
        offset = 0

        while True:

            response = (
                supabase
                .table("energy_data")
                .select("*")
                .gte(
                    "timestamp",
                    min_timestamp.isoformat()
                )
                .lte(
                    "timestamp",
                    max_timestamp.isoformat()
                )
                .order("timestamp", desc=False)
                .range(
                    offset,
                    offset + SUPABASE_PAGE_SIZE - 1
                )
                .execute()
            )

            batch = response.data or []
            rows.extend(batch)

            if len(batch) < SUPABASE_PAGE_SIZE:
                break

            offset += SUPABASE_PAGE_SIZE

        return normalize_data(rows)

    except Exception as e:

        st.error(
            f"Supabase Error: {e}"
        )

        return pd.DataFrame(columns=DATA_COLUMNS)


# =========================================================
# HELPER
# =========================================================

def kw(value):

    if pd.isna(value):
        return 0.0

    return float(value) / 1000


# =========================================================
# COMBINED PHASE CALCULATION
# =========================================================

def calculate_combined_phase(latest):

    # -----------------------------------------------------
    # LINE-TO-LINE VOLTAGE
    # อ่านโดยตรงจาก LEOS IPM310
    # -----------------------------------------------------

    v12 = float(latest["v12"])
    v23 = float(latest["v23"])
    v31 = float(latest["v31"])


    # -----------------------------------------------------
    # CURRENT
    #
    # IPM310 มี I1 / I2 / I3
    # ไม่มีค่า I12 / I23 / I31 โดยตรง
    #
    # จึงคำนวณค่าเฉลี่ยของ 2 เฟส
    # -----------------------------------------------------

    i1 = float(latest["i1"])
    i2 = float(latest["i2"])
    i3 = float(latest["i3"])

    a12 = (i1 + i2) / 2
    a23 = (i2 + i3) / 2
    a31 = (i3 + i1) / 2


    # -----------------------------------------------------
    # ACTIVE POWER
    #
    # P1 / P2 / P3 ใน Database เป็น W
    #
    # รวมกำลังไฟฟ้าของแต่ละคู่เฟส
    # -----------------------------------------------------

    p1 = float(latest["p1"])
    p2 = float(latest["p2"])
    p3 = float(latest["p3"])

    w12 = p1 + p2
    w23 = p2 + p3
    w31 = p3 + p1


    return {

        "v12": v12,
        "a12": a12,
        "w12": w12,

        "v23": v23,
        "a23": a23,
        "w23": w23,

        "v31": v31,
        "a31": a31,
        "w31": w31

    }


# =========================================================
# ADD COMBINED PHASE COLUMNS
# =========================================================

def add_combined_phase_columns(data):

    result = data.copy()

    result["a12"] = (
        result["i1"] +
        result["i2"]
    ) / 2

    result["a23"] = (
        result["i2"] +
        result["i3"]
    ) / 2

    result["a31"] = (
        result["i3"] +
        result["i1"]
    ) / 2

    result["w12"] = (
        result["p1"] +
        result["p2"]
    )

    result["w23"] = (
        result["p2"] +
        result["p3"]
    )

    result["w31"] = (
        result["p3"] +
        result["p1"]
    )

    return result


# =========================================================
# CHART DATA
# =========================================================

def chart_data(
    data,
    max_points=MAX_CHART_POINTS
):

    if len(data) <= max_points:
        return data.copy()

    step = max(
        1,
        len(data) // max_points
    )

    return data.iloc[::step].copy()


# =========================================================
# POWER CHART
# =========================================================

def create_power_chart(
    data,
    title
):

    plot_df = chart_data(
        data
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=plot_df["timestamp"],
            y=plot_df["power_kw"],
            mode="lines",
            name="Total Power",
            line=dict(
                width=2
            )
        )
    )

    fig.update_layout(

        title=title,

        height=420,

        paper_bgcolor="#0b1a2b",

        plot_bgcolor="#0b1a2b",

        font=dict(
            color="#d9ecff"
        ),

        margin=dict(
            l=30,
            r=30,
            t=50,
            b=30
        ),

        xaxis=dict(
            title="Time",
            gridcolor="#18364d"
        ),

        yaxis=dict(
            title="Power (kW)",
            gridcolor="#18364d"
        ),

        hovermode="x unified"
    )

    return fig


# =========================================================
# GENERATE STANDARD TABLE
# =========================================================

def make_data_table(data):

    table = (
        data
        .sort_values(
            "timestamp",
            ascending=False
        )
        .copy()
    )

    table["p1"] /= 1000
    table["p2"] /= 1000
    table["p3"] /= 1000

    table["power_kw"] = (
        table["total_power"] / 1000
    )

    table["timestamp"] = (
        table["timestamp"]
        .dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    table = table[
        [
            "timestamp",

            "v1",
            "v2",
            "v3",

            "i1",
            "i2",
            "i3",

            "p1",
            "p2",
            "p3",

            "power_kw",

            "power_factor",
            "frequency"
        ]
    ].copy()

    table.columns = [

        "Timestamp",

        "V1 (V)",
        "V2 (V)",
        "V3 (V)",

        "I1 (A)",
        "I2 (A)",
        "I3 (A)",

        "P1 (kW)",
        "P2 (kW)",
        "P3 (kW)",

        "Total (kW)",

        "PF",

        "Hz"
    ]

    return table


# =========================================================
# GENERATE COMBINED PHASE TABLE
# =========================================================

def make_combined_phase_table(data):

    table = add_combined_phase_columns(
        data
    )

    table = (
        table
        .sort_values(
            "timestamp",
            ascending=False
        )
        .copy()
    )

    table = table[
        [
            "timestamp",

            "v12",
            "a12",
            "w12",

            "v23",
            "a23",
            "w23",

            "v31",
            "a31",
            "w31"
        ]
    ].copy()

    table.columns = [

        "Timestamp",

        "V12 (V)",
        "A12 (A)",
        "W12 (W)",

        "V23 (V)",
        "A23 (A)",
        "W23 (W)",

        "V31 (V)",
        "A31 (A)",
        "W31 (W)"

    ]

    return table


# =========================================================
# GRAPH: VOLTAGE
# =========================================================

def create_voltage_chart(data):

    plot_df = chart_data(data)

    fig = go.Figure()

    for col, name in [
        ("v1", "V1"),
        ("v2", "V2"),
        ("v3", "V3")
    ]:

        fig.add_trace(
            go.Scatter(
                x=plot_df["timestamp"],
                y=plot_df[col],
                mode="lines",
                name=name
            )
        )

    fig.update_layout(

        height=400,

        paper_bgcolor="#0b1a2b",

        plot_bgcolor="#0b1a2b",

        font=dict(
            color="#d9ecff"
        ),

        xaxis=dict(
            title="Time",
            gridcolor="#18364d"
        ),

        yaxis=dict(
            title="Voltage (V)",
            gridcolor="#18364d"
        ),

        hovermode="x unified"
    )

    return fig


# =========================================================
# GRAPH: CURRENT
# =========================================================

def create_current_chart(data):

    plot_df = chart_data(data)

    fig = go.Figure()

    for col, name in [
        ("i1", "I1"),
        ("i2", "I2"),
        ("i3", "I3")
    ]:

        fig.add_trace(
            go.Scatter(
                x=plot_df["timestamp"],
                y=plot_df[col],
                mode="lines",
                name=name
            )
        )

    fig.update_layout(

        height=400,

        paper_bgcolor="#0b1a2b",

        plot_bgcolor="#0b1a2b",

        font=dict(
            color="#d9ecff"
        ),

        xaxis=dict(
            title="Time",
            gridcolor="#18364d"
        ),

        yaxis=dict(
            title="Current (A)",
            gridcolor="#18364d"
        ),

        hovermode="x unified"
    )

    return fig


# =========================================================
# GRAPH: COMBINED PHASE
# =========================================================

def create_combined_phase_chart(data):

    plot_df = add_combined_phase_columns(
        chart_data(data)
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=plot_df["timestamp"],
            y=plot_df["w12"],
            mode="lines",
            name="W12"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=plot_df["timestamp"],
            y=plot_df["w23"],
            mode="lines",
            name="W23"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=plot_df["timestamp"],
            y=plot_df["w31"],
            mode="lines",
            name="W31"
        )
    )

    fig.update_layout(

        height=400,

        paper_bgcolor="#0b1a2b",

        plot_bgcolor="#0b1a2b",

        font=dict(
            color="#d9ecff"
        ),

        xaxis=dict(
            title="Time",
            gridcolor="#18364d"
        ),

        yaxis=dict(
            title="Combined Power (W)",
            gridcolor="#18364d"
        ),

        hovermode="x unified"
    )

    return fig


# =========================================================
# DASHBOARD
# =========================================================

@st.fragment(
    run_every="2s"
)

def dashboard():

    # =====================================================
    # HEADER
    # =====================================================

    st.html("""
    <div class="scada-header">

        <div class="scada-title">
            ⚡ LEOS IPM310 — ENERGY MONITORING SCADA
        </div>

        <div class="scada-subtitle">

            3-PHASE ELECTRICAL ENERGY MONITORING SYSTEM

            &nbsp;&nbsp;|&nbsp;&nbsp;

            <span class="online">
                ● SYSTEM ONLINE
            </span>

        </div>

    </div>
    """)


    # =====================================================
    # MENU
    # =====================================================

    st.html("""
    <div class="section-title">
        DASHBOARD MENU
    </div>
    """)


    page = st.radio(

        "เลือกหน้าการแสดงผล",

        [
            "REALTIME",
            "HOURLY",
            "DAILY",
            "MONTHLY",
            "YEARLY"
        ],

        horizontal=True,

        label_visibility="collapsed",

        key="dashboard_page"

    )


    # =====================================================
    # LOAD DATA
    # =====================================================

    if page == "REALTIME":

        df = load_last_24h()

    else:

        df = load_all_data()


    # =====================================================
    # NO DATA
    # =====================================================

    if df.empty:

        st.warning(
            "ยังไม่มีข้อมูลจาก LEOS IPM310"
        )

        st.info(
            "กรุณาเปิด Logger ก่อน"
        )

        return


    # =====================================================
    # REALTIME
    # =====================================================

    if page == "REALTIME":

        latest = df.iloc[-1]

        v1 = float(latest["v1"])
        v2 = float(latest["v2"])
        v3 = float(latest["v3"])

        i1 = float(latest["i1"])
        i2 = float(latest["i2"])
        i3 = float(latest["i3"])

        p1 = kw(latest["p1"])
        p2 = kw(latest["p2"])
        p3 = kw(latest["p3"])

        total_power = kw(
            latest["total_power"]
        )

        pf = float(
            latest["power_factor"]
        )

        frequency = float(
            latest["frequency"]
        )

        last_update = latest[
            "timestamp"
        ]


        # -------------------------------------------------
        # COMBINED PHASE VALUES
        # -------------------------------------------------

        combined = calculate_combined_phase(
            latest
        )

        v12 = combined["v12"]
        a12 = combined["a12"]
        w12 = combined["w12"]

        v23 = combined["v23"]
        a23 = combined["a23"]
        w23 = combined["w23"]

        v31 = combined["v31"]
        a31 = combined["a31"]
        w31 = combined["w31"]


        # -------------------------------------------------
        # SYSTEM STATUS
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            SYSTEM STATUS
        </div>
        """)

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.html(
                f"""
                <div class="main-card">

                    <div class="card-label">
                        TOTAL POWER
                    </div>

                    <div class="card-number">
                        {total_power:.2f}

                        <span class="card-unit">
                            kW
                        </span>

                    </div>

                </div>
                """
            )

        with c2:

            st.html(
                f"""
                <div class="main-card">

                    <div class="card-label">
                        POWER FACTOR
                    </div>

                    <div class="card-number">
                        {pf:.3f}
                    </div>

                </div>
                """
            )

        with c3:

            st.html(
                f"""
                <div class="main-card">

                    <div class="card-label">
                        FREQUENCY
                    </div>

                    <div class="card-number">

                        {frequency:.2f}

                        <span class="card-unit">
                            Hz
                        </span>

                    </div>

                </div>
                """
            )

        with c4:

            st.html(
                f"""
                <div class="status-card">

                    <div class="status-online">
                        ● SYSTEM ONLINE
                    </div>

                    <div class="update-label">
                        Last Update
                    </div>

                    <div class="update-value">

                        {
                            last_update.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        }

                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # VOLTAGE
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            VOLTAGE
        </div>
        """)

        v1c, v2c, v3c = st.columns(3)

        with v1c:

            st.html(
                f"""
                <div class="phase-card">

                    <div class="phase-label">
                        PHASE 1 — V1
                    </div>

                    <div class="phase-number">
                        {v1:.2f} V
                    </div>

                </div>
                """
            )

        with v2c:

            st.html(
                f"""
                <div class="phase-card">

                    <div class="phase-label">
                        PHASE 2 — V2
                    </div>

                    <div class="phase-number">
                        {v2:.2f} V
                    </div>

                </div>
                """
            )

        with v3c:

            st.html(
                f"""
                <div class="phase-card">

                    <div class="phase-label">
                        PHASE 3 — V3
                    </div>

                    <div class="phase-number">
                        {v3:.2f} V
                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # CURRENT
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            CURRENT
        </div>
        """)

        i1c, i2c, i3c = st.columns(3)

        with i1c:

            st.html(
                f"""
                <div class="phase-card">

                    <div class="phase-label">
                        PHASE 1 — I1
                    </div>

                    <div class="phase-number">
                        {i1:.2f} A
                    </div>

                </div>
                """
            )

        with i2c:

            st.html(
                f"""
                <div class="phase-card">

                    <div class="phase-label">
                        PHASE 2 — I2
                    </div>

                    <div class="phase-number">
                        {i2:.2f} A
                    </div>

                </div>
                """
            )

        with i3c:

            st.html(
                f"""
                <div class="phase-card">

                    <div class="phase-label">
                        PHASE 3 — I3
                    </div>

                    <div class="phase-number">
                        {i3:.2f} A
                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # COMBINED PHASE
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            COMBINED PHASE
        </div>
        """)

        st.caption(
            "V = ค่าที่วัดโดย LEOS IPM310 | "
            "A และ W = ค่าคำนวณจาก I1/I2/I3 และ P1/P2/P3"
        )


        cp1, cp2, cp3 = st.columns(3)


        # -------------------------------------------------
        # PHASE 1-2
        # -------------------------------------------------

        with cp1:

            st.html(
                f"""
                <div class="combined-phase-card">

                    <div class="combined-phase-label">
                        PHASE 1-2
                    </div>

                    <div class="combined-value">
                        {v12:.2f}
                        <span class="combined-unit">
                            V
                        </span>
                    </div>

                    <div class="combined-value">
                        {a12:.2f}
                        <span class="combined-unit">
                            A
                        </span>
                    </div>

                    <div class="combined-value">
                        {w12:.2f}
                        <span class="combined-unit">
                            W
                        </span>
                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # PHASE 2-3
        # -------------------------------------------------

        with cp2:

            st.html(
                f"""
                <div class="combined-phase-card">

                    <div class="combined-phase-label">
                        PHASE 2-3
                    </div>

                    <div class="combined-value">
                        {v23:.2f}
                        <span class="combined-unit">
                            V
                        </span>
                    </div>

                    <div class="combined-value">
                        {a23:.2f}
                        <span class="combined-unit">
                            A
                        </span>
                    </div>

                    <div class="combined-value">
                        {w23:.2f}
                        <span class="combined-unit">
                            W
                        </span>
                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # PHASE 3-1
        # -------------------------------------------------

        with cp3:

            st.html(
                f"""
                <div class="combined-phase-card">

                    <div class="combined-phase-label">
                        PHASE 3-1
                    </div>

                    <div class="combined-value">
                        {v31:.2f}
                        <span class="combined-unit">
                            V
                        </span>
                    </div>

                    <div class="combined-value">
                        {a31:.2f}
                        <span class="combined-unit">
                            A
                        </span>
                    </div>

                    <div class="combined-value">
                        {w31:.2f}
                        <span class="combined-unit">
                            W
                        </span>
                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # ACTIVE POWER
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            ACTIVE POWER
        </div>
        """)

        p1c, p2c, p3c, ptc = st.columns(4)

        with p1c:

            st.html(
                f"""
                <div class="power-card">

                    <div class="power-label">
                        P1
                    </div>

                    <div class="power-number">
                        {p1:.2f} kW
                    </div>

                </div>
                """
            )

        with p2c:

            st.html(
                f"""
                <div class="power-card">

                    <div class="power-label">
                        P2
                    </div>

                    <div class="power-number">
                        {p2:.2f} kW
                    </div>

                </div>
                """
            )

        with p3c:

            st.html(
                f"""
                <div class="power-card">

                    <div class="power-label">
                        P3
                    </div>

                    <div class="power-number">
                        {p3:.2f} kW
                    </div>

                </div>
                """
            )

        with ptc:

            st.html(
                f"""
                <div class="power-card power-total">

                    <div class="power-label">
                        TOTAL
                    </div>

                    <div class="power-number">
                        {total_power:.2f} kW
                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # 24 HOUR STATISTICS
        # -------------------------------------------------

        df24 = df.copy()

        df24["power_kw"] = (
            df24["total_power"] / 1000
        )

        max_power = df24[
            "power_kw"
        ].max()

        min_power = df24[
            "power_kw"
        ].min()

        avg_power = df24[
            "power_kw"
        ].mean()


        st.html("""
        <div class="section-title">
            POWER STATISTICS — LAST 24 HOURS
        </div>
        """)

        s1, s2, s3 = st.columns(3)

        with s1:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        MAX POWER
                    </div>

                    <div class="stat-number">
                        {max_power:.2f} kW
                    </div>

                </div>
                """
            )

        with s2:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        MIN POWER
                    </div>

                    <div class="stat-number">
                        {min_power:.2f} kW
                    </div>

                </div>
                """
            )

        with s3:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        AVERAGE POWER
                    </div>

                    <div class="stat-number">
                        {avg_power:.2f} kW
                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # POWER TREND
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            POWER TREND — LAST 24 HOURS
        </div>
        """)

        fig_power = create_power_chart(
            df24,
            "Power Trend — Last 24 Hours"
        )

        st.plotly_chart(
            fig_power,
            width="stretch",
            key="realtime_power_chart"
        )


        # -------------------------------------------------
        # VOLTAGE TREND
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            VOLTAGE TREND — LAST 24 HOURS
        </div>
        """)

        fig_voltage = create_voltage_chart(
            df24
        )

        st.plotly_chart(
            fig_voltage,
            width="stretch",
            key="realtime_voltage_chart"
        )


        # -------------------------------------------------
        # CURRENT TREND
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            CURRENT TREND — LAST 24 HOURS
        </div>
        """)

        fig_current = create_current_chart(
            df24
        )

        st.plotly_chart(
            fig_current,
            width="stretch",
            key="realtime_current_chart"
        )


        # -------------------------------------------------
        # COMBINED PHASE POWER TREND
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            COMBINED PHASE POWER TREND — LAST 24 HOURS
        </div>
        """)

        fig_combined = create_combined_phase_chart(
            df24
        )

        st.plotly_chart(
            fig_combined,
            width="stretch",
            key="realtime_combined_phase_chart"
        )


        # -------------------------------------------------
        # FULL 24 HOUR TABLE
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            REALTIME DATA — FULL 24 HOURS
        </div>
        """)

        recent_display = make_data_table(
            df24
        )

        first_ts = (
            df24["timestamp"]
            .min()
            .strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        last_ts = (
            df24["timestamp"]
            .max()
            .strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        st.caption(
            f"ข้อมูลครบทุก Record ในช่วง 24 ชั่วโมง | "
            f"{len(recent_display):,} records | "
            f"{first_ts} → {last_ts}"
        )

        st.dataframe(
            recent_display,
            width="stretch",
            height=700,
            hide_index=True
        )


        # -------------------------------------------------
        # COMBINED PHASE TABLE
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            COMBINED PHASE DATA — FULL 24 HOURS
        </div>
        """)

        combined_display = make_combined_phase_table(
            df24
        )

        st.caption(
            "V12 / V23 / V31 = ค่าวัดจาก LEOS IPM310 | "
            "A และ W = ค่าคำนวณ"
        )

        st.dataframe(
            combined_display,
            width="stretch",
            height=500,
            hide_index=True
        )


        # -------------------------------------------------
        # CSV
        # -------------------------------------------------

        csv_data = (
            recent_display
            .to_csv(index=False)
            .encode("utf-8-sig")
        )

        st.download_button(
            "ดาวน์โหลดข้อมูล 24 ชั่วโมง CSV",
            data=csv_data,
            file_name="LEOS_IPM310_last_24h.csv",
            mime="text/csv",
            key="realtime_csv"
        )


        combined_csv = (
            combined_display
            .to_csv(index=False)
            .encode("utf-8-sig")
        )

        st.download_button(
            "ดาวน์โหลด Combined Phase 24 ชั่วโมง CSV",
            data=combined_csv,
            file_name="LEOS_IPM310_combined_phase_24h.csv",
            mime="text/csv",
            key="realtime_combined_csv"
        )


    # =====================================================
    # HOURLY
    # =====================================================

    elif page == "HOURLY":

        st.html("""
        <div class="section-title">
            HOURLY ENERGY MONITORING
        </div>
        """)


        # -------------------------------------------------
        # SELECT DATE
        # -------------------------------------------------

        min_date = (
            df["timestamp"]
            .dt.date
            .min()
        )

        max_date = (
            df["timestamp"]
            .dt.date
            .max()
        )

        selected_date = st.date_input(

            "เลือกวันที่",

            value=max_date,

            min_value=min_date,

            max_value=max_date,

            format="DD/MM/YYYY",

            key="hourly_date"

        )


        # -------------------------------------------------
        # AVAILABLE HOURS
        # -------------------------------------------------

        day_data = df[
            df["timestamp"]
            .dt.date
            == selected_date
        ].copy()

        if day_data.empty:

            st.warning(
                "ไม่มีข้อมูลของวันที่เลือก"
            )

            return


        hourly_hours = sorted(
            day_data[
                "timestamp"
            ]
            .dt
            .hour
            .unique()
        )


        # -------------------------------------------------
        # SELECT HOUR
        # -------------------------------------------------

        selected_hour = st.selectbox(

            "เลือกชั่วโมง",

            hourly_hours,

            format_func=lambda x:
                f"{x:02d}:00 - {x:02d}:59",

            key="hourly_select"

        )


        # -------------------------------------------------
        # FILTER HOUR
        # -------------------------------------------------

        hourly = day_data[

            day_data[
                "timestamp"
            ]
            .dt
            .hour
            == selected_hour

        ].copy()


        if hourly.empty:

            st.warning(
                "ไม่มีข้อมูลในชั่วโมงที่เลือก"
            )

            return


        # -------------------------------------------------
        # POWER
        # -------------------------------------------------

        hourly["power_kw"] = (
            hourly["total_power"] / 1000
        )


        # -------------------------------------------------
        # STATISTICS
        # -------------------------------------------------

        hour_avg = (
            hourly["power_kw"].mean()
        )

        hour_max = (
            hourly["power_kw"].max()
        )

        hour_min = (
            hourly["power_kw"].min()
        )

        hour_pf = (
            hourly["power_factor"].mean()
        )


        c1, c2, c3, c4 = st.columns(4)


        with c1:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        HOUR AVG POWER
                    </div>

                    <div class="stat-number">
                        {hour_avg:.2f} kW
                    </div>

                </div>
                """
            )


        with c2:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        HOUR MAX POWER
                    </div>

                    <div class="stat-number">
                        {hour_max:.2f} kW
                    </div>

                </div>
                """
            )


        with c3:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        HOUR MIN POWER
                    </div>

                    <div class="stat-number">
                        {hour_min:.2f} kW
                    </div>

                </div>
                """
            )


        with c4:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        HOUR AVG PF
                    </div>

                    <div class="stat-number">
                        {hour_pf:.3f}
                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # INFORMATION
        # -------------------------------------------------

        h1, h2, h3 = st.columns(3)


        with h1:

            st.html(
                f"""
                <div class="info-card">

                    <div class="info-label">
                        SELECTED DATE
                    </div>

                    <div class="info-value">
                        {selected_date.strftime("%d/%m/%Y")}
                    </div>

                </div>
                """
            )


        with h2:

            st.html(
                f"""
                <div class="info-card">

                    <div class="info-label">
                        SELECTED HOUR
                    </div>

                    <div class="info-value">
                        {selected_hour:02d}:00 - {selected_hour:02d}:59
                    </div>

                </div>
                """
            )


        with h3:

            st.html(
                f"""
                <div class="info-card">

                    <div class="info-label">
                        DATA RECORDS
                    </div>

                    <div class="info-value">
                        {len(hourly):,}
                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # TIME RANGE
        # -------------------------------------------------

        first_hour = (
            hourly["timestamp"]
            .min()
            .strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        last_hour = (
            hourly["timestamp"]
            .max()
            .strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        st.caption(
            f"ช่วงข้อมูล: {first_hour} → {last_hour} | "
            f"ทั้งหมด {len(hourly):,} records"
        )


        # -------------------------------------------------
        # HOURLY POWER
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            HOURLY POWER TREND
        </div>
        """)

        fig_hour_power = create_power_chart(
            hourly,
            f"Power Trend — "
            f"{selected_date.strftime('%d/%m/%Y')} "
            f"{selected_hour:02d}:00"
        )

        st.plotly_chart(
            fig_hour_power,
            width="stretch",
            key="hourly_power_chart"
        )


        # -------------------------------------------------
        # HOURLY VOLTAGE
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            HOURLY VOLTAGE TREND
        </div>
        """)

        fig_hour_voltage = create_voltage_chart(
            hourly
        )

        st.plotly_chart(
            fig_hour_voltage,
            width="stretch",
            key="hourly_voltage_chart"
        )


        # -------------------------------------------------
        # HOURLY CURRENT
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            HOURLY CURRENT TREND
        </div>
        """)

        fig_hour_current = create_current_chart(
            hourly
        )

        st.plotly_chart(
            fig_hour_current,
            width="stretch",
            key="hourly_current_chart"
        )


        # -------------------------------------------------
        # HOURLY COMBINED PHASE POWER
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            HOURLY COMBINED PHASE POWER
        </div>
        """)

        fig_hour_combined = create_combined_phase_chart(
            hourly
        )

        st.plotly_chart(
            fig_hour_combined,
            width="stretch",
            key="hourly_combined_phase_chart"
        )


        # -------------------------------------------------
        # HOURLY TABLE
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            HOURLY DATA — ALL RECORDS
        </div>
        """)

        hourly_table = make_data_table(
            hourly
        )

        st.dataframe(
            hourly_table,
            width="stretch",
            height=700,
            hide_index=True
        )


        # -------------------------------------------------
        # HOURLY COMBINED PHASE TABLE
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            HOURLY COMBINED PHASE — ALL RECORDS
        </div>
        """)

        hourly_combined_table = (
            make_combined_phase_table(
                hourly
            )
        )

        st.dataframe(
            hourly_combined_table,
            width="stretch",
            height=500,
            hide_index=True
        )


        # -------------------------------------------------
        # HOURLY CSV
        # -------------------------------------------------

        hourly_csv = (
            hourly_table
            .to_csv(index=False)
            .encode("utf-8-sig")
        )

        st.download_button(

            "ดาวน์โหลดข้อมูลรายชั่วโมง CSV",

            data=hourly_csv,

            file_name=(
                f"LEOS_IPM310_"
                f"{selected_date}_"
                f"{selected_hour:02d}00-"
                f"{selected_hour:02d}59.csv"
            ),

            mime="text/csv",

            key="hourly_csv"

        )


        hourly_combined_csv = (
            hourly_combined_table
            .to_csv(index=False)
            .encode("utf-8-sig")
        )

        st.download_button(

            "ดาวน์โหลด Combined Phase รายชั่วโมง CSV",

            data=hourly_combined_csv,

            file_name=(
                f"LEOS_IPM310_combined_"
                f"{selected_date}_"
                f"{selected_hour:02d}00-"
                f"{selected_hour:02d}59.csv"
            ),

            mime="text/csv",

            key="hourly_combined_csv"

        )


    # =====================================================
    # DAILY
    # =====================================================

    elif page == "DAILY":

        st.html("""
        <div class="section-title">
            DAILY ENERGY MONITORING
        </div>
        """)


        # -------------------------------------------------
        # SELECT DATE
        # -------------------------------------------------

        min_date = (
            df["timestamp"]
            .dt.date
            .min()
        )

        max_date = (
            df["timestamp"]
            .dt.date
            .max()
        )

        selected_date = st.date_input(

            "เลือกวันที่",

            value=max_date,

            min_value=min_date,

            max_value=max_date,

            format="DD/MM/YYYY",

            key="daily_date"

        )


        daily = df[
            df["timestamp"]
            .dt.date
            == selected_date
        ].copy()


        if daily.empty:

            st.warning(
                "ไม่มีข้อมูลของวันที่เลือก"
            )

            return


        # -------------------------------------------------
        # POWER
        # -------------------------------------------------

        daily["power_kw"] = (
            daily["total_power"] / 1000
        )


        max_power = (
            daily["power_kw"].max()
        )

        min_power = (
            daily["power_kw"].min()
        )

        avg_power = (
            daily["power_kw"].mean()
        )

        avg_pf = (
            daily["power_factor"].mean()
        )


        c1, c2, c3, c4 = st.columns(4)


        with c1:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        MAX POWER
                    </div>

                    <div class="stat-number">
                        {max_power:.2f} kW
                    </div>

                </div>
                """
            )


        with c2:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        MIN POWER
                    </div>

                    <div class="stat-number">
                        {min_power:.2f} kW
                    </div>

                </div>
                """
            )


        with c3:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        AVERAGE POWER
                    </div>

                    <div class="stat-number">
                        {avg_power:.2f} kW
                    </div>

                </div>
                """
            )


        with c4:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        AVERAGE PF
                    </div>

                    <div class="stat-number">
                        {avg_pf:.3f}
                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # DAILY INFO
        # -------------------------------------------------

        d1, d2 = st.columns(2)


        with d1:

            st.html(
                f"""
                <div class="info-card">

                    <div class="info-label">
                        SELECTED DATE
                    </div>

                    <div class="info-value">
                        {selected_date.strftime("%d/%m/%Y")}
                    </div>

                </div>
                """
            )


        with d2:

            st.html(
                f"""
                <div class="info-card">

                    <div class="info-label">
                        DATA RECORDS
                    </div>

                    <div class="info-value">
                        {len(daily):,}
                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # POWER GRAPH
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            DAILY POWER TREND
        </div>
        """)

        fig_daily = create_power_chart(
            daily,
            "Power Trend — Daily"
        )

        st.plotly_chart(
            fig_daily,
            width="stretch",
            key="daily_power_chart"
        )


        # -------------------------------------------------
        # VOLTAGE GRAPH
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            DAILY VOLTAGE TREND
        </div>
        """)

        fig_daily_v = create_voltage_chart(
            daily
        )

        st.plotly_chart(
            fig_daily_v,
            width="stretch",
            key="daily_voltage_chart"
        )


        # -------------------------------------------------
        # CURRENT GRAPH
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            DAILY CURRENT TREND
        </div>
        """)

        fig_daily_i = create_current_chart(
            daily
        )

        st.plotly_chart(
            fig_daily_i,
            width="stretch",
            key="daily_current_chart"
        )


        # -------------------------------------------------
        # DAILY COMBINED PHASE POWER
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            DAILY COMBINED PHASE POWER
        </div>
        """)

        fig_daily_combined = create_combined_phase_chart(
            daily
        )

        st.plotly_chart(
            fig_daily_combined,
            width="stretch",
            key="daily_combined_phase_chart"
        )


        # -------------------------------------------------
        # DAILY TABLE
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            DAILY DATA — ALL RECORDS
        </div>
        """)

        daily_table = make_data_table(
            daily
        )

        st.dataframe(
            daily_table,
            width="stretch",
            height=700,
            hide_index=True
        )


        # -------------------------------------------------
        # DAILY COMBINED PHASE TABLE
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            DAILY COMBINED PHASE — ALL RECORDS
        </div>
        """)

        daily_combined_table = (
            make_combined_phase_table(
                daily
            )
        )

        st.dataframe(
            daily_combined_table,
            width="stretch",
            height=500,
            hide_index=True
        )


        # -------------------------------------------------
        # DAILY CSV
        # -------------------------------------------------

        daily_csv = (
            daily_table
            .to_csv(index=False)
            .encode("utf-8-sig")
        )

        st.download_button(

            "ดาวน์โหลดข้อมูลรายวัน CSV",

            data=daily_csv,

            file_name=(
                f"LEOS_IPM310_"
                f"{selected_date}.csv"
            ),

            mime="text/csv",

            key="daily_csv"

        )


        daily_combined_csv = (
            daily_combined_table
            .to_csv(index=False)
            .encode("utf-8-sig")
        )

        st.download_button(

            "ดาวน์โหลด Combined Phase รายวัน CSV",

            data=daily_combined_csv,

            file_name=(
                f"LEOS_IPM310_combined_"
                f"{selected_date}.csv"
            ),

            mime="text/csv",

            key="daily_combined_csv"

        )


    # =====================================================
    # MONTHLY
    # =====================================================

    elif page == "MONTHLY":

        st.html("""
        <div class="section-title">
            MONTHLY ENERGY MONITORING
        </div>
        """)


        df_month = df.copy()

        df_month["month_period"] = (
            df_month["timestamp"]
            .dt.to_period("M")
        )


        months = sorted(

            df_month[
                "month_period"
            ].unique(),

            reverse=True

        )


        if not months:

            st.warning(
                "ยังไม่มีข้อมูลรายเดือน"
            )

            return


        selected_month = st.selectbox(

            "เลือกเดือน",

            months,

            format_func=lambda x:
                x.strftime("%B %Y"),

            key="monthly_select"

        )


        monthly = df_month[
            df_month["month_period"]
            == selected_month
        ].copy()


        if monthly.empty:

            st.warning(
                "ไม่มีข้อมูลของเดือนนี้"
            )

            return


        monthly["power_kw"] = (
            monthly["total_power"]
            / 1000
        )


        monthly["day"] = (
            monthly["timestamp"]
            .dt.date
        )


        daily_summary = (

            monthly

            .groupby("day")

            .agg(

                avg_power=(
                    "power_kw",
                    "mean"
                ),

                max_power=(
                    "power_kw",
                    "max"
                ),

                min_power=(
                    "power_kw",
                    "min"
                ),

                avg_pf=(
                    "power_factor",
                    "mean"
                ),

                records=(
                    "power_kw",
                    "count"
                )

            )

            .reset_index()

        )


        month_avg = (
            monthly["power_kw"].mean()
        )

        month_max = (
            monthly["power_kw"].max()
        )

        month_min = (
            monthly["power_kw"].min()
        )

        month_pf = (
            monthly["power_factor"].mean()
        )


        c1, c2, c3, c4 = st.columns(4)


        with c1:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        MONTH AVG POWER
                    </div>

                    <div class="stat-number">
                        {month_avg:.2f} kW
                    </div>

                </div>
                """
            )


        with c2:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        MONTH MAX POWER
                    </div>

                    <div class="stat-number">
                        {month_max:.2f} kW
                    </div>

                </div>
                """
            )


        with c3:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        MONTH MIN POWER
                    </div>

                    <div class="stat-number">
                        {month_min:.2f} kW
                    </div>

                </div>
                """
            )


        with c4:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        MONTH AVG PF
                    </div>

                    <div class="stat-number">
                        {month_pf:.3f}
                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # MONTHLY GRAPH
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            MONTHLY POWER TREND
        </div>
        """)

        fig_month = go.Figure()


        fig_month.add_trace(

            go.Scatter(

                x=daily_summary[
                    "day"
                ],

                y=daily_summary[
                    "avg_power"
                ],

                mode="lines+markers",

                name="Average Power"

            )

        )


        fig_month.add_trace(

            go.Scatter(

                x=daily_summary[
                    "day"
                ],

                y=daily_summary[
                    "max_power"
                ],

                mode="lines",

                name="Maximum Power"

            )

        )


        fig_month.update_layout(

            height=450,

            paper_bgcolor="#0b1a2b",

            plot_bgcolor="#0b1a2b",

            font=dict(
                color="#d9ecff"
            ),

            xaxis=dict(
                title="Date",
                gridcolor="#18364d"
            ),

            yaxis=dict(
                title="Power (kW)",
                gridcolor="#18364d"
            ),

            hovermode="x unified"

        )


        st.plotly_chart(

            fig_month,

            width="stretch",

            key="monthly_power_chart"

        )


        # -------------------------------------------------
        # MONTHLY TABLE
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            MONTHLY DAILY SUMMARY
        </div>
        """)


        monthly_display = (
            daily_summary.copy()
        )


        monthly_display.columns = [

            "Date",

            "Average Power (kW)",

            "Maximum Power (kW)",

            "Minimum Power (kW)",

            "Average PF",

            "Records"

        ]


        st.dataframe(

            monthly_display,

            width="stretch",

            hide_index=True

        )


        monthly_csv = (
            monthly_display
            .to_csv(index=False)
            .encode("utf-8-sig")
        )


        st.download_button(

            "ดาวน์โหลดสรุปรายเดือน CSV",

            data=monthly_csv,

            file_name=(
                f"LEOS_IPM310_"
                f"{selected_month}.csv"
            ),

            mime="text/csv",

            key="monthly_csv"

        )


    # =====================================================
    # YEARLY
    # =====================================================

    elif page == "YEARLY":

        st.html("""
        <div class="section-title">
            YEARLY ENERGY MONITORING
        </div>
        """)


        years = sorted(

            df[
                "timestamp"
            ]
            .dt
            .year
            .unique(),

            reverse=True

        )


        if not years:

            st.warning(
                "ยังไม่มีข้อมูลรายปี"
            )

            return


        selected_year = st.selectbox(

            "เลือกปี",

            years,

            key="yearly_select"

        )


        yearly = df[

            df[
                "timestamp"
            ]
            .dt
            .year
            == selected_year

        ].copy()


        if yearly.empty:

            st.warning(
                "ไม่มีข้อมูลของปีนี้"
            )

            return


        yearly["power_kw"] = (

            yearly["total_power"]

            / 1000

        )


        yearly["month"] = (

            yearly[
                "timestamp"
            ]
            .dt
            .month

        )


        monthly_summary = (

            yearly

            .groupby("month")

            .agg(

                avg_power=(
                    "power_kw",
                    "mean"
                ),

                max_power=(
                    "power_kw",
                    "max"
                ),

                min_power=(
                    "power_kw",
                    "min"
                ),

                avg_pf=(
                    "power_factor",
                    "mean"
                ),

                records=(
                    "power_kw",
                    "count"
                )

            )

            .reset_index()

        )


        month_names = {

            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December"

        }


        monthly_summary[
            "month_name"
        ] = (

            monthly_summary[
                "month"
            ]
            .map(month_names)

        )


        year_avg = (
            yearly["power_kw"].mean()
        )

        year_max = (
            yearly["power_kw"].max()
        )

        year_min = (
            yearly["power_kw"].min()
        )

        year_pf = (
            yearly["power_factor"].mean()
        )


        c1, c2, c3, c4 = st.columns(4)


        with c1:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        YEAR AVG POWER
                    </div>

                    <div class="stat-number">
                        {year_avg:.2f} kW
                    </div>

                </div>
                """
            )


        with c2:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        YEAR MAX POWER
                    </div>

                    <div class="stat-number">
                        {year_max:.2f} kW
                    </div>

                </div>
                """
            )


        with c3:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        YEAR MIN POWER
                    </div>

                    <div class="stat-number">
                        {year_min:.2f} kW
                    </div>

                </div>
                """
            )


        with c4:

            st.html(
                f"""
                <div class="stat-card">

                    <div class="stat-label">
                        YEAR AVG PF
                    </div>

                    <div class="stat-number">
                        {year_pf:.3f}
                    </div>

                </div>
                """
            )


        # -------------------------------------------------
        # YEARLY GRAPH
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            YEARLY POWER TREND
        </div>
        """)


        fig_year = go.Figure()


        fig_year.add_trace(

            go.Bar(

                x=monthly_summary[
                    "month_name"
                ],

                y=monthly_summary[
                    "avg_power"
                ],

                name="Average Power"

            )

        )


        fig_year.update_layout(

            height=450,

            paper_bgcolor="#0b1a2b",

            plot_bgcolor="#0b1a2b",

            font=dict(
                color="#d9ecff"
            ),

            xaxis=dict(
                title="Month",
                gridcolor="#18364d"
            ),

            yaxis=dict(
                title="Average Power (kW)",
                gridcolor="#18364d"
            )

        )


        st.plotly_chart(

            fig_year,

            width="stretch",

            key="yearly_power_chart"

        )


        # -------------------------------------------------
        # YEARLY TABLE
        # -------------------------------------------------

        st.html("""
        <div class="section-title">
            YEARLY MONTHLY SUMMARY
        </div>
        """)


        yearly_display = monthly_summary[

            [
                "month_name",
                "avg_power",
                "max_power",
                "min_power",
                "avg_pf",
                "records"
            ]

        ].copy()


        yearly_display.columns = [

            "Month",

            "Average Power (kW)",

            "Maximum Power (kW)",

            "Minimum Power (kW)",

            "Average PF",

            "Records"

        ]


        st.dataframe(

            yearly_display,

            width="stretch",

            hide_index=True

        )


        yearly_csv = (
            yearly_display
            .to_csv(index=False)
            .encode("utf-8-sig")
        )


        st.download_button(

            "ดาวน์โหลดสรุปรายปี CSV",

            data=yearly_csv,

            file_name=(
                f"LEOS_IPM310_"
                f"{selected_year}.csv"
            ),

            mime="text/csv",

            key="yearly_csv"

        )


# =========================================================
# FOOTER
# =========================================================

st.html("""
<div style="
    text-align:center;
    color:#60758a;
    margin-top:30px;
    padding-top:15px;
    border-top:1px solid #18364d;
">

    LEOS IPM310 • Energy Monitoring System • Modbus TCP

</div>
""")


# =========================================================
# START
# =========================================================

dashboard()