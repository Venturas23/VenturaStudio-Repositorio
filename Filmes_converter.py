import requests
import json
import os
import re
from m3u_parser import M3uParser

# --- Configurações ---
M3U_FILE_PATH = "D:/Projetos/VenturaStudio-Repositorio/Filmes.m3u"
OUTPUT_JSON_PATH = "Filmes_com_TMDB.json"
TMDB_API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0NTVjYTdhNTM4MjA0NTBmMjM5Y2E1YmYxMDQ1ODJjNCIsIm5iZiI6MTc1MjY4Njg3NS41OTcsInN1YiI6IjY4NzdlMTFiYzZlZjc3ZGJkMTQzZDNjOCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.H7orvOjrk5A9XbrMrRc_mmwZ0ylPReyGoQPQCDdH4pE"
TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/original"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

# --- Funções ---

def search_movie_on_tmdb(movie_title, movie_year, api_token):
    if not movie_title:
        return None

    search_url = f"{TMDB_API_BASE_URL}/search/movie"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    params = {
        "query": movie_title,
        "include_adult": False,
        "language": "pt-BR",
        "page": 1
    }
    if movie_year:
        params['primary_release_year'] = movie_year

    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("results"):
            first_result = data["results"][0]
            backdrop_path = f"{TMDB_IMAGE_BASE_URL}{first_result.get('backdrop_path')}" if first_result.get('backdrop_path') else None
            poster_path = f"{TMDB_IMAGE_BASE_URL}{first_result.get('poster_path')}" if first_result.get('poster_path') else None

            return {
                "id": first_result.get("id"),
                "backdrop_path": backdrop_path,
                "overview": first_result.get("overview"),
                "poster_path": poster_path
            }

    except requests.exceptions.RequestException as e:
        print(f"[Erro de API] Não foi possível conectar ao TMDB para '{movie_title}': {e}")
    
    return None

def get_brazil_certification(movie_id, api_token):
    url = f"{TMDB_API_BASE_URL}/movie/{movie_id}/release_dates"
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
                release_info = result.get("release_dates", [])
                if release_info:
                    certification = release_info[0].get("certification", "Indisponível")
                    descriptors = release_info[0].get("descriptors", [])
                    return {
                        "ageGroup": certification,
                        "descriptors": descriptors
                    }
        return {
            "ageGroup": "Indisponível",
            "descriptors": []
        }

    except requests.exceptions.RequestException as e:
        print(f"[Erro] Falha ao buscar classificação indicativa para ID {movie_id}: {e}")
        return {
            "ageGroup": "Indisponível",
            "descriptors": []
        }

# --- Lógica Principal ---

def main():
    if not os.path.exists(M3U_FILE_PATH):
        print(f"[ERRO] O arquivo de entrada não foi encontrado em: {M3U_FILE_PATH}")
        return

    print(f"Analisando o arquivo M3U: {M3U_FILE_PATH}")
    parser = M3uParser(timeout=10, useragent=USER_AGENT)
    parser.parse_m3u(M3U_FILE_PATH)
    
    movies_from_m3u = parser.get_list()
    total_movies = len(movies_from_m3u)
    print(f"Encontrados {total_movies} itens no arquivo M3U.")

    enriched_movie_list = []

    for index, movie_data in enumerate(movies_from_m3u):
        movie_name_raw = movie_data.get("name")
        full_name = movie_name_raw.strip() if movie_name_raw else "Nome não encontrado"

        movie_name = re.sub(r'\(4K\)|\[4K\]|4K|\(HD\)|\[HD\]|\(Dublado\)|\[Dublado\]|\[HDR\]|\[Hybrid\]|\[Dublagem Nao Oficial\]|\[CAM\]|\[Corte do Diretor\]|\[L\]|\[Libras\]|\[LIBRAS\]\[Cinema\]', '', full_name, flags=re.IGNORECASE).strip()
        movie_year = None

        year_match = re.search(r'\((\d{4})\)', movie_name)
        if year_match:
            movie_year = year_match.group(1)
            movie_name = re.sub(r'\s*\(\d{4}\)', '', movie_name).strip()

        print(f"\n({index + 1}/{total_movies}) Processando: '{full_name}'")
        print(f"   [Título Limpo] Usando para a busca: '{movie_name}'")

        tmdb_info = search_movie_on_tmdb(movie_name, movie_year, TMDB_API_TOKEN)

        if tmdb_info:
            if tmdb_info.get("id"):
                certification_info = get_brazil_certification(tmdb_info["id"], TMDB_API_TOKEN)
                tmdb_info["certification"] = certification_info
            movie_data['tmdb_info'] = tmdb_info
            print(f"   [Sucesso] Dados do TMDB encontrados para '{movie_name}'.")
        else:
            print(f"   [Aviso] Nenhum dado encontrado no TMDB para '{movie_name}'.")
            fallback_logo = movie_data.get("attributes", {}).get("tvg-logo")
            if fallback_logo:
                movie_data['tmdb_info'] = {
                    "backdrop_path": None,
                    "overview": "Sinopse não encontrada.",
                    "poster_path": fallback_logo,
                    "certification": {
                        "ageGroup": "Indisponível",
                        "descriptors": []
                    }
                }
                print(f"   [Fallback] Usando 'tvg-logo' do M3U como pôster.")
            else:
                movie_data['tmdb_info'] = None
                print(f"   [Falha] Nenhuma informação de imagem encontrada (TMDB ou tvg-logo).")

        enriched_movie_list.append(movie_data)

    print(f"\nSalvando a lista completa no arquivo: {OUTPUT_JSON_PATH}")
    try:
        with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(enriched_movie_list, f, indent=4, ensure_ascii=False)
        print("Arquivo JSON gerado com sucesso!")
    except IOError as e:
        print(f"[ERRO] Não foi possível salvar o arquivo JSON: {e}")

if __name__ == "__main__":
    main()