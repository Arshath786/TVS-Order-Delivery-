# TVS Order & Delivery Intelligence Dashboard

A public-portfolio Streamlit dashboard built from the supplied TVS project datasets.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy free
1. Create a GitHub repository (public).
2. Upload `app.py`, `requirements.txt`, and the `data/` folder.
3. Open https://share.streamlit.io/ and sign in with GitHub.
4. Select the repository, branch `main`, and main file `app.py`.
5. Deploy. Streamlit will provide a public `*.streamlit.app` URL.

## Data protection
The supplied customer CSV contained customer names, phone numbers and email addresses.
Those direct identifiers have been removed from the public copy. Do not add them back.
Only publish data you own or have permission to share.

## Metric notes
- Total orders and delivery counts are calculated from Fact_Orders.csv.
- Delivered means `Actual_Delivery_Date` is present; otherwise Pending.
- Delivery days are calculated as actual delivery date minus order date.
- Estimated order value is a proxy using `On_Road_Price` from Bike_Dime.csv, not actual recognized revenue.
- This project dataset does not contain a separate returns table or a separate sales transaction value table.
