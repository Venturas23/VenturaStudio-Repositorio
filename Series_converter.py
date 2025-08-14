import requests
import json
import os
import re
from m3u_parser import M3uParser

# --- Configurações ---
# ATENÇÃO: VERIFIQUE E ATUALIZE ESTES CAMINHOS E O SEU TOKEN
M3U_FILE_PATH = "D:/Projetos/VenturaStudio-Repositorio/Séries.m3u"
OUTPUT_JSON_PATH = "Series_com_TMDB.json"
NEW_M3U_FILE_PATH = "D:/Projetos/VenturaStudio-Repositorio/Séries_com_capa.m3u"
TMDB_API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0NTVjYTdhNTM4MjA0NTBmMjM5Y2E1YmYxMDQ1ODJjNCIsIm5iZiI6MTc1MjY4Njg3NS41OTcsInN1YiI6IjY4NzdlMTFiYzZlZjc3ZGJkMTQzZDNjOCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.H7orvOjrk5A9XbrMrRc_mmwZ0ylPReyGoQPQCDdH4pE"
TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/original"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

# --- Funções ---

def search_tv_show_on_tmdb(series_title, api_token):
    """
    Busca por uma série no TMDB, retorna os dados completos e
    tenta obter a capa do primeiro episódio se não houver pôster da série.
    """
    if not series_title:
        return None
    
    search_url = f"{TMDB_API_BASE_URL}/search/tv"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    params = {
        "query": series_title,
        "include_adult": False,
        "language": "pt-BR",
        "page": 1
    }
    
    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("results"):
            return None
        
        first_result = data["results"][0]
        series_id = first_result.get("id")
        
        # Inicia com as informações básicas
        backdrop_path = f"{TMDB_IMAGE_BASE_URL}{first_result.get('backdrop_path')}" if first_result.get('backdrop_path') else None
        poster_path = f"{TMDB_IMAGE_BASE_URL}{first_result.get('poster_path')}" if first_result.get('poster_path') else None

        # Se não houver pôster, tenta buscar a imagem do primeiro episódio
        if not poster_path and series_id:
            episode_url = f"{TMDB_API_BASE_URL}/tv/{series_id}/season/1/episode/1"
            try:
                episode_response = requests.get(episode_url, headers=headers, timeout=10)
                episode_response.raise_for_status()
                episode_data = episode_response.json()
                if episode_data.get('still_path'):
                    poster_path = f"{TMDB_IMAGE_BASE_URL}{episode_data.get('still_path')}"
                    print(f"    [Aviso] Pôster não encontrado. Usando a capa do 1º episódio para '{series_title}'.")
            except requests.exceptions.RequestException:
                pass # Ignora erros se não encontrar o episódio

        return {
            "backdrop_path": backdrop_path,
            "overview": first_result.get("overview"),
            "poster_path": poster_path
        }
            
    except requests.exceptions.RequestException as e:
        print(f"    [Erro de API] Não foi possível conectar ao TMDB para '{series_title}': {e}")
        return None

def extract_episode_info(name):
    """
    Extrai o nome da série e a numeração do episódio (SXXEXX) do nome,
    removendo informações entre colchetes, parênteses ou anos que possam atrapalhar.
    """
    # Remove texto entre parênteses, colchetes e anos
    clean_name = re.sub(r'\[.*?\]|\(.*?\)|\d{4}', '', name).strip()
    
    match = re.search(r'(S\d+E\d+)', name, re.IGNORECASE)
    if match:
        episode_number = match.group(1).upper()
        # O nome da série é o que sobra depois de remover o SXXEXX
        series_name = clean_name.replace(match.group(0), '').strip()
        return series_name, episode_number
    
    return clean_name, None

def create_new_m3u(enriched_series_list, output_file_path):
    """
    Cria um novo arquivo M3U a partir da lista de séries enriquecida.
    """
    print(f"\nGerando novo arquivo M3U em: {output_file_path}")
    
    try:
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            
            for series in enriched_series_list:
                series_logo = series.get("logo")
                
                for episode_number, episode_data in series["episodes"].items():
                    episode_link = episode_data.get("link")
                    episode_name = episode_data.get("name")
                    group_title = episode_data.get("category")
                    
                    # A logo do TMDB tem precedência
                    logo_to_use = series_logo if series_logo else episode_data.get("cover")
                    logo_attr = f'tvg-logo="{logo_to_use}"' if logo_to_use else ''
                    
                    f.write(f'#EXTINF:-1 group-title="{group_title}" {logo_attr},{episode_name}\n')
                    f.write(f'{episode_link}\n')
                    
        print("Arquivo M3U gerado com sucesso!")
    except IOError as e:
        print(f"[ERRO] Não foi possível salvar o arquivo M3U: {e}")

# --- Lógica Principal ---

def main():
    """
    Função principal que orquestra a leitura, agrupamento, enriquecimento e gravação dos dados.
    """
    if not os.path.exists(M3U_FILE_PATH):
        print(f"[ERRO] O arquivo de entrada não foi encontrado em: {M3U_FILE_PATH}")
        print("Por favor, verifique o caminho no topo do script (variável M3U_FILE_PATH).")
        return

    print(f"Analisando o arquivo M3U: {M3U_FILE_PATH}")
    parser = M3uParser(timeout=10, useragent=USER_AGENT)
    parser.parse_m3u(M3U_FILE_PATH)

    movies_from_m3u = parser.get_list()
    total_items = len(movies_from_m3u)
    print(f"Encontrados {total_items} itens no arquivo M3U.")

    series_dict = {}

    print("\n--- Agrupando episódios por série ---")
    for item in movies_from_m3u:
        full_name = item.get("name", "Nome não encontrado").strip()
        category = item.get("group-title", "Categoria não encontrada").strip()
        tvg_logo = item.get("tvg-logo")
        link = item.get("url")
        
        series_name, episode_number = extract_episode_info(full_name)

        if not episode_number:
            print(f"[Aviso] Item sem formato SXXEXX, ignorando: '{full_name}'")
            continue

        if series_name not in series_dict:
            series_dict[series_name] = {
                "name": series_name,
                "logo": tvg_logo,  # Armazena o logo original como fallback
                "category": category,
                "episodes": {}
            }
        
        series_dict[series_name]["episodes"][episode_number] = {
            "name": full_name,
            "link": link,
            "category": category,
            "cover": tvg_logo
        }

    total_series = len(series_dict)
    print(f"\n--- Enriquecendo dados de {total_series} séries com TMDB ---")

    enriched_series_list = []
    for index, (series_name, series_data) in enumerate(series_dict.items()):
        print(f"\n({index + 1}/{total_series}) Processando: '{series_name}'")
        
        # Usa o nome da série limpo para a busca
        cleaned_series_name, _ = extract_episode_info(series_name)
        tmdb_info = search_tv_show_on_tmdb(cleaned_series_name, TMDB_API_TOKEN)
        
        if tmdb_info:
            series_data['tmdb_info'] = tmdb_info
            series_data['logo'] = tmdb_info.get('poster_path') or series_data.get('logo')
            print(f"    [Sucesso] Dados do TMDB encontrados para '{series_name}'.")
        else:
            series_data['tmdb_info'] = {
                "backdrop_path": None,
                "overview": "Sinopse não encontrada.",
                "poster_path": series_data.get('logo')
            }
            print(f"    [Aviso] Nenhum dado encontrado no TMDB para '{series_name}'.")
        
        enriched_series_list.append(series_data)
        
    print(f"\nSalvando a lista completa de séries no arquivo: {OUTPUT_JSON_PATH}")
    try:
        with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(enriched_series_list, f, indent=4, ensure_ascii=False)
        print("Arquivo JSON gerado com sucesso!")
    except IOError as e:
        print(f"[ERRO] Não foi possível salvar o arquivo JSON: {e}")

    create_new_m3u(enriched_series_list, NEW_M3U_FILE_PATH)

if __name__ == "__main__":
    main()