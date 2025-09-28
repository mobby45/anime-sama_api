# Refactor is not a bad idea

import re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Any

import httpx

from ..episode import Episode
from ..catalogue import Catalogue
from .utils import normalize


@dataclass(frozen=True)
class EpisodeWithExtraInfo:
    warpped: Episode
    release_date: datetime | None = None
    mal_id: int | None = None
    official_title: str | None = None  # Ajout du titre officiel

    def release_year_parentheses(self) -> str:
        if self.release_date is None:
            return ""
        return f" ({self.release_date.year})"
    
    def mal_id_prefix(self) -> str:
        """Retourne le préfixe [mal-ID] si disponible"""
        if self.mal_id is None:
            return ""
        return f"[mal-{self.mal_id}] "
    
    def get_official_title(self) -> str:
        """Retourne le titre officiel ou le nom de la série par défaut"""
        if self.official_title:
            return self.official_title
        return self.warpped.serie_name
    
    def formatted_episode_name(self) -> str:
        """Formate le nom de l'épisode avec un numéro à 2 chiffres si c'est un numéro"""
        episode_name = self.warpped.name
        
        # Cherche un pattern comme "Episode X" ou "Épisode X" 
        episode_pattern = r'(?i)(episode|épisode)\s*(\d+)'
        match = re.search(episode_pattern, episode_name)
        
        if match:
            prefix = match.group(1)
            number = int(match.group(2))
            return re.sub(episode_pattern, f"{prefix} {number:02d}", episode_name)
        
        # Cherche juste un numéro à la fin
        number_pattern = r'\b(\d+)$'
        match = re.search(number_pattern, episode_name.strip())
        
        if match:
            number = int(match.group(1))
            return re.sub(number_pattern, f"{number:02d}", episode_name)
        
        return episode_name
    
    def formatted_serie_name(self) -> str:
        """Formate le nom de la série avec le préfixe MAL ID"""
        return self.mal_id_prefix() + self.warpped.serie_name
    
    def formatted_season_name(self) -> str:
        """Formate le nom de la saison avec un numéro à 2 chiffres si c'est une saison"""
        season_name = self.warpped.season_name
        
        # Cherche un pattern comme "Season X" ou "Saison X"
        season_pattern = r'(?i)(season|saison)\s*(\d+)'
        match = re.search(season_pattern, season_name)
        
        if match:
            prefix = match.group(1)
            number = int(match.group(2))
            return re.sub(season_pattern, f"{prefix} {number:02d}", season_name)
        
        # Pour les cas comme "Arc de X" ou autres formats spéciaux
        # On garde le nom original car ce ne sont pas des numéros de saison classiques
        return season_name


def convert_with_extra_info(
    episode: Episode, serie: Catalogue | None = None
) -> EpisodeWithExtraInfo:
    release_date = None
    mal_id = None
    official_title = None
    
    if serie is not None:
        release_date = get_serie_release_date(serie)
        mal_data = get_serie_mal_data(serie, episode)  # Récupère les données MAL complètes
        if mal_data:
            mal_id = mal_data.get("mal_id")
            official_title = mal_data.get("title")
    
    return EpisodeWithExtraInfo(
        warpped=episode, 
        release_date=release_date, 
        mal_id=mal_id,
        official_title=official_title
    )


en2fr_genre = {
    "Comedy": "Comédie",
    "Gourmet": "Gastronomie",
    "Drama": "Drame",
    "Adventure": "Aventure",
    "Mystery": "Mystère",
    "Sci-Fi": "Science-fiction",
    "Sports": "Tournois",
    "Supernatural": "Surnaturel",
    "Girls Love": "Yuri",
    "Horror": "Horreur",
    "Fantasy": "Fantastique",
}


def get_serie_release_date(serie: Catalogue) -> datetime | None:
    try:
        anime = _get_mal_listing(serie)
        if anime is None:
            return None

        iso_date = anime.get("aired", {}).get("from")
        if iso_date is None:
            return None

        return datetime.fromisoformat(iso_date)
    except httpx.HTTPStatusError:
        return None


def get_serie_mal_data(serie: Catalogue, episode: Episode | None = None) -> dict | None:
    """Récupère les données MAL complètes (ID et titre) de la série ou de l'épisode spécifique"""
    try:
        # Si on a un épisode spécifique, vérifier si c'est un contenu spécial
        if episode is not None:
            episode_name_lower = episode.name.lower()
            season_name_lower = episode.season_name.lower()
            
            # Vérifier si c'est clairement un film/contenu spécial
            special_keywords = ["movie", "film", "ova", "ona", "special", "recap"]
            is_special_content = any(keyword in episode_name_lower or keyword in season_name_lower 
                                   for keyword in special_keywords)
            
            # Seulement chercher un contenu spécifique si c'est clairement spécial
            if is_special_content:
                specific_anime = _get_mal_listing_for_episode_cached(
                    serie.name,
                    tuple(serie.alternative_names),
                    episode.name,
                    episode.season_name,
                    tuple(serie.genres),
                    serie.is_anime
                )
                if specific_anime is not None:
                    return {
                        "mal_id": specific_anime.get("mal_id"),
                        "title": _get_best_title(specific_anime)
                    }
        
        # Pour les séries normales ou si aucun contenu spécial trouvé, 
        # récupérer les données de la série principale
        anime = _get_mal_listing(serie)
        if anime is None:
            return None

        return {
            "mal_id": anime.get("mal_id"),
            "title": _get_best_title(anime)
        }
    except httpx.HTTPStatusError:
        return None


def _get_best_title(anime: dict) -> str:
    """Récupère le meilleur titre disponible (priorité au titre anglais ou par défaut)"""
    titles = anime.get("titles", [])
    
    # Priorité 1: Titre anglais
    for title in titles:
        if title.get("type") == "English":
            return title.get("title", "")
    
    # Priorité 2: Titre par défaut
    for title in titles:
        if title.get("type") == "Default":
            return title.get("title", "")
    
    # Priorité 3: Premier titre disponible
    if titles:
        return titles[0].get("title", "")
    
    # Fallback: titre principal
    return anime.get("title", "Unknown")


@lru_cache(maxsize=128)
def _get_mal_listing_for_episode_cached(
    serie_name: str,
    alternative_names: tuple[str, ...],
    episode_name: str,
    season_name: str,
    genres: tuple[str, ...],
    is_anime: bool
) -> None | Any:
    """Version cachée de la recherche spécifique pour un épisode (film, OVA, etc.)"""
    if not is_anime:
        return None

    # Termes qui indiquent un contenu spécial (film, OVA, etc.)
    special_keywords = ["movie", "film", "ova", "ona", "special", "recap"]
    episode_name_lower = episode_name.lower()
    season_name_lower = season_name.lower()
    
    # Vérifie si c'est un contenu spécial
    is_special_content = any(keyword in episode_name_lower or keyword in season_name_lower 
                           for keyword in special_keywords)
    
    if not is_special_content:
        return None  # Pas un contenu spécial, utiliser la recherche normale
    
    # Construire des requêtes de recherche spécifiques
    search_queries = []
    
    # Priorité au nom de l'épisode car c'est là que se trouve le nom du film
    search_queries.append(f"{serie_name} {episode_name}")
    
    # Essayer avec le nom de la série + nom de la saison (si différent)
    if season_name != episode_name:
        search_queries.append(f"{serie_name} {season_name}")
    
    # Essayer avec les noms alternatifs + nom de l'épisode
    for alt_name in alternative_names:
        search_queries.append(f"{alt_name} {episode_name}")
        if season_name != episode_name:
            search_queries.append(f"{alt_name} {season_name}")
    
    # Essayer juste le nom de l'épisode (parfois le nom du film suffit)
    if len(episode_name) > 3:  # Éviter les noms trop courts
        search_queries.append(episode_name)
    
    for query in search_queries:
        i = 0
        while True:
            response = httpx.get(f"https://api.jikan.moe/v4/anime?q={query}&limit=10")
            i += 1
            if response.status_code != 429 or i > 9:
                break

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            continue
            
        animes = response.json().get("data", [])

        for anime in animes:
            # Vérifier le type (Movie, OVA, Special, etc.)
            anime_type = anime.get("type", "").lower()
            
            # Si on cherche un film et que c'est un film, ou si on cherche un OVA et que c'est un OVA
            type_match = (
                (("movie" in episode_name_lower or "film" in episode_name_lower) and anime_type == "movie") or
                (("ova" in episode_name_lower or "ova" in season_name_lower) and anime_type == "ova") or
                (("special" in episode_name_lower or "special" in season_name_lower) and anime_type == "special") or
                (anime_type in ["movie", "ova", "special"])  # Accepter aussi si c'est juste un type spécial
            )
            
            if type_match:
                # Vérifier si les titres correspondent
                for title in anime.get("titles", []):
                    title_text = normalize(title.get("title", ""))
                    query_normalized = normalize(query)
                    episode_normalized = normalize(episode_name)
                    
                    # Vérifications de correspondance plus flexibles
                    title_matches = (
                        query_normalized in title_text or 
                        title_text in query_normalized or
                        episode_normalized in title_text or
                        title_text in episode_normalized
                    )
                    
                    if title_matches:
                        # Vérification additionnelle des genres (plus souple pour les films)
                        anime_genres = [genre.get("name") for genre in anime.get("genres", [])]
                        not_corresponding_genres = [
                            genre
                            for genre in anime_genres
                            if genre not in genres
                            and en2fr_genre.get(genre) not in genres
                        ]
                        
                        # Condition encore plus souple pour les films/OVA
                        if len(anime_genres) == 0 or len(not_corresponding_genres) / len(anime_genres) < 0.7:
                            return anime

    return None


def _is_movie_title(title: str) -> bool:
    """Détecte si un titre contient des mots-clés indiquant un film"""
    movie_keywords = ["movie", "film", "the movie", "le film"]
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in movie_keywords)


@lru_cache(maxsize=128)
def _get_mal_listing(serie: Catalogue) -> None | Any:
    if not serie.is_anime:
        return None

    for name in [serie.name] + list(serie.alternative_names):
        i = 0
        while True:
            response = httpx.get(f"https://api.jikan.moe/v4/anime?q={name}&limit=10")
            i += 1
            if response.status_code != 429 or i > 9:
                break

        response.raise_for_status()
        animes = response.json().get("data", [])

        # Séparer les résultats en séries et films
        tv_series = []
        other_types = []
        
        for anime in animes:
            anime_type = anime.get("type", "").lower()
            if anime_type in ["tv", "ona"]:  # Types de séries
                tv_series.append(anime)
            else:
                other_types.append(anime)
        
        # Priorité aux séries TV/ONA, puis aux autres types
        for anime_list in [tv_series, other_types]:
            for anime in anime_list:
                anime_type = anime.get("type", "").lower()
                
                # Pour les séries normales, éviter les films sauf si explicitement recherché
                should_skip_movie = (
                    anime_type == "movie" and 
                    not _is_movie_title(name) and
                    len(tv_series) > 0  # Il y a des séries TV disponibles
                )
                
                if should_skip_movie:
                    continue
                
                for title in anime.get("titles", []):
                    name_normalized = normalize(name)
                    title_normalized = normalize(title.get("title", ""))
                    anime_genres = [genre.get("name") for genre in anime.get("genres", [])]
                    
                    # Vérifier si le titre contient des mots-clés de film alors qu'on ne recherche pas un film
                    title_text = title.get("title", "")
                    if (not _is_movie_title(name) and 
                        _is_movie_title(title_text) and 
                        anime_type == "movie" and 
                        len(tv_series) > 0):
                        continue
                    
                    if name_normalized == title_normalized:
                        # Also guess work but eliminate edge case like fate
                        if len(anime_genres) == 0 and len(serie.genres) != 0:
                            continue

                        return anime
                        
                    if name_normalized in title_normalized or title_normalized in name_normalized:
                        # Because this condition is not a guarantee, we do an additionnal screenning base on corresponding genres
                        not_corresponding_genres = [
                            genre
                            for genre in anime_genres
                            if genre not in serie.genres
                            and en2fr_genre.get(genre) not in serie.genres
                        ]

                        # Very scientific formula. I'm joking it just guess work
                        if (len(anime_genres) == 0 or 
                            len(not_corresponding_genres) / len(anime_genres) < 0.35) and (
                            len(anime_genres) != 0 or len(serie.genres) == 0
                        ):
                            return anime

    return None