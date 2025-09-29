import requests
import json
import os
import re

# --- Configurações ---
M3U_FILE_PATH = "D:/Projetos/VenturaStudio-Repositorio/Séries.m3u"
OUTPUT_JSON_PATH = "Series_com_TMDB.json"
TMDB_API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0NTVjYTdhNTM4MjA0NTBmMjM5Y2E1YmYxMDQ1ODJjNCIsIm5iZiI6MTc1MjY4Njg3NS41OTcsInN1YiI6IjY4NzdlMTFiYzZlZjc3ZGJkMTQzZDNjOCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.H7orvOjrk5A9XbrMrRc_mmwZ0ylPReyGoQPQCDdH4pE"
TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/original"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

# --- Funções ---

def parse_m3u_manually(file_path):
    items = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    pattern = re.compile(r'(\S+?)="([^"]*?)"')
    
    for i, line in enumerate(lines):
        if line.startswith('#EXTINF'):
            attrs = dict(pattern.findall(line))
            name = attrs.get('tvg-name', '')
            if not name:
                name_match = re.search(r',(.+)', line)
                name = name_match.group(1).strip() if name_match else 'Nome não encontrado'

            group_title = attrs.get('group-title', '')
            if not group_title:
                match = re.search(r'group="([^"]*?)"', line)
                group = match.group(1) if match else 'Sem Categoria'
            else:
                group = group_title

            url = lines[i + 1].strip() if i + 1 < len(lines) else None
            tvg_logo = attrs.get('tvg-logo')
            
            if url and not url.startswith('#'):
                items.append({
                    "name": name,
                    "group": group,
                    "logo": tvg_logo,
                    "url": url
                })
    return items

def search_tv_show_on_tmdb(series_title, api_token):
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
        
        return {
            "tmdb_id": first_result.get("id"),
            "backdrop_path": f"{TMDB_IMAGE_BASE_URL}{first_result.get('backdrop_path')}" if first_result.get('backdrop_path') else None,
            "poster_path": f"{TMDB_IMAGE_BASE_URL}{first_result.get('poster_path')}" if first_result.get('poster_path') else None,
            "overview": first_result.get("overview", "Sinopse não encontrada."),
            "name": first_result.get("name")
        }
            
    except requests.exceptions.RequestException as e:
        print(f"    [Erro de API] Não foi possível conectar ao TMDB para '{series_title}': {e}")
        return None

def get_brazil_certification(tv_id, api_token):
    url = f"{TMDB_API_BASE_URL}/tv/{tv_id}/content_ratings"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_token}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        for result in data.get("results", []):
            if result.get("iso_3166_1") == "BR":
                return {
                    "ageGroup": result.get("rating", "Indisponível"),
                    "descriptors": []
                }
        return {
            "ageGroup": "Indisponível",
            "descriptors": []
        }

    except requests.exceptions.RequestException as e:
        print(f"[Erro] Falha ao buscar classificação indicativa para série ID {tv_id}: {e}")
        return {
            "ageGroup": "Indisponível",
            "descriptors": []
        }

def extract_episode_info(name):
    clean_name = re.sub(r'\[.*?\]|\(.*?\)|(\d{4})', '', name).strip()
    match = re.search(r'(S\d+E\d+)', name, re.IGNORECASE)
    if match:
        episode_number = match.group(1).upper()
        series_name = clean_name.replace(match.group(0), '').strip()
        series_name = re.sub(r'[,\s]+$', '', series_name)
        return series_name, episode_number
    return clean_name, None

# --- Lógica Principal ---

def main():
    if not os.path.exists(M3U_FILE_PATH):
        print(f"[ERRO] O arquivo de entrada não foi encontrado em: {M3U_FILE_PATH}")
        return

    print(f"Analisando o arquivo M3U: {M3U_FILE_PATH}")
    movies_from_m3u = parse_m3u_manually(M3U_FILE_PATH)
    total_items = len(movies_from_m3u)
    print(f"Encontrados {total_items} itens no arquivo M3U.")

    series_dict = {}
    print("\n--- Agrupando episódios por série ---")
    for item in movies_from_m3u:
        full_name = item.get("name", "Nome não encontrado").strip()
        categoria = item.get("group", "Sem Categoria").strip()
        tvg_logo = item.get("logo")
        link = item.get("url")
        
        series_name, episode_number = extract_episode_info(full_name)

        if not episode_number:
            print(f"[Aviso] Item sem formato SXXEXX, ignorando: '{full_name}'")
            continue

        if series_name not in series_dict:
            series_dict[series_name] = {
                "name": series_name,
                "category": categoria,
                "tmdb_info": {},
                "episodes": {}
            }
        
        series_dict[series_name]["episodes"][episode_number] = {
            "full_name": full_name,
            "link": link,
            "m3u_logo": tvg_logo
        }

    total_series = len(series_dict)
    print(f"\n--- Enriquecendo dados de {total_series} séries com TMDB ---")

    enriched_series_list = []
    for index, (series_name, series_data) in enumerate(series_dict.items()):
        print(f"\n({index + 1}/{total_series}) Processando: '{series_name}'")
        
        tmdb_info = search_tv_show_on_tmdb(series_name, TMDB_API_TOKEN)
        
        if tmdb_info:
            if tmdb_info.get("tmdb_id"):
                certification_info = get_brazil_certification(tmdb_info["tmdb_id"], TMDB_API_TOKEN)
                tmdb_info["certification"] = certification_info
            series_data['tmdb_info'] = tmdb_info
            print(f"    Série salva na categoria '{series_data['category']}'.") 
            print(f"    [Sucesso] Dados do TMDB encontrados para '{series_name}'.")
        else:
            series_data['tmdb_info'] = {
                "tmdb_id": None,
                "backdrop_path": None,
                "poster_path": series_data['episodes'][next(iter(series_data['episodes']))].get('m3u_logo'),
                "overview": "Sinopse não encontrada.",
                "name": series_name,
                "certification": {
                    "ageGroup": "Indisponível",
                    "descriptors": []
                }
            }
            print(f"    [Aviso] Nenhum dado encontrado no TMDB para '{series_name}'.")

        enriched_series_list.append(series_data)
        
    print(f"\nSalvando a lista completa de séries no arquivo: {OUTPUT_JSON_PATH}")
    try:
        with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(enriched_series_list, f, indent=4, ensure_ascii=False)
        print("Arquivo JSON gerado com sucesso! ✅")
    except IOError as e:
        print(f"[ERRO] Não foi possível salvar o arquivo JSON: {e}")

if __name__ == "__main__":
    main()