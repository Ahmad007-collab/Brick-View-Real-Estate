import pandas as pd
import sqlite3
import numpy as np
import streamlit as st
from PIL import Image

# load image before using it in the sidebar
image = Image.open(r"C:\Users\Windows 11\Pictures\House.jpg")

st.sidebar.image(image)
st.sidebar.markdown(
    "<div style=\"white-space:nowrap; font-size:30px; font-weight: bold;\">\n BrickView \n </div>",
    unsafe_allow_html=True
    )
st.sidebar.title('Real Estate Intelligence')
selection = st.sidebar.radio('Menu', ['Introduction', 'Filters & Explores', 'Visualisations', 'CRUD Operations', 'SQL Queries'])
if selection == 'Introduction':
    left, center, right = st.columns([2, 1, 2])
    with center:
        img_small = image.resize((150, 100))  # (width, height)
        st.image(img_small)
        st.markdown(
            "<div style=\"text-align: left; white-space:nowrap; font-size:40px; font-weight: bold;\">\n BrickView Real Estate\n </div>",
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <div style="
                text-align: left;
                white-space: nowrap;
                font-size: 20px">
                Welcome to Discover the Real Estate You Can Trust.
            </div>
            """,
            unsafe_allow_html=True
        )
if selection == 'Filters & Explores':
    import streamlit as st
    import pandas as pd
    from database import get_connection

    conn = get_connection()

    df = pd.read_sql("SELECT * FROM listings", conn)

    st.title("Property Filters")

    # City Filter
    cities = ["All"] + sorted(df["City"].dropna().unique())
    selected_city = st.selectbox("City", cities)

    if selected_city != "All":
        df = df[df["City"] == selected_city]

    # Property Type
    types = sorted(df["Property_Type"].dropna().unique())
    selected_types = st.multiselect("Property Type", types)

    if selected_types:
        df = df[df["Property_Type"].isin(selected_types)]

    #agents

    agents = sorted(df['Agent_ID'].dropna().unique())
    selected_agents = st.multiselect('Agent_ID',agents)

    # Price
    min_price = int(df["Price"].min())
    max_price = int(df["Price"].max())

    price_range = st.slider(
        "Price",
        min_price,
        max_price,
        (min_price, max_price)
    )

    df = df[
        (df["Price"] >= price_range[0]) &
        (df["Price"] <= price_range[1])
    ]

    if selected_agents:
        df = df[df['Agent_ID'].isin(selected_agents)]

    st.dataframe(df)
if selection == 'Visualisations':  
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    from database import get_connection

    st.title("📊 Real Estate Visualizations")

    conn = get_connection()

    query = """
    SELECT City,
        COUNT(*) AS total
    FROM listings
    GROUP BY City
    ORDER BY total DESC
    """

    city_df = pd.read_sql(query, conn)

    fig = px.bar(
        city_df,
        x="City",
        y="total",
        color="total",
        title="Listings by City"
    )

    st.plotly_chart(fig, use_container_width=True)

#-------------------------------------------------------

    query = """
    SELECT
    strftime('%Y-%m', date_listed) AS Month,
    COUNT(*) AS Listings
    FROM listings
    GROUP BY Month
    ORDER BY Month
    """

    month_df = pd.read_sql(query, conn)

    fig = px.line(
        month_df,
        x="Month",
        y="Listings",
        markers=True,
        title="Listings Added Over Time"
    )
    st.plotly_chart(fig, use_container_width=True)

#-------------------------------------------------------

    query = """
    SELECT Property_Type,
    COUNT(*) AS Total
    FROM listings
    GROUP BY Property_Type
    """

    pie_df = pd.read_sql(query, conn)

    fig = px.pie(
        pie_df,
        names="Property_Type",
        values="Total",
        hole=0.4,
        title="Property Type Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

#-------------------------------------------------------
    query = """
    SELECT
    Latitude AS latitude,
    Longitude AS longitude,
    Price,
    City
    FROM listings
    """

    map_df = pd.read_sql(query, conn)

    st.map(map_df)

#--------------- CREATE -------------------

if selection == 'CRUD Operations':
    import streamlit as st
    import pandas as pd
    from database import get_connection

    conn = get_connection()

    st.title("📋 CRUD Operations")
    st.caption("Create, Read, Update and Delete records across all database tables")

    table = st.selectbox(
        "📋 Select Table",
        [
            "listings",
            "agents",
            "buyers",
            "property_attr",
            "sales"
        ]
    )

    operation = st.radio(
        "",
        ["👁 View","➕ Add","✏ Update","🗑 Delete"],
        horizontal=True
    )


    rows = st.slider(
        "Rows to display",
        min_value=5,
        max_value=100,
        value=50,
        step=5
    )

    query = f"""
    SELECT *
    FROM {table}
    LIMIT {rows}
    """

    df = pd.read_sql(query, conn)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # ADD
    if operation == "➕ Add":

        st.subheader("➕ Add New Record")

        schema = pd.read_sql(
            f"PRAGMA table_info({table})",
            conn
        )

        values = {}

        with st.form("add_form"):

            for _, row in schema.iterrows():

                column = row["name"]
                dtype = row["type"].upper()

                # Skip auto-generated INTEGER primary keys
                if row["pk"] == 1 and "INT" in dtype:
                    continue

                if "INT" in dtype:

                    values[column] = st.number_input(
                        column,
                        step=1,
                        format="%d"
                    )

                elif "REAL" in dtype or "FLOAT" in dtype or "DOUBLE" in dtype:

                    values[column] = st.number_input(column)

                else:

                    values[column] = st.text_input(column)

            submitted = st.form_submit_button("Add Record")

            if submitted:

                cols = ",".join(values.keys())

                placeholders = ",".join(["?"] * len(values))

                sql = f"""
                INSERT INTO {table}
                ({cols})
                VALUES ({placeholders})
                """

                conn.execute(sql, tuple(values.values()))

                conn.commit()

                st.success("Record added successfully.")

                st.rerun()

    #UPDATE

    if operation == "✏ Update":

        st.subheader("✏ Update Record")

        schema = pd.read_sql(
            f"PRAGMA table_info({table})",
            conn
        )

        primary_key = schema[schema["pk"] == 1]["name"].iloc[0]

        ids = pd.read_sql(
            f"""
            SELECT {primary_key}
            FROM {table}
            """,
            conn
        )

        selected_id = st.selectbox(
            "Select Record",
            ids[primary_key]
        )

        record = pd.read_sql(
            f"""
            SELECT *
            FROM {table}
            WHERE {primary_key}=?
            """,
            conn,
            params=(selected_id,)
        )

        updated_values = {}

        with st.form("update_form"):

            for _, row in schema.iterrows():

                column = row["name"]

                value = record.iloc[0][column]

                dtype = row["type"].upper()

                if "INT" in dtype:

                    updated_values[column] = st.number_input(
                        column,
                        value=int(value)
                    )

                elif "REAL" in dtype or "FLOAT" in dtype:

                    updated_values[column] = st.number_input(
                        column,
                        value=float(value)
                    )

                else:

                    updated_values[column] = st.text_input(
                        column,
                        value=str(value)
                    )

            submit = st.form_submit_button("Update Record")

            if submit:

                assignments = ",".join(
                    f"{col}=?" for col in updated_values.keys()
                )

                sql = f"""
                UPDATE {table}
                SET {assignments}
                WHERE {primary_key}=?
                """

                conn.execute(
                    sql,
                    list(updated_values.values()) + [selected_id]
                )

                conn.commit()

                st.success("Record Updated Successfully")
                st.rerun()
    #DELETE

    if operation == "🗑 Delete":

        st.subheader("🗑 Delete Record")

        schema = pd.read_sql(
            f"PRAGMA table_info({table})",
            conn
        )

        primary_key = schema[schema["pk"] == 1]["name"].iloc[0]

        ids = pd.read_sql(
            f"""
            SELECT {primary_key}
            FROM {table}
            """,
            conn
        )

        selected_id = st.selectbox(
            "Select Record to Delete",
            ids[primary_key]
        )

        st.warning("This action cannot be undone.")

        if st.button("Delete Record"):

            conn.execute(
                f"""
                DELETE FROM {table}
                WHERE {primary_key}=?
                """,
                (selected_id,)
            )

            conn.commit()

            st.success("Record Deleted Successfully")

            st.rerun()

if selection == ('SQL Queries'):
    import streamlit as st
    import pandas as pd
    import sqlite3

    # Database Connection
    conn = sqlite3.connect("brickview_realstate.db")

    st.title("📂 Pre-built Analytical Queries")

    # -----------------------------
    # Query 1
    # -----------------------------
    with st.expander("1️⃣ What is the average listing price by city?"):

        query = """
        SELECT city, AVG(price) AS avg_price
        FROM listings
        GROUP BY city;
        """

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 2
    #------------------------------
    with st.expander("2️⃣ What is the average price per square foot by property type?"):

        query = """
        SELECT Property_Type AS property_type,
            AVG(Price * 1.0 / Sqft) AS avg_price_per_sqft
        FROM listings
        WHERE Sqft IS NOT NULL
        AND Sqft > 0
        GROUP BY Property_Type
        ORDER BY avg_price_per_sqft DESC;
        """

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 3
    #------------------------------
    with st.expander("3️⃣ How does furnishing status impact property prices?"):
        query = """
        SELECT pa.furnishing_status, COUNT(*) AS total_properties,
        ROUND(AVG(l.Price), 2) AS avg_price,
        ROUND(MIN(l.Price), 2) AS min_price,
        ROUND(MAX(l.Price), 2) AS max_price
        FROM property_attributes pa
        JOIN listings l
        ON pa.listing_id = l.Listing_ID
        WHERE pa.furnishing_status IS NOT NULL
        GROUP BY pa.furnishing_status
        ORDER BY avg_price DESC;
        """
        
        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 4
    #------------------------------
    with st.expander("4️⃣ Do properties closer to metro stations command higher prices?"):
        query = """
        SELECT
            CASE
                WHEN metro_distance_km IS NOT NULL AND metro_distance_km * 1000 <= 500 THEN '0-500 meters'
                WHEN metro_distance_km IS NOT NULL AND metro_distance_km * 1000 <= 1000 THEN '501-1000 meters'
                WHEN metro_distance_km IS NOT NULL AND metro_distance_km * 1000 <= 2000 THEN '1001-2000 meters'
                ELSE '2000M+'
            END AS distance_band,
            COUNT(*) AS property_count,
            ROUND(AVG(l.price), 2) AS avg_price,
            ROUND(MIN(l.price), 2) AS min_price,
            ROUND(MAX(l.price), 2) AS max_price
        FROM property_attributes pa
        JOIN listings l
            ON pa.listing_id = l.listings_id
        GROUP BY distance_band
        ORDER BY avg_price DESC;
        """
        query = query.replace("l.listings_id", "l.Listing_ID")
        df_avg_price = pd.read_sql(query, conn)
        print(df_avg_price)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 5
    #------------------------------
    with st.expander("5️⃣ Are rented properties priced differently from non-rented ones?"):
        query = """
        SELECT 
            CASE 
                WHEN is_rented = 1 THEN 'Rented'
                ELSE 'Not Rented'
            END AS rental_status,
            COUNT(*) AS property_count,
            AVG(price) AS avg_price,
            MIN(price) AS min_price,
            MAX(price) AS max_price
        FROM property_attributes pa
        JOIN listings l ON pa.listing_id = l.Listing_ID
        GROUP BY rental_status;
        """
        query = query.replace("l.listings_id", "l.Listing_ID")
        df_rental_status = pd.read_sql(query, conn)
        print(df_rental_status)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)
        
    #------------------------------
    # Query 6
    #------------------------------
    with st.expander("6️⃣ How do bedrooms and bathrooms affect pricing?"):
        query = """
        SELECT
            pa.bedrooms,
            pa.bathrooms,
            COUNT(*) AS property_count,
            AVG(l.price) AS avg_price,
            MIN(l.price) AS min_price,
            MAX(l.price) AS max_price
        FROM property_attributes pa
        JOIN listings l
            ON pa.listing_id = l.Listing_ID
        GROUP BY pa.bedrooms, bathrooms
        ORDER BY pa.bedrooms, bathrooms;
        """
        query = query.replace("l.listings_id", "l.Listing_ID")
        df_bedrooms_bathrooms = pd.read_sql(query, conn)
        print(df_bedrooms_bathrooms)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)
        
    #------------------------------
    # Query 7
    #------------------------------
    with st.expander("7️⃣ Do properties with parking and power backup sell at higher prices?"):
        query = """
        SELECT
            CASE
                WHEN parking_Available = 'True' AND power_backup = 'True' THEN 'parking_Availabe & power backup'
                WHEN parking_Available = 'True' AND power_backup = 'False' THEN 'parking_Available only'
                WHEN parking_Available = 'False' AND power_backup = 'True' THEN 'power_backup only'
                ELSE 'Neither'
            END AS amenities,
            COUNT(*) AS property_count,
            AVG(price) AS avg_price,
            MIN(price) AS min_price,
            MAX(price) AS max_price
        FROM property_attributes pa
        JOIN listings l ON pa.listing_id = l.Listing_ID
        GROUP BY
            CASE
                WHEN parking_Available = 'True' AND power_backup = 'True' THEN 'parking_Available & power backup'
                WHEN parking_Available = 'True' AND power_backup = 'False' THEN 'parking_Available only'
                WHEN parking_Available = 'False' AND power_backup = 'True' THEN 'power_backup only'
                ELSE 'Neither'
            END
        ORDER BY avg_price DESC;
        """

        df_avg_price = pd.read_sql(query, conn)
        print(df_avg_price)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 8
    #------------------------------
    with st.expander("8️⃣ How does year built influence listing price?"):
        import sqlite3

        conn = sqlite3.connect("brickview_realstate.db")

        query = """
        SELECT
            CASE
                WHEN year_built >= 2020 THEN '2020-present'
                WHEN year_built >= 2010 THEN '2010-2019'
                WHEN year_built >= 2000 THEN '2000-2009'
                WHEN year_built >= 1990 THEN '1990-1999'
                ELSE 'Before 1990'
            END AS construction_period,
            COUNT(*) AS property_count,
            AVG(l.price) AS avg_listing_price,
            MIN(l.price) AS min_price,
            MAX(l.price) AS max_price
        FROM property_attributes pa
        JOIN listings l ON pa.listing_id = l.Listing_ID
        GROUP BY
            CASE
                WHEN year_built >= 2020 THEN '2020-present'
                WHEN year_built >= 2010 THEN '2010-2019'
                WHEN year_built >= 2000 THEN '2000-2009'
                WHEN year_built >= 1990 THEN '1990-1999'
                ELSE 'Before 1990'
            END
        ORDER BY avg_listing_price DESC;
        """

        query = query.replace("l.listings_id", "l.Listing_ID")
        df_avg_listing_price = pd.read_sql(query, conn)
        print(df_avg_listing_price)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 9
    #------------------------------
    with st.expander("9️⃣ Which cities have the highest average property prices?"):
        query = """
        SELECT
            city,
            COUNT(*) AS property_count,
            AVG(price) AS avg_price,
            MIN(price) AS min_price,
            MAX(price) AS max_price
        FROM listings
        GROUP BY city
        ORDER BY avg_price DESC;
        """

        df_avg_price = pd.read_sql(query, conn)
        print(df_avg_price)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 10
    #------------------------------
    with st.expander("🔟 How are properties distributed across price buckets? "):
        query = """
        SELECT
            CASE
                WHEN Price < 100000 THEN 'Below 100k'
                WHEN Price BETWEEN 100000 AND 299999 THEN '100K - 299K'
                WHEN Price BETWEEN 300000 AND 499999 THEN '300K - 499K'
                WHEN Price BETWEEN 500000 AND 999999 THEN '500K - 999K'
                ELSE '1M and Above'
            END AS price_bucket,
            COUNT(*) AS Property_count,
            AVG(price) AS avg_price,
            MIN(price) AS min_price
        FROM listings
        GROUP BY price_bucket
        ORDER BY min_price;
        """

        df_min_price = pd.read_sql(query, conn)
        print(df_min_price)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 11
    #------------------------------
    with st.expander("1️⃣1️⃣ What is the average days on market by city?"):
        import pandas as pd
        import sqlite3

        query = """
        SELECT
            l.city AS City,
            AVG(s.days_on_market) AS avg_days_on_market
        FROM listings l
        JOIN sales s
            ON l.Listing_ID = s.listing_id
        GROUP BY l.city
        ORDER BY avg_days_on_market DESC;
        """

        conn = sqlite3.connect("brickview_realstate.db")
        df_avg_days_on_market = pd.read_sql(query, conn)
        print(df_avg_days_on_market)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 12
    #------------------------------
    with st.expander("1️⃣2️⃣ Which property types sell the fastest?"):
        import sqlite3
        import pandas as pd

        conn = sqlite3.connect("brickview_realstate.db")

        query = """
        SELECT 
            l.Listing_ID AS property_id,
            l.City,
            ROUND(l.Date_Listed) AS days_on_market
        FROM listings l
        JOIN sales s
            ON l.Listing_ID = s.listing_id
        ORDER BY days_on_market ASC;
        """

        df_DATEDIFF = pd.read_sql(query, conn)
        print(df_DATEDIFF)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 13
    #------------------------------
    with st.expander("1️⃣3️⃣ What percentage of properties are sold above listing price?"):
        import sqlite3
        import pandas as pd

        conn = sqlite3.connect("brickview_realstate.db")

        query = """
        SELECT
            ROUND(
                100.0 * SUM(CASE WHEN s.Sale_Price > l.price THEN 1 ELSE 0 END)
                / COUNT(*),
                2
            ) AS percentage_sold_above_listing
        FROM sales s
        JOIN listings l
            ON s.listing_id = l.Listing_ID
        WHERE s.Sale_Price IS NOT NULL
        AND l.price IS NOT NULL;
        """

        df_Price = pd.read_sql(query, conn)
        print(df_Price)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 14
    #------------------------------
    with st.expander("1️⃣4️⃣ What is the sale-to-list price ratio by city?"):
        import sqlite3
        import pandas as pd

        conn = sqlite3.connect("brickview_realstate.db")

        query = """
        SELECT
        l.city AS City,
        ROUND(AVG((s.sale_price * 100.0) / l.price), 2) AS sale_to_list_ratio_pct
        FROM sales s
        JOIN listings l
        ON s.listing_id = l.Listing_ID
        WHERE s.sale_price IS NOT NULL
        AND l.price IS NOT NULL
        AND l.price > 0
        GROUP BY l.city
        ORDER BY sale_to_list_ratio_pct DESC;
        """
        df_sale_to_list_ratio_pct = pd.read_sql(query, conn)
        print(df_sale_to_list_ratio_pct)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 15
    #------------------------------
    with st.expander("1️⃣5️⃣ Which listings took more than 90 days to sell?"):
        cols = [row[1] for row in conn.execute("PRAGMA table_info(listings)").fetchall()]

        can_compute_days = ("Date_Sold" in cols) and ("Date_Listed" in cols)
        has_days_col = "Days_on_Market" in cols

        select_parts = []
        # Property_Type
        select_parts.append("Property_Type" if "Property_Type" in cols else "NULL AS Property_Type")
        # Listing_ID -> listing_id
        select_parts.append("Listing_ID AS listing_id" if "Listing_ID" in cols else "NULL AS listing_id")
        # City
        select_parts.append("City" if "City" in cols else "NULL AS City")
        # Date_Listed
        select_parts.append("Date_Listed" if "Date_Listed" in cols else "NULL AS Date_Listed")
        # Date_Sold
        select_parts.append("Date_Sold" if "Date_Sold" in cols else "NULL AS Date_Sold")
        # Days_on_Market: use existing column, or compute from dates, or NULL
        if has_days_col:
            select_parts.append("Days_on_Market")
        elif can_compute_days:
            select_parts.append("ROUND(julianday(Date_Sold) - julianday(Date_Listed)) AS Days_on_Market")
        else:
            select_parts.append("NULL AS Days_on_Market")

        select_clause = ",\n    ".join(select_parts)

        # Build WHERE / ORDER clauses depending on availability
        if has_days_col:
            where_clause = "WHERE Days_on_Market > 90"
            order_clause = "ORDER BY Days_on_Market DESC"
        elif can_compute_days:
            where_clause = "WHERE (julianday(Date_Sold) - julianday(Date_Listed)) > 90"
            order_clause = "ORDER BY Days_on_Market DESC"
        else:
            where_clause = ""  # cannot filter by days on market
            order_clause = ""

        query = f"""
        SELECT
            {select_clause}
        FROM listings
        {where_clause}
        {order_clause};
        """

        df_Days_on_Market = pd.read_sql(query, conn)
        print(df_Days_on_Market)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 16
    #------------------------------
    with st.expander("1️⃣6️⃣ How does metro distance affect time on market?"):
        cursor = conn.cursor()
        sales_cols = [r[1] for r in cursor.execute("PRAGMA table_info(sales)").fetchall()]
        listing_cols = [r[1] for r in cursor.execute("PRAGMA table_info(listings)").fetchall()]

        # find sale date column in sales table
        for c in ['sale_date','Sale_Date','Date_Sold','date_sold','saleDate','SaleDate']:
            if c in sales_cols:
                sale_date_col = c
                break
        else:
            raise RuntimeError(f"Could not find sale date column in sales table. Found: {', '.join(sales_cols)}")

        # find listing date column in listings table
        for c in ['Date_Listed','date_listed','listed_date','DateListed','dateListed']:
            if c in listing_cols:
                listing_date_col = c
                break
        else:
            raise RuntimeError(f"Could not find listing date column in listings table. Found: {', '.join(listing_cols)}")

        # find listing id column name used in listings table
        for c in ['Listing_ID','listing_id','ListingId','listingId']:
            if c in listing_cols:
                listing_id_col = c
                break
        else:
            raise RuntimeError(f"Could not find listing id column in listings table. Found: {', '.join(listing_cols)}")

        # Build and run query using the detected column names (quoted to preserve case)
        query = f"""
        SELECT
            CASE
                WHEN pa.metro_distance_km < 1 THEN '0-1 km'
                WHEN pa.metro_distance_km < 3 THEN '1-3 km'
                WHEN pa.metro_distance_km < 5 THEN '3-5 km'
                ELSE '5+ km'
            END AS metro_distance_km,
            ROUND(AVG(julianday(s.\"{sale_date_col}\") - julianday(l.\"{listing_date_col}\")), 2) AS avg_Days_on_Market,
            COUNT(*) AS total_listings
        FROM listings l
        JOIN property_attributes pa ON pa.listing_id = l.\"{listing_id_col}\"
        JOIN sales s ON s.listing_id = l.\"{listing_id_col}\"
        WHERE pa.metro_distance_km IS NOT NULL
        AND s.\"{sale_date_col}\" IS NOT NULL
        AND l.\"{listing_date_col}\" IS NOT NULL
        GROUP BY
            CASE
                WHEN pa.metro_distance_km < 1 THEN '0-1 km'
                WHEN pa.metro_distance_km < 3 THEN '1-3 km'
                WHEN pa.metro_distance_km < 5 THEN '3-5 km'
                ELSE '5+ km'
            END
        ORDER BY avg_Days_on_Market;
        """

        df_Days_on_Market = pd.read_sql(query, conn)
        print(df_Days_on_Market)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 17
    #------------------------------
    with st.expander("1️⃣7️⃣ What is the monthly sales trend?"):
        import sqlite3
        import pandas as pd

        conn = sqlite3.connect("brickview_realstate.db")

        query = """
        SELECT
            CAST(strftime('%Y', Date_Sold) AS INTEGER) AS sale_year,
            CAST(strftime('%m', Date_Sold) AS INTEGER) AS sale_month,
            COUNT(*) AS properties_sold,
            SUM(Sale_Price) AS total_sales_value,
            AVG(Sale_Price) AS average_sale_price
        FROM sales
        WHERE Date_Sold IS NOT NULL
        GROUP BY
            sale_year,
            sale_month
        ORDER BY
            sale_year,
            sale_month;
        """

        df_sale_year_sale_month = pd.read_sql(query, conn)
        print(df_sale_year_sale_month)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 18
    #------------------------------
    with st.expander("1️⃣8️⃣ Which properties are currently unsold?"):
        import sqlite3
        import pandas as pd

        conn = sqlite3.connect("brickview_realstate.db")

        query = """
        SELECT
            Property_Type,
            City,
            Date_Listed
        FROM listings
        ORDER BY Date_Listed DESC;
        """

        cols = [r[1] for r in conn.execute("PRAGMA table_info(listings)").fetchall()]

        def find(cands):
            for c in cands:
                if c in cols:
                    return c
            return None

        pt_col = find(['Property_Type','property_type','PropertyType'])
        city_col = find(['City','city'])
        date_listed_col = find(['Date_Listed','listed_date','DateListed','listedDate','listeddate'])
        price_col = find(['listing_price','price','Listing_Price','listingPrice'])
        date_sold_col = find(['Date_Sold','date_sold','DateSold','datesold'])

        select_parts = [
            (f"{pt_col} AS Property_Type" if pt_col else "NULL AS Property_Type"),
            (f"{city_col} AS City" if city_col else "NULL AS City"),
            (f"{date_listed_col} AS Date_Listed" if date_listed_col else "NULL AS Date_Listed"),
            (f"{price_col} AS listing_price" if price_col else "NULL AS listing_price"),
        ]

        where_clause = f"WHERE {date_sold_col} IS NULL" if date_sold_col else ""
        order_clause = f"ORDER BY {date_listed_col} DESC" if date_listed_col else ""

        # build the joiner separately to avoid backslashes inside f-string expressions
        joiner = ",\n    "
        query_corrected = f"SELECT\n    {joiner.join(select_parts)}\nFROM listings\n{where_clause}\n{order_clause};"

        df_Date_Listed = pd.read_sql(query_corrected, conn)
        print(df_Date_Listed)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 19
    #------------------------------
    with st.expander("1️⃣9️⃣ Which agents have closed the most sales?"):
        import sqlite3
        import pandas as pd

        conn = sqlite3.connect("brickview_realstate.db")

        query = """
        SELECT
            agent_id,
            COUNT(*) AS total_sales_closed
        FROM agents
        GROUP BY agent_id
        ORDER BY deals_closed DESC;
        """
        df_deals_closed = pd.read_sql(query_corrected, conn)
        print(df_deals_closed)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 20
    #------------------------------
    with st.expander("2️⃣0️⃣ Who are the top agents by total sales revenue?"):
        import sqlite3
        import pandas as pd

        conn = sqlite3.connect("brickview_realstate.db")

        query = """
        SELECT
            agent_id,
            agent_name,
            SUM(sale_price) AS total_sales_revenue,
            COUNT(*) AS properties_sold,
            AVG(sale_price) AS average_sale_price
        FROM listings
        WHERE Date_Sold IS NOT NULL
        GROUP BY
            agent_id,
            agent_name
        ORDER BY total_sales_revenue DESC;
        """
        # build a robust query using actual table column names
        listings_cols = [r[1] for r in conn.execute("PRAGMA table_info(listings)").fetchall()]
        sales_cols = [r[1] for r in conn.execute("PRAGMA table_info(sales)").fetchall()]
        agents_cols = [r[1] for r in conn.execute("PRAGMA table_info(agents)").fetchall()]

        def find(cols, candidates):
            for c in candidates:
                if c in cols:
                    return c
            return None

        listing_id_col = find(listings_cols, ['Listing_ID','listing_id','ListingId','listingId'])
        listing_agent_col = find(listings_cols, ['Agent_ID','agent_id','AgentId','agentId'])
        sales_listing_id_col = find(sales_cols, ['listing_id','Listing_ID','ListingId'])
        sales_price_col = find(sales_cols, ['sale_price','Sale_Price','SalePrice','salePrice'])
        sales_date_col = find(sales_cols, ['Date_Sold','date_sold','Sale_Date','sale_date'])
        agents_id_col = find(agents_cols, ['agents_id','agent_id','id','Agents_ID','Agent_ID'])
        agents_name_col = find(agents_cols, ['name','agent_name','Name','Agent_Name'])

        if not listing_agent_col:
            raise RuntimeError(f"Could not find agent id column in listings. Found: {listings_cols}")

        # prepare joins / selects depending on availability of agents table / name
        if agents_name_col and agents_id_col:
            join_agents = f'LEFT JOIN agents a ON a."{agents_id_col}" = l."{listing_agent_col}"'
            select_agent_name = f'a."{agents_name_col}" AS agent_name'
            group_by_extra = f', a."{agents_name_col}"'
        else:
            join_agents = ''
            select_agent_name = 'NULL AS agent_name'
            group_by_extra = ''

        # ensure sales columns exist
        if not sales_listing_id_col or not sales_price_col:
            raise RuntimeError(f"Could not find required columns in sales table. Found: {sales_cols}")

        # filter by sale date if available
        where_clause = f'WHERE s."{sales_date_col}" IS NOT NULL' if sales_date_col else ''

        query = f'''
        SELECT
            l."{listing_agent_col}" AS agent_id,
            {select_agent_name},
            SUM(s."{sales_price_col}") AS total_sales_revenue,
            COUNT(*) AS properties_sold,
            AVG(s."{sales_price_col}") AS average_sale_price
        FROM listings l
        JOIN sales s ON s."{sales_listing_id_col}" = l."{listing_id_col}"
        {join_agents}
        {where_clause}
        GROUP BY
            l."{listing_agent_col}"{group_by_extra}
        ORDER BY total_sales_revenue DESC;
        '''

        df_total_sales_revenue = pd.read_sql(query, conn)
        print(df_total_sales_revenue)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 21
    #------------------------------
    with st.expander("2️⃣1️⃣ Which agents close deals fastest?"):
        query = """
        SELECT
            a.Agent_ID AS agent_id,
            a.Name AS agent_name,
            ROUND(AVG(julianday(s.Date_Sold) - julianday(l.Date_Listed)), 2) AS avg_days_to_close,
            COUNT(s.Listing_ID) AS deals_closed
        FROM agents a
        JOIN listings l ON l.Agent_ID = a.Agent_ID
        JOIN sales s ON s.Listing_ID = l.Listing_ID
        WHERE s.Date_Sold IS NOT NULL
        AND l.Date_Listed IS NOT NULL
        GROUP BY
            a.Agent_ID,
            a.Name
        ORDER BY
            avg_days_to_close ASC;
        """

        df_agents_closing_speed = pd.read_sql(query, conn)
        print(df_agents_closing_speed)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 22
    #------------------------------
    with st.expander("2️⃣2️⃣ Does experience correlate with deals closed?"):
        query = """
        SELECT
            a."Agent_ID" AS agent_id,
            a."Name" AS agent_name,
            a."experience_years" AS years_experience,
            COUNT(s."Listing_ID") AS deals_closed
        FROM agents a
        LEFT JOIN listings l
            ON a."Agent_ID" = l."Agent_ID"
        LEFT JOIN sales s
            ON l."Listing_ID" = s."Listing_ID"
        WHERE s."Date_Sold" IS NOT NULL
        GROUP BY
            a."Agent_ID",
            a."Name",
            a."experience_years"
        ORDER BY
            a."experience_years" DESC;
        """

        df_years_experience = pd.read_sql(query, conn)
        print(df_years_experience)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 23
    #------------------------------
    with st.expander("2️⃣3️⃣ Do agents with higher ratings close deals faster?"):
        query = """
        SELECT
            a."Agent_ID" AS agent_id,
            a."Name" AS agent_name,
            a.rating,
            ROUND(AVG(julianday(s."Date_Sold") - julianday(l."Date_Listed")), 2) AS avg_days_to_close,
            COUNT(s."Listing_ID") AS deals_closed
        FROM agents a
        JOIN listings l
            ON l."Agent_ID" = a."Agent_ID"
        JOIN sales s
            ON s."Listing_ID" = l."Listing_ID"
        WHERE s."Date_Sold" IS NOT NULL
        AND l."Date_Listed" IS NOT NULL
        GROUP BY
            a."Agent_ID",
            a."Name",
            a.rating
        ORDER BY
            avg_days_to_close ASC;
        """

        df_days_to_close = pd.read_sql(query, conn)
        print(df_days_to_close)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 24
    #------------------------------
    with st.expander("2️⃣4️⃣ What is the average commission earned by each agent?"):
        query = """
        SELECT
            a."Agent_ID" AS agent_id,
            a."Name" AS agent_name,
            a."commission_rate" AS commission_rate,
            COUNT(s."Listing_ID") AS total_deals,
            ROUND(AVG(s."Sale_Price" * a."commission_rate" / 100), 2) AS avg_commission_earned,
            ROUND(SUM(s."Sale_Price" * a."commission_rate" / 100), 2) AS total_commission_earned
        FROM agents a
        LEFT JOIN listings l
            ON a."Agent_ID" = l."Agent_ID"
        LEFT JOIN sales s
            ON l."Listing_ID" = s."Listing_ID"
        WHERE s."Sale_Price" IS NOT NULL
        GROUP BY
            a."Agent_ID",
            a."Name",
            a."commission_rate"
        ORDER BY
            total_commission_earned DESC;
        """

        df_comission_earned = pd.read_sql(query, conn)
        print(df_comission_earned)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 25
    #------------------------------
    with st.expander("2️⃣5️⃣ Which agents currently have the most active listings?"):
        listing_cols = [row[1] for row in conn.execute("PRAGMA table_info(listings)").fetchall()]
        agents_cols = [row[1] for row in conn.execute("PRAGMA table_info(agents)").fetchall()]

        def find_col(cols, candidates):
            for c in candidates:
                if c in cols:
                    return c
            return None

        status_col = find_col(listing_cols, ['status', 'Status', 'listing_status', 'Listing_Status'])
        date_sold_col = find_col(listing_cols, ['Date_Sold', 'date_sold', 'Sale_Date', 'sale_date'])
        listing_id_col = find_col(listing_cols, ['listing_id', 'Listing_ID', 'ListingId', 'listingId', 'listings_id', 'Listings_ID'])
        listing_agent_col = find_col(listing_cols, ['agent_id', 'Agent_ID', 'AgentId', 'agentId'])
        agents_id_col = find_col(agents_cols, ['agent_id', 'agents_id', 'Agent_ID', 'Agents_ID'])
        agents_name_col = find_col(agents_cols, ['name', 'Name', 'agent_name', 'Agent_Name'])

        sales_cols = [row[1] for row in conn.execute("PRAGMA table_info(sales)").fetchall()]
        sales_listing_id_col = find_col(sales_cols, ['listing_id', 'Listing_ID', 'ListingId', 'listingId', 'listings_id', 'Listings_ID'])

        if not agents_id_col:
            raise RuntimeError(f"Could not find agent id column in agents table. Found: {agents_cols}")
        if not listing_agent_col:
            raise RuntimeError(f"Could not find agent id column in listings table. Found: {listing_cols}")
        if not agents_name_col:
            raise RuntimeError(f"Could not find agent name column in agents table. Found: {agents_cols}")
        if not listing_id_col:
            raise RuntimeError(f"Could not find listing id column in listings table. Found: {listing_cols}")

        if status_col:
            where_clause = f"WHERE l.\"{status_col}\" = 'Active'"
        elif date_sold_col:
            where_clause = f"WHERE l.\"{date_sold_col}\" IS NULL"
        elif sales_listing_id_col:
            where_clause = f"""
        WHERE l.\"{listing_id_col}\" NOT IN (
            SELECT s.\"{sales_listing_id_col}\"
            FROM sales s
            WHERE s.\"{sales_listing_id_col}\" IS NOT NULL
        )
        """
        else:
            raise RuntimeError(
                "Could not find a status or Date_Sold column in listings "
                "or a sales listing_id column to identify active listings."
            )

        query = f"""
        SELECT
            a."{agents_id_col}" AS agent_id,
            a."{agents_name_col}" AS agent_name,
            COUNT(l."{listing_id_col}") AS active_listings
        FROM agents a
        JOIN listings l
            ON a."{agents_id_col}" = l."{listing_agent_col}"
        {where_clause}
        GROUP BY
            a."{agents_id_col}",
            a."{agents_name_col}"
        ORDER BY
            active_listings DESC;
        """

        df_active_listings = pd.read_sql(query, conn)
        print(df_active_listings)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 26
    #------------------------------
    with st.expander("2️⃣6️⃣ What percentage of buyers are investors vs End Users?"):
        query = """
        SELECT
            buyer_type,
            COUNT(buyer_id) AS total_buyers,
            ROUND(
                COUNT(buyer_id) * 100.0 / (SELECT COUNT(*) FROM buyers),
                2
            ) AS percentage_of_buyers
        FROM buyers
        GROUP BY buyer_type;
        """

        df_buyer_type = pd.read_sql(query, conn)
        print(df_buyer_type)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 28
    #------------------------------
    with st.expander("2️⃣8️⃣ What is the average loan amount by buyer type?"):
        query = """
        SELECT
            buyer_type,
            ROUND(
                AVG(CASE WHEN loan_amount IS NOT NULL THEN loan_amount END),
                2
            ) AS avg_loan_amount,
            SUM(CASE WHEN loan_amount IS NOT NULL THEN 1 ELSE 0 END) AS total_loans
        FROM buyers
        GROUP BY buyer_type
        ORDER BY avg_loan_amount DESC;
        """

        df_avg_loan_amount = pd.read_sql(query, conn)
        print(df_avg_loan_amount)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 29
    #------------------------------
    with st.expander("2️⃣9️⃣ Which payment mode is most commonly used?"):
        # Prefer payments table if it exists, otherwise fall back to buyers.payment_mode
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

        if 'payments' in tables:
            query = """
            SELECT
                payment_mode,
                COUNT(payment_id) AS usage_count
            FROM payments
            GROUP BY payment_mode
            ORDER BY usage_count DESC;
            """
        else:
            query = """
            SELECT
                payment_mode,
                COUNT(buyer_id) AS usage_count
            FROM buyers
            GROUP BY payment_mode
            ORDER BY usage_count DESC;
            """

        df_usage_count = pd.read_sql(query, conn)
        print(df_usage_count)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)

    #------------------------------
    # Query 30
    #------------------------------
    with st.expander("3️⃣0️⃣  Do loan-backed purchases take longer to close?"):
        # Use existing connection `conn`. Compute avg days to close for loan-backed vs non-loan purchases
        import pandas as pd

        # discover columns
        def cols(table):
            return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]

        buyers_cols = cols("buyers")
        sales_cols = cols("sales")
        listing_cols = cols("listings")

        def find(cands, arr):
            for c in cands:
                if c in arr:
                    return c
            return None

        # relevant columns
        buyer_sale_id_col = find(['sale_id','sales_id','Sale_ID','saleId'], buyers_cols)
        loan_taken_col = find(['loan_taken','loanTaken','loan_taken_flag'], buyers_cols)
        loan_amount_col = find(['loan_amount','Loan_Amount','loanAmount'], buyers_cols)

        sales_id_col = find(['sales_id','sale_id','Sale_ID','id'], sales_cols)
        sales_listing_id_col = find(['listing_id','Listing_ID','ListingId'], sales_cols)
        sales_date_col = find(['Date_Sold','sale_date','Sale_Date','DateSold','SaleDate'], sales_cols)

        listing_id_col = find(['Listing_ID','listing_id','ListingId','listings_id'], listing_cols)
        listing_date_col = find(['Date_Listed','listed_date','listedDate','DateListed'], listing_cols)

        # determine loan indicator expression
        if loan_taken_col:
            loan_indicator = f"(b.\"{loan_taken_col}\" = 1 OR b.\"{loan_taken_col}\" IN ('True','true','TRUE'))"
        elif loan_amount_col:
            loan_indicator = f"b.\"{loan_amount_col}\" IS NOT NULL"
        else:
            raise RuntimeError("Could not find loan indicator (loan_taken / loan_amount) in buyers table.")

        # build joins: buyers -> sales -> listings
        joins = []
        if buyer_sale_id_col and sales_id_col:
            joins.append(f'JOIN sales s ON b.\"{buyer_sale_id_col}\" = s.\"{sales_id_col}\"')
        elif buyer_sale_id_col and sales_listing_id_col:
            joins.append(f'JOIN sales s ON b.\"{buyer_sale_id_col}\" = s.\"{sales_listing_id_col}\"')
        elif sales_id_col and sales_listing_id_col:
            joins.append('JOIN sales s ON 1=1')  # will be filtered later if needed
        else:
            raise RuntimeError("Could not determine join path between buyers and sales tables.")

        if sales_listing_id_col and listing_id_col:
            joins.append(f'JOIN listings l ON s.\"{sales_listing_id_col}\" = l.\"{listing_id_col}\"')
        elif listing_date_col and sales_date_col:
            # if listings not joinable, try to compute from sales dates only
            pass
        else:
            raise RuntimeError("Could not join sales to listings to get listing/listed date.")

        join_clause = "\n".join(joins)

        # ensure we have sale and listing date columns for days calculation
        if not sales_date_col:
            raise RuntimeError("Could not find sale date column in sales table.")
        if not listing_date_col:
            raise RuntimeError("Could not find listing/listed date column in listings table.")

        query = f"""
        SELECT
            CASE WHEN {loan_indicator} THEN 'Loan-backed' ELSE 'No Loan' END AS financing_type,
            ROUND(AVG(julianday(s."{sales_date_col}") - julianday(l."{listing_date_col}")), 2) AS avg_days_to_close,
            COUNT(*) AS total_deals
        FROM buyers b
        {join_clause}
        WHERE s."{sales_date_col}" IS NOT NULL
        AND l."{listing_date_col}" IS NOT NULL
        GROUP BY financing_type
        ORDER BY avg_days_to_close DESC;
        """

        df_avg_days_to_close = pd.read_sql(query, conn)
        print(df_avg_days_to_close)

        df = pd.read_sql(query, conn)

        st.code(query, language="sql")
        st.dataframe(df, use_container_width=True)




      

        
