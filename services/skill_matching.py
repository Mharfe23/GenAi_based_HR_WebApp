from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional, Set
import re
try:
    import json5  # type: ignore
except Exception:  # Fallback if json5 isn't installed
    import json as json5  # type: ignore
import logging

from embeddings.chroma_gemini_embedding import find_similar_skill as chroma_find_similar


logging.basicConfig(
    level=logging.WARNING,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class SkillMatchingStrategy(ABC):
    @abstractmethod
    def map_skills_to_reference(
        self,
        skills_cv: Iterable[str],
        technologies_reference: Set[str],
        llm_client=None,
    ) -> Dict[str, Optional[str]]:
        """
        Returns a mapping from each input skill (lowercased) to either:
        - a normalized skill present in technologies_reference, or
        - None if no match is found.
        """
        pass


class ChromaSimilarityStrategy(SkillMatchingStrategy):
    def map_skills_to_reference(
        self,
        skills_cv: Iterable[str],
        technologies_reference: Set[str],
        llm_client=None,
    ) -> Dict[str, Optional[str]]:
        mapping: Dict[str, Optional[str]] = {}
        for skill in skills_cv:
            lower_skill = skill.strip().lower()
            if lower_skill in technologies_reference:
                mapping[lower_skill] = lower_skill
                continue
            try:
                similar = chroma_find_similar(lower_skill)
                if isinstance(similar, str):
                    normalized = similar.strip().lower()
                    if normalized in technologies_reference:
                        mapping[lower_skill] = normalized
                        continue
                mapping[lower_skill] = None
            except Exception as e:
                logger.warning(f"Chroma similarity failed for '{lower_skill}': {e}")
                mapping[lower_skill] = None
        return mapping


class LLMNormalizationStrategy(SkillMatchingStrategy):
    def _build_prompt(self, skills_cv: List[str], technologies_reference: List[str]) -> str:
        skills_str = ", ".join(skills_cv)
        techno_str = ", ".join(technologies_reference)
        prompt = f"""
OBJECTIF CRITIQUE : Mapper les compétences du CV vers le RÉFÉRENTIEL EXISTANT ci-dessous.

CV - COMPÉTENCES DÉTECTÉES :
{skills_str}

RÉFÉRENTIEL OFFICIEL (UTILISER EXCLUSIVEMENT CES VALEURS, SANS AUCUNE MODIFICATION) :
{techno_str}

RÈGLES STRICTES :
1. Tu dois faire correspondre chaque compétence du CV à UNE ET UNE SEULE valeur EXACTE du référentiel.
2. Si plusieurs correspondances sont possibles, choisis celle qui est exactement écrite dans le référentiel.
3. NE PAS :
   - reformuler les acronymes (ex : JMS ≠ Java Message Service)
   - corriger l'orthographe
   - enrichir ou transformer les noms
4. Si une compétence n'existe PAS dans le référentiel, alors :
   - "correspondance_trouvee": false
   - "skill_normalise": doit rester égal au mot du CV
5. Assigne un niveau arbitraire (débutant, intermédiaire, avancé) selon ton jugement.

FORMAT DE RÉPONSE (uniquement ce JSON, sans texte autour) :
{{  
  "technologies_normalisees": [  
    {{  
      "skill_cv_original": "Spring",  
      "skill_normalise": "Spring Boot", 
      "correspondance_trouvee": true  
    }},  
    {{  
      "skill_cv_original": "TechInconnue",  
      "skill_normalise": "TechInconnue",
      "correspondance_trouvee": false  
    }}  
  ]  
}}
"""
        return prompt

    def map_skills_to_reference(
        self,
        skills_cv: Iterable[str],
        technologies_reference: Set[str],
        llm_client=None,
    ) -> Dict[str, Optional[str]]:
        skills_list = [s.strip() for s in skills_cv if s and s.strip()]
        if not skills_list:
            return {}

        # Prepare reference in lower-case (the public API expects lower-case outputs like Chroma)
        ref_lower = {t.strip().lower() for t in technologies_reference}

        # 1) Pre-map exact matches to themselves (aligns with Chroma behavior)
        mapping: Dict[str, Optional[str]] = {}
        to_normalize: List[str] = []
        for s in skills_list:
            key = s.lower()
            if key in ref_lower:
                mapping[key] = key
            else:
                to_normalize.append(s)

        if not to_normalize:
            return mapping

        if llm_client is None:
            # No LLM available: return None for all non-matching skills (align with Chroma when it fails)
            for s in to_normalize:
                mapping[s.lower()] = None
            return mapping

        # 2) Ask LLM only for the non-matching skills
        prompt = self._build_prompt(to_normalize, sorted(list(ref_lower)))

        try:
            raw_response = llm_client.generate(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            for s in to_normalize:
                mapping[s.lower()] = None
            return mapping

        try:
            cleaned = raw_response.strip()
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if not match:
                logger.warning("Aucun JSON trouvé dans la normalisation.")
                for s in to_normalize:
                    mapping[s.lower()] = None
                return mapping

            json_block = match.group(0)
            data = json5.loads(json_block)
            items = data.get("technologies_normalisees", [])

            for item in items:
                original = str(item.get("skill_cv_original", "")).strip().lower()
                normalized = str(item.get("skill_normalise", "")).strip().lower()
                found = bool(item.get("correspondance_trouvee", False))

                if not original:
                    continue

                if found and normalized in ref_lower:
                    mapping[original] = normalized
                else:
                    mapping[original] = None

            # Ensure all LLM-processed inputs are present in the mapping
            for s in to_normalize:
                key = s.lower()
                if key not in mapping:
                    mapping[key] = None

            logger.info(f"{sum(1 for v in mapping.values() if v)} compétences normalisées via LLM")
            return mapping

        except Exception as e:
            logger.error(f"Erreur inattendue lors de la normalisation : {e}")
            for s in to_normalize:
                mapping[s.lower()] = None
            return mapping


def get_skill_match_strategy(name: str) -> SkillMatchingStrategy:
    normalized_name = (name or "").strip().lower()
    if normalized_name in {"chroma", "similarity", "vector", "default"}:
        return ChromaSimilarityStrategy()
    if normalized_name in {"llm", "normalizer", "llm_normalization", "llm-normalization"}:
        return LLMNormalizationStrategy()
    # Fallback to chroma
    return ChromaSimilarityStrategy()


