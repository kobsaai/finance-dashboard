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
    
def update_category_for_all(df, edited_df, column_name="Wer"):
    """
    Aktualisiert alle Einträge mit demselben 'Wer'-Wert auf die neue Kategorie.
    """
    for idx, row in edited_df.iterrows():
        new_category = row["Category"]
        if new_category == df.at[idx, "Category"]:
            continue  # Keine Änderung notwendig

        # Finde alle Zeilen mit demselben 'Wer'-Wert und update sie
        df.loc[df[column_name] == row[column_name], "Category"] = new_category

def apply_changes(edited_df, original_df, is_income=True):
    for idx, row in edited_df.iterrows():
        new_category = row["Category"]
        old_category = original_df.at[idx, "Category"]
        
        if new_category == old_category:
            continue

        details = row["Wer"]
        original_df.at[idx, "Category"] = new_category
        move_keyword_between_categories(old_category, new_category, details)

def move_keyword_between_categories(old_category: str, new_category: str, keyword: str):
    # Entferne das Keyword aus der alten Kategorie
    if old_category in st.session_state.categories:
        if keyword in st.session_state.categories[old_category]:
            st.session_state.categories[old_category].remove(keyword)
    
    # Füge das Keyword zur neuen Kategorie hinzu
    add_keyword_to_category(new_category, keyword)


def main():
    st.title("Finance Dashboard")

    uploaded_file = st.file_uploader("Upload your finance CSV file from comdirect bank", type=["csv"])
    dummy_button = st.button("Use Dummy Data")

    if dummy_button:
        base_dir = os.path.dirname(__file__)
        uploaded_file = os.path.join(base_dir, "dummy", "dummy_umsätze.csv")

    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        st.session_state.file_loaded = True

    if st.session_state.get("uploaded_file") is not None:
        if st.session_state.get("file_loaded"):
            df = load_transactions(st.session_state.uploaded_file)


            if df is not None:
                st.session_state.income_df = df[df["Type"] == "Einnahme"].copy()
                st.session_state.expenses_df = df[df["Type"] == "Ausgabe"].copy()

                st.header("Kategorien verwalten")
                new_category = st.text_input("Neue Kategorie hinzufügen")
                add_button = st.button("Kategorie hinzufügen")
                delete_button = st.button("Kategorien Löschen")

                if delete_button:
                    # Datei löschen
                    if os.path.exists("categories.json"):
                        os.remove("categories.json")
                        st.success("Die Kategorien wurden erfolgreich gelöscht!")
                        # Optional: Auch die SessionState leeren
                        del st.session_state.categories
                        st.rerun()
                    else:
                        st.warning("Keine Kategorien-Datei gefunden.")


                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.rerun()

                st.divider()

                tab1, tab2 = st.tabs(["Einnahmen", "Ausgaben"])

                with tab1:
                    st.subheader("Deine Einnahmen")

                    edited_income_df = st.data_editor(
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
                        key="category_editor_income",
                        on_change=lambda: update_category_for_all(
                            st.session_state.income_df, edited_income_df
                        )  # <-- Automatische Aktualisierung!
                    )

                with tab2:
                    st.subheader("Deine Ausgaben")

                    edited_expenses_df = st.data_editor(
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
                        key="category_editor_expenses",
                        on_change=lambda: update_category_for_all(
                            st.session_state.expenses_df, edited_expenses_df
                        )  # <-- Automatische Aktualisierung!
                    )

                st.divider()
                save_button = st.button("Alle Änderungen übernehmen", type="primary")

                if save_button:
                    apply_changes(edited_income_df, st.session_state.income_df)
                    apply_changes(edited_expenses_df, st.session_state.expenses_df)
                    st.session_state.file_loaded = True
                    st.rerun()  
                    st.success("Alle Änderungen wurden übernommen!")

main()
