import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="TVS | Order & Delivery Intelligence", page_icon="🏍️", layout="wide")

BG = "#081426"
PANEL = "#10213B"
BLUE = "#2395FF"
CYAN = "#46C7F5"
RED = "#F04452"
TEXT = "#EAF2FF"
MUTED = "#9EB2CC"

st.markdown("""
<style>
.stApp {background: linear-gradient(135deg,#071326 0%,#0B1C33 55%,#071326 100%); color:#EAF2FF;}
header[data-testid="stHeader"] {background:rgba(0,0,0,0);}
.block-container {padding-top:1.5rem; max-width:1500px;}
[data-testid="stMetric"] {background:#10213B;border:1px solid #203B60;padding:17px 18px;border-radius:14px;box-shadow:0 8px 24px #0003;}
[data-testid="stMetricLabel"] {color:#AFC4DF;}
[data-testid="stMetricValue"] {color:#FFFFFF;}
section[data-testid="stSidebar"] {background:#0B1B31;border-right:1px solid #203B60;}
h1,h2,h3 {color:#F4F8FF;}
div[data-testid="stPlotlyChart"] {background:#10213B;border:1px solid #203B60;border-radius:14px;padding:8px;}
.small-muted {color:#9EB2CC;font-size:0.9rem;}
.hero {background:linear-gradient(100deg,#102B50,#0C1A30);border:1px solid #244A78;border-radius:18px;padding:22px 26px;margin-bottom:18px;}
.hero-kicker {color:#69C9FF;font-size:12px;letter-spacing:2px;font-weight:700;}
.hero-title {font-size:30px;font-weight:800;color:#FFFFFF;margin:4px 0;}
.hero-sub {color:#B7CBE4;margin:0;}
</style>
""", unsafe_allow_html=True)

DATA = Path(__file__).parent / "data"

@st.cache_data
def load_data():
    orders = pd.read_csv(DATA/"Fact_Orders.csv")
    customers = pd.read_csv(DATA/"Customer_Dime.csv")
    dealers = pd.read_csv(DATA/"Dealer_Dime.csv")
    bikes = pd.read_csv(DATA/"Bike_Dime.csv")
    for c in ["Order_Date","Expected_Delivery_Date","Actual_Delivery_Date"]:
        orders[c] = pd.to_datetime(orders[c], errors="coerce")
    df = (orders.merge(customers, on="Customer_ID", how="left")
                 .merge(dealers, on="Dealer_Code", how="left")
                 .merge(bikes, on="Model_Code", how="left"))
    df["Delivery_Status"] = df["Actual_Delivery_Date"].notna().map({True:"Delivered",False:"Pending"})
    df["Delivery_Days"] = (df["Actual_Delivery_Date"]-df["Order_Date"]).dt.days
    df["Order_Month"] = df["Order_Date"].dt.to_period("M").dt.to_timestamp()
    # Estimate only: list price joined from Bike_Dime, not an actual transaction amount.
    df["Estimated_Order_Value"] = df["On_Road_Price"]
    return df

df = load_data()
st.markdown("""
<div class="hero">
 <div class="hero-kicker">TVS MOTOR BUSINESS INTELLIGENCE</div>
 <div class="hero-title">ORDER & DELIVERY PERFORMANCE</div>
 <p class="hero-sub">Interactive business intelligence | Sales • Customers • Dealers • Deliveries</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ⚙️ Dashboard filters")
    min_date, max_date = df.Order_Date.min().date(), df.Order_Date.max().date()
    date_range = st.date_input("Order date range", value=(min_date,max_date), min_value=min_date, max_value=max_date)
    districts = ["All"] + sorted(df["District"].dropna().unique().tolist())
    district = st.selectbox("Dealer district", districts)
    cities = ["All"] + sorted(df["City"].dropna().unique().tolist())
    city = st.selectbox("Customer city", cities)
    categories = ["All"] + sorted(df["Category"].dropna().unique().tolist())
    category = st.selectbox("Vehicle category", categories)
    statuses = ["All","Delivered","Pending"]
    status = st.selectbox("Delivery status", statuses)
    fuels = ["All"] + sorted(df["Fuel_Type"].dropna().unique().tolist())
    fuel = st.selectbox("Fuel type", fuels)
    st.markdown("---")
    st.caption("Dataset: supplied TVS project CSVs")

f = df.copy()
if isinstance(date_range, tuple) and len(date_range)==2:
    f = f[(f.Order_Date.dt.date>=date_range[0]) & (f.Order_Date.dt.date<=date_range[1])]
if district!="All": f=f[f.District==district]
if city!="All": f=f[f.City==city]
if category!="All": f=f[f.Category==category]
if status!="All": f=f[f.Delivery_Status==status]
if fuel!="All": f=f[f.Fuel_Type==fuel]

total = len(f)
delivered = int((f.Delivery_Status=="Delivered").sum())
pending = total-delivered
rate = delivered/total*100 if total else 0
avg_days = f.loc[f.Delivery_Status=="Delivered","Delivery_Days"].mean()
avg_days_text = f"{avg_days:.1f} days" if pd.notna(avg_days) else "—"
est_value = f["Estimated_Order_Value"].sum()

m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("Total orders",f"{total:,.0f}")
m2.metric("Delivered orders",f"{delivered:,.0f}")
m3.metric("Pending orders",f"{pending:,.0f}")
m4.metric("Delivery rate",f"{rate:.1f}%")
m5.metric("Avg. delivery time",avg_days_text)

tab1,tab2,tab3,tab4,tab5 = st.tabs(["Executive overview","Sales & models","Delivery performance","Customer insights","Dealer performance"])

plot_layout = dict(template="plotly_dark",paper_bgcolor=PANEL,plot_bgcolor=PANEL,font=dict(color=TEXT),margin=dict(l=25,r=20,t=48,b=35),legend=dict(orientation="h",y=1.12))
with tab1:
    a,b = st.columns(2)
    with a:
        monthly=f.groupby("Order_Month",dropna=True).size().reset_index(name="Orders")
        fig=px.line(monthly,x="Order_Month",y="Orders",markers=True,title="Monthly order trend")
        fig.update_traces(line_color=BLUE, line_width=3)
        fig.update_layout(**plot_layout)
        st.plotly_chart(fig,use_container_width=True)
    with b:
        status_df=f["Delivery_Status"].value_counts().rename_axis("Status").reset_index(name="Orders")
        fig=px.pie(status_df,names="Status",values="Orders",hole=.66,title="Delivery status mix",color="Status",color_discrete_map={"Delivered":BLUE,"Pending":RED})
        fig.update_layout(**plot_layout)
        st.plotly_chart(fig,use_container_width=True)
    c,d=st.columns(2)
    with c:
        cat=f.groupby("Category").size().reset_index(name="Orders").sort_values("Orders",ascending=True)
        fig=px.bar(cat,x="Orders",y="Category",orientation="h",title="Orders by vehicle category",text_auto=".2s",color_discrete_sequence=[BLUE])
        fig.update_layout(**plot_layout)
        st.plotly_chart(fig,use_container_width=True)
    with d:
        top=f.groupby("City").size().nlargest(10).sort_values().reset_index(name="Orders")
        fig=px.bar(top,x="Orders",y="City",orientation="h",title="Top 10 customer cities",text_auto=".2s",color_discrete_sequence=[CYAN])
        fig.update_layout(**plot_layout)
        st.plotly_chart(fig,use_container_width=True)

with tab2:
    a,b=st.columns(2)
    with a:
        trend=f.groupby("Order_Month").agg(Estimated_Value=("Estimated_Order_Value","sum")).reset_index()
        fig=px.area(trend,x="Order_Month",y="Estimated_Value",title="Estimated order value trend (₹)",color_discrete_sequence=[BLUE])
        fig.update_layout(**plot_layout)
        st.plotly_chart(fig,use_container_width=True)
    with b:
        models=f.groupby("Bike_Model").size().nlargest(10).sort_values().reset_index(name="Orders")
        fig=px.bar(models,x="Orders",y="Bike_Model",orientation="h",title="Top 10 bike models",text_auto=".2s",color_discrete_sequence=[CYAN])
        fig.update_layout(**plot_layout)
        st.plotly_chart(fig,use_container_width=True)
    st.caption("Estimated order value is calculated using the On_Road_Price in Bike_Dime.csv. It is a list-price proxy, not verified revenue or actual invoiced sales.")

with tab3:
    a,b=st.columns(2)
    with a:
        by_dealer=f.groupby("Dealer_Name").agg(Delivered=("Delivery_Status",lambda x:(x=="Delivered").sum()),Pending=("Delivery_Status",lambda x:(x=="Pending").sum())).reset_index()
        by_dealer=by_dealer.sort_values("Pending",ascending=True).tail(12)
        fig=go.Figure()
        fig.add_bar(y=by_dealer.Dealer_Name,x=by_dealer.Delivered,name="Delivered",orientation="h",marker_color=BLUE)
        fig.add_bar(y=by_dealer.Dealer_Name,x=by_dealer.Pending,name="Pending",orientation="h",marker_color=RED)
        fig.update_layout(barmode="stack",title="Delivered vs pending by dealer",**plot_layout)
        st.plotly_chart(fig,use_container_width=True)
    with b:
        lead=f.loc[f.Delivery_Status=="Delivered","Delivery_Days"].dropna()
        if len(lead):
            hist=pd.DataFrame({"Delivery days":lead})
            fig=px.histogram(hist,x="Delivery days",nbins=20,title="Delivered order lead-time distribution",color_discrete_sequence=[CYAN])
            fig.update_layout(**plot_layout)
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.info("No delivered orders in the selected filters.")
    st.markdown("#### Delivery records")
    st.dataframe(f[["Order_ID","Order_Date","Dealer_Name","District","Bike_Model","Delivery_Status","Expected_Delivery_Date","Actual_Delivery_Date"]].sort_values("Order_Date",ascending=False).head(300),use_container_width=True,hide_index=True)

with tab4:
    a,b=st.columns(2)
    with a:
        gender=f["Gender"].value_counts().rename_axis("Gender").reset_index(name="Customers")
        fig=px.pie(gender,names="Gender",values="Customers",hole=.62,title="Customer gender distribution",color_discrete_sequence=[BLUE,CYAN])
        fig.update_layout(**plot_layout)
        st.plotly_chart(fig,use_container_width=True)
    with b:
        age=f.groupby(pd.cut(f.Age,bins=[0,18,25,35,45,55,100],labels=["18 or below","19–25","26–35","36–45","46–55","56+"])).size().reset_index(name="Orders")
        age.columns=["Age group","Orders"]
        fig=px.bar(age,x="Age group",y="Orders",title="Orders by customer age group",color_discrete_sequence=[BLUE],text_auto=".2s")
        fig.update_layout(**plot_layout)
        st.plotly_chart(fig,use_container_width=True)
    st.caption("Customer names, phone numbers and email addresses are intentionally excluded from this public dashboard.")

with tab5:
    a,b=st.columns(2)
    with a:
        d=f.groupby("Dealer_Name").size().nlargest(12).sort_values().reset_index(name="Orders")
        fig=px.bar(d,x="Orders",y="Dealer_Name",orientation="h",title="Top dealers by orders",color_discrete_sequence=[BLUE],text_auto=".2s")
        fig.update_layout(**plot_layout)
        st.plotly_chart(fig,use_container_width=True)
    with b:
        years=f.groupby("Dealer_Since").size().reset_index(name="Orders")
        fig=px.bar(years,x="Dealer_Since",y="Orders",title="Orders by dealer establishment year",color_discrete_sequence=[CYAN])
        fig.update_layout(**plot_layout)
        st.plotly_chart(fig,use_container_width=True)
    st.dataframe(f.groupby(["Dealer_Name","District"]).agg(Orders=("Order_ID","count"),Delivered=("Delivery_Status",lambda x:(x=="Delivered").sum()),Pending=("Delivery_Status",lambda x:(x=="Pending").sum())).reset_index().sort_values("Orders",ascending=False),use_container_width=True,hide_index=True)

st.markdown("---")
left,right=st.columns([3,1])
with left:
    st.markdown("**TVS Order & Delivery Intelligence**  ·  Portfolio project")
    st.caption("Built with Python, Streamlit, Pandas and Plotly. Metrics are calculated from the supplied project datasets.")
with right:
    st.download_button("⬇️ Download filtered data",f.to_csv(index=False).encode("utf-8"),"tvs_filtered_orders.csv","text/csv",use_container_width=True)
