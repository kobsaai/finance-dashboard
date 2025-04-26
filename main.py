import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import json
from utils.normalize_transactions import parse_transaction


st.set_page_config(page_title="Data Analysis App", page_icon="📊", layout="wide")

category_file = "categories.json"

if "categories" not in st.session_state:
    st.session_state.categories = {
        "Uncategorized": []
    }
if os.path.exists(category_file):
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)

def save_categories():
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f)

def categorize_transactions(df):
    df["Category"] = "Uncategorized"

    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue

        normalized_keywords = [keyword.lower().strip().replace(" ", "") for keyword in keywords]

        for idx, row in df.iterrows():
            details = str(row["Wer"]).lower().strip().replace(" ", "")
            if details in normalized_keywords:
                df.at[idx, "Category"] = category
    return df

def add_keyword_to_category(category, keyword):
    keyword = keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    return False



def load_transactions(file):
    try:
        df = pd.read_csv(file, encoding="latin1", sep=";", skiprows=3)
        df.columns = [col.strip() for col in df.columns]
        df = df.rename(columns={"Unnamed: 5" : "Type"})
        df.drop("Wertstellung (Valuta)", axis="columns", inplace=True)
        df["Buchungstag"] = pd.to_datetime(df["Buchungstag"], format="%d.%m.%Y", errors="coerce")

        df["Umsatz in EUR"] = df["Umsatz in EUR"].str.replace(".", "", regex=False)
        df["Umsatz in EUR"] = df["Umsatz in EUR"].str.replace(",", ".", regex=False)
        df["Umsatz in EUR"] = df["Umsatz in EUR"].astype(float)

        df["Type"] = np.where(df["Umsatz in EUR"] < 0, "Ausgabe", "Einnahme")
        df_parsed = df["Buchungstext"].fillna("").apply(parse_transaction).apply(pd.Series)
        df_complete = pd.concat([df, df_parsed], axis=1)
        df_reordered = df_complete.iloc[:, [0,1,4,5,3,2]]
        st.write(df_complete.columns)


        return categorize_transactions(df_complete).iloc[:, [0,1,4,5,3,7]]
        #return df_reordered
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

def main():
    st.title("Finance Dashboard")

    uploaded_file= st.file_uploader("Upload your finance CSV file from comdirect bank", type=["csv"])
    dummy_button = st.button("Use Dummy Data")

    if dummy_button:
        base_dir = os.path.dirname(__file__)  # Pfad zu deinem aktuellen Python-Skript
        uploaded_file = os.path.join(base_dir, "dummy", "dummy_umsätze.csv")


    if uploaded_file is not None:
        df = load_transactions(uploaded_file)

        if df is not None:
            income_df = df[df["Type"] == "Einnahme"]
            expenses_df = df[df["Type"] == "Ausgabe"]

            st.session_state.income_df = income_df.copy()
            st.session_state.expenses_df = expenses_df.copy()

            tab1, tab2 = st.tabs(["Einnahmen", "Ausgaben"])
            with tab1:
                new_category = st.text_input("New Category Name")
                add_button = st.button("Add Category")

                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.rerun()
                st.subheader("Deine Einnahmen")
                edited_df = st.data_editor(
                    st.session_state.income_df,
                    column_config={
                        "Buchungstag": st.column_config.DateColumn("Buchungstag", format="DD/MM/YYYY"),
                        "Umsatz in EUR": st.column_config.NumberColumn("Umsatz in EUR", format="%.2f €"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor"
                )

                save_button = st.button("Apply Changes", type="primary")
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row["Category"]
                        if new_category == st.session_state.expenses_df.at[idx, "Category"]:
                            continue

                        details = row["Wer"]
                        st.session_state.income_df.at[idx, "Category]"] = new_category
                        add_keyword_to_category(new_category, details)

                st.subheader("Zusammenfassung Einnahmen")
                category_totals = st.session_state.income_df.groupby("Category")["Umsatz in EUR"].sum().reset_index()
                category_totals = category_totals.sort_values("Umsatz in EUR", ascending=False)

                st.dataframe(
                    category_totals,
                    column_config={
                        "Umsatz in EUR": st.column_config.NumberColumn("Umsatz in EUR", format="%.2f €")
                    },
                    use_container_width=True,
                    hide_index=True
                             )
                        
            with tab2:
                new_category = st.text_input("New Category Name", key="New Category Name 2")
                add_button = st.button("Add Category", key="Add Category 2")

                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.rerun()
                st.subheader("Deine Einnahmen")
                edited_df = st.data_editor(
                    st.session_state.expenses_df,
                    column_config={
                        "Buchungstag": st.column_config.DateColumn("Buchungstag", format="DD/MM/YYYY"),
                        "Umsatz in EUR": st.column_config.NumberColumn("Umsatz in EUR", format="%.2f €"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor 2"
                )

                save_button = st.button("Apply Changes", type="primary", key="Apply Changes 2")
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row["Category"]
                        if new_category == st.session_state.expenses_df.at[idx, "Category"]:
                            continue

                        details = row["Wer"]
                        st.session_state.expenses_df.at[idx, "Category]"] = new_category
                        add_keyword_to_category(new_category, details)

                st.subheader("Zusammenfassung Einnahmen")
                category_totals = st.session_state.expenses_df.groupby("Category")["Umsatz in EUR"].sum().reset_index()
                category_totals = category_totals.sort_values("Umsatz in EUR", ascending=False)

                st.dataframe(
                    category_totals,
                    column_config={
                        "Umsatz in EUR": st.column_config.NumberColumn("Umsatz in EUR", format="%.2f €")
                    },
                    use_container_width=True,
                    hide_index=True
                             )

main()