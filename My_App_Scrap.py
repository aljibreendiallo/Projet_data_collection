import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration des options du navigateur
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage") 
chrome_options.add_argument('--disable-gpu')  # Désactive l'accélération GPU
chrome_options.add_argument('--disable-dev-shm-usage')  # Évite les erreurs de mémoire
chrome_options.add_argument('--disable-extensions')  # Désactive les extensions
chrome_options.add_argument('--disable-infobars')  # Désactive les infobars
chrome_options.add_argument('--remote-debugging-port=9222')

# Initialisation du driver avec webdriver_manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Définir une liste de dictionnaires pour les sites à scraper
sites_disponibles = {
    "Appartement à louer": "https://dakarvente.com/annonces-categorie-appartements-louer-10.html",
    "Appartement à vendre": "https://dakarvente.com/annonces-categorie-appartements-vendre-61.html",
    "Terrain à vendre": "https://dakarvente.com/annonces-categorie-terrains-vendre-13.html"
}

# Page d'accueil
def home():
    st.image("Data/logo_DIT.png")
    st.title("Bienvenue dans l'Application de Scraping Immobilier")
    st.markdown("""
        Cette application permet de scraper des annonces immobilières à partir du site Dakarvente.
        Sélectionnez un site et le nombre de pages à scraper, puis visualisez et téléchargez les données.
    """)
    st.button("Commencer", on_click=lambda: st.session_state.page == "scrapping")

# Page de Scrapping
def scrapping():
    st.image("logo_DIT.png")
    st.title("Application de Scraping Immobilier")
    st.markdown("""
        Scrappez des données immobilières à partir de différents sites.
    """)
    
    site_choisi = st.selectbox("Choisissez un site à scraper :", options=list(sites_disponibles.keys()))
    nombre_pages = st.slider("Nombre de pages à scraper :", min_value=1, max_value=70, value=1)
    
    if st.button("Lancer le scraping"):
        st.info(f"Scraping en cours pour le site : {site_choisi} (nombre de pages : {nombre_pages})...")
        url = sites_disponibles[site_choisi]
        
        def scraper_terrain_vente(url, num_pages):
            Df = pd.DataFrame()
            try:
                for p in range(1, num_pages + 1):
                    page_url = f'{url}?page=annonces_categorie&id=13&sort=&nb={p}'
                    driver.get(page_url)
                    
                    containers = driver.find_elements(By.CSS_SELECTOR, "[class='item-inner mv-effect-translate-1 mv-box-shadow-gray-1']")
                    
                    data = []
                    for container in containers:
                        try:
                            details = container.find_element(By.CLASS_NAME, "content-desc").text
                            price = container.find_element(By.CLASS_NAME, "content-price").text.strip().replace('FCFA ', '')
                            location = container.find_element(By.XPATH, '//*[@id="div-desktop"]/div/div[4]/span').text
                            image_link = container.find_element(By.XPATH, '//*[@id="div-desktop"]/div/div[1]/div[2]/h2/a[1]').get_attribute('href')
                            
                            dic = {
                                'details': details,
                                'price': price,
                                'location': location,
                                'image_link': image_link
                            }
                            data.append(dic)
                        except NoSuchElementException as e:
                            print(f"Élément non trouvé : {e}")
                        except Exception as e:
                            print(f"Erreur lors du scraping: {e}")
                    
                    Df = pd.concat([Df, pd.DataFrame(data)], ignore_index=True)
            except Exception as e:
                print(f"Erreur lors du scraping: {e}")
            return Df
        
        resultat = scraper_terrain_vente(url, nombre_pages)
        
        if not resultat.empty:
            st.success("Scraping terminé avec succès !")
            st.data_editor(resultat, hide_index=True)
            
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
appartement_a_loue_cleaned = pd.read_csv("Data/appartement_a_louer_cleaned.csv")
Appartement_a_vendre_cleaned = pd.read_csv("Data/Appartement_a_vendre_cleaned.csv")
Terrain_a_vendre_cleaned = pd.read_csv("Data/Terrain_a_vendre_cleaned.csv")

# Page Tableau de Bord
def dashboard():
    st.image("Data/logo_DIT.png")
    st.title("Tableau de Bord Immobilière")
    
    type_bien = st.selectbox("Type de bien", ["Appartements à louer", "Appartements à vendre", "Terrains à vendre"])
    
    def get_data(type_bien):
        if type_bien == "Appartements à louer":
            return appartement_a_loue_cleaned
        elif type_bien == "Appartements à vendre":
            return Appartement_a_vendre_cleaned
        elif type_bien == "Terrains à vendre":
            return Terrain_a_vendre_cleaned
    
    def get_stats(data):
        return data.describe()
    
    if st.button('Afficher le diagramme des Adresses'):
        st.header('Diagramme des Adresses')
        fig, ax = plt.subplots(figsize=(15, 8))
        sns.countplot(x='Adresse', data=get_data(type_bien), palette="viridis")
        ax.set_title(f'Distribution des Adresses ({type_bien})')
        ax.set_xlabel('Adresse')
        ax.set_ylabel('Nombre d\'annonces')
        plt.xticks(rotation=90)
        st.pyplot(fig)
    
    if st.button('Afficher la moyenne des prix par adresse'):
        st.header('Moyenne des Prix par Adresse')
        data = get_data(type_bien)
        mean_prices = data.groupby('Adresse')['Prix'].mean().reset_index()
        fig, ax = plt.subplots(figsize=(15, 8))
        sns.barplot(x='Adresse', y='Prix', data=mean_prices.sort_values(by='Prix', ascending=False), palette="viridis")
        ax.set_title(f'Moyenne des Prix par Adresse ({type_bien})')
        ax.set_xlabel('Adresse')
        ax.set_ylabel('Moyenne des Prix')
        plt.xticks(rotation=90)
        st.pyplot(fig)

# Formulaires d'évaluation
def evaluation():
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

# Fermeture du driver
driver.quit()
