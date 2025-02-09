import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Définir une liste de dictionnaires pour les sites à scraper
sites_disponibles = {
    "Chiens a vendre": "https://sn.coinafrique.com/categorie/chiens?page=",
    "Moutons à vendre": "https://sn.coinafrique.com/categorie/moutons?page=",
    "Poules, lapins et pigeons à vendre": "https://sn.coinafrique.com/categorie/poules-lapins-et-pigeons?page=",
    "Autres animaux": "https://sn.coinafrique.com/categorie/autres-animaux?page="
}

# Page d'accueil
def home():
    st.image("Data/logo_DIT.png")
    st.title("Bienvenue dans l'Application de Scraping d'Animaux")
    st.markdown("""
        Cette application permet de scraper des annonces d'animaux à partir du site CoinAfrique.
        Sélectionnez une catégorie et le nombre de pages à scraper, puis visualisez et téléchargez les données.
    """)
    if st.button("Commencer"):
        st.session_state.page = "scrapping"

# Page de Scrapping
def scrapping():
    st.image("Data/logo_DIT.png")
    st.title("Application de Scraping d'Animaux")
    st.markdown("""
        Scrappez des données d'animaux à partir de différentes catégories.
    """)
    
    site_choisi = st.selectbox("Choisissez une catégorie à scraper :", options=list(sites_disponibles.keys()))
    nombre_pages = st.slider("Nombre de pages à scraper :", min_value=1, max_value=20, value=1)
    
    if st.button("Lancer le scraping"):
        st.info(f"Scraping en cours pour la catégorie : {site_choisi} (nombre de pages : {nombre_pages})...")

        base_url = sites_disponibles[site_choisi]
        
        def scraper_animaux(base_url, num_pages):
            df = pd.DataFrame()
            for p in range(1, num_pages + 1):
                url = f"{base_url}{p}"
                res = requests.get(url)  # Récupération du code HTML de la page
                soup = BeautifulSoup(res.text, 'html.parser')  # Stocker le code HTML dans un objet BeautifulSoup
                containers = soup.find_all('div', class_='col s6 m4 l3')
                data = []
                for container in containers:
                    try:
                        # Récupérer l'URL de l'annonce
                        url_container = container.find('a', class_='card-image ad__card-image waves-block waves-light')['href']
                        url_container = f"https://sn.coinafrique.com{url_container}"
                        
                        # Accéder à la page de l'annonce
                        res_c = requests.get(url_container)
                        soup_c = BeautifulSoup(res_c.text, 'html.parser')
                        
                        # Extraire les informations
                        nom = soup_c.find('span', class_='breadcrumb cible').text.strip()
                        prix = soup_c.find('p', class_='price').text.replace(' ', '').replace('CFA', '').strip()
                        adresse = soup_c.find_all('span', class_='valign-wrapper')[1].text.strip()
                        img_link = soup_c.find('div', class_='swiper-wrapper').div.get('style').split('(')[1].replace(')', '').strip()
                        
                        # Ajouter les données à la liste
                        dic = {
                            'Nom': nom,
                            'Prix': prix,
                            'Adresse': adresse,
                            'Image Link': img_link
                        }
                        data.append(dic)
                    except Exception as e:
                        st.error(f"Erreur lors du scraping d'une annonce : {e}")
                
                # Ajouter les données de la page au DataFrame
                df = pd.concat([df, pd.DataFrame(data)], ignore_index=True)
            return df
        
        resultat = scraper_animaux(base_url, nombre_pages)
        
        if not resultat.empty:
            st.success("Scraping terminé avec succès !")
            st.data_editor(resultat, hide_index=True)
            
            # Télécharger les données en CSV
            csv = resultat.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Télécharger les données en CSV",
                data=csv,
                file_name="resultats_scraping.csv",
                mime="text/csv"
            )
        else:
            st.warning("Aucune donnée n'a été récupérée.")

# Charger les données à utiliser sur le dashboard
def load_data():
    try:
        Moutons_a_vendre_cleaned = pd.read_csv('Data/Moutons_a_vendre_cleaned.csv')
        Chiens_a_vendre = pd.read_csv('Data/Chiens_a_vendre_cleaned.csv')
        Poules_pigeons_a_vendre = pd.read_csv('Data/Poules_lapins_pigeons_a_vendre_cleaned.csv')
        Autres_animaux = pd.read_csv('Data/Autres_animaux_a_vendre_cleaned.csv')
        return Moutons_a_vendre_cleaned, Chiens_a_vendre, Poules_pigeons_a_vendre, Autres_animaux
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return None, None, None, None

Moutons_a_vendre_cleaned, Chiens_a_vendre, Poules_pigeons_a_vendre, Autres_animaux = load_data()

# Creation de dashboard
def dashboard():
    st.image("Data/logo_DIT.png")
    st.title("Dashboard d'analyse des annonces d'animaux")
    st.subheader("Voici les données récupérées et les analyses effectuées.")
    
    # Page Moutons à vendre
    annonces = st.selectbox("Choisissez une catégorie :", ["Moutons à vendre", "Chiens à vendre", "Poules, lapins et pigeons à vendre", "Autres animaux"])
    
    def get_data(annonces):
        if annonces == "Moutons à vendre":
            return Moutons_a_vendre_cleaned
        elif annonces == "Chiens à vendre":
            return Chiens_a_vendre
        elif annonces == "Poules, lapins et pigeons à vendre":
            return Poules_pigeons_a_vendre
        else:
            return Autres_animaux
    
    data = get_data(annonces)
    
    if data is not None:
        # Convertir la colonne 'Prix' en numérique
        data['prix'] = pd.to_numeric(data['prix'], errors='coerce')
        
        if st.button('Afficher le diagramme des Adresses'):
            st.header('Diagramme des Adresses')
            fig, ax = plt.subplots(figsize=(15, 8))
            sns.countplot(x='adresse', data=data, palette="viridis")
            ax.set_title(f'Distribution par Adresse ({annonces})')
            ax.set_xlabel('Adresse')
            ax.set_ylabel('Nombre d\'annonces')
            plt.xticks(rotation=90)
            st.pyplot(fig)
        
        # Statistics descriptive
        if st.button("Satistique"):
            st.header("Statistique descriptive")
            st.write(get_data(annonces).describe())
        
# Formulaires d'évaluation
def evaluation():
    st.image("Data/logo_DIT.png")
    st.header("Formulaire d'évaluation")
    st.write("Merci de bien vouloir remplir le formulaire pour nous aider à améliorer notre application.")
    st.markdown("[Cliquez pour renseigner le formulaire](https://ee.kobotoolbox.org/x/motvWPy9)")

# Menu principal
pages = {
    "Accueil": home,
    "Scrapping": scrapping,
    "Tableau de Bord": dashboard,
    "Évaluation": evaluation
}

st.sidebar.title("Navigation")
selected_page = st.sidebar.radio("Pages", list(pages.keys()))

# Gestion des pages
if selected_page in pages:
    pages[selected_page]()