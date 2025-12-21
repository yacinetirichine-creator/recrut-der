"""
🏢 Recrut'der - Routes Entreprises
===================================
Gestion des entreprises et vérification SIRET
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from uuid import UUID

from api.models.v2_models import (
    EntrepriseCreate,
    EntrepriseUpdate,
    EntrepriseResponse
)
from api.routes.auth import get_current_user
from api.database.supabase_client import supabase
from loguru import logger


router = APIRouter()


@router.post("/", response_model=EntrepriseResponse, status_code=status.HTTP_201_CREATED)
async def create_entreprise(
    entreprise_data: EntrepriseCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 Créer une nouvelle entreprise
    
    Accessible uniquement aux recruteurs.
    Vérification SIRET optionnelle via API entreprise.data.gouv.fr
    """
    try:
        # Vérifier que l'utilisateur est un recruteur
        recruteur = supabase.table("recruteurs")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .single()\
            .execute()
        
        if not recruteur.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les recruteurs peuvent créer une entreprise"
            )
        
        # Créer l'entreprise
        result = supabase.table("entreprises")\
            .insert(entreprise_data.model_dump())\
            .execute()
        
        entreprise = result.data[0]
        
        # Lier l'entreprise au recruteur
        supabase.table("recruteurs")\
            .update({"entreprise_id": entreprise["id"]})\
            .eq("id", recruteur.data["id"])\
            .execute()
        
        logger.info(f"✅ Entreprise créée: {entreprise['nom']} par {current_user['email']}")
        
        return entreprise
        
    except Exception as e:
        logger.error(f"❌ Erreur création entreprise: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{entreprise_id}", response_model=EntrepriseResponse)
async def get_entreprise(entreprise_id: UUID):
    """
    📄 Récupérer les détails d'une entreprise
    
    Accessible à tous pour les entreprises vérifiées.
    """
    try:
        result = supabase.table("entreprises")\
            .select("*")\
            .eq("id", str(entreprise_id))\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entreprise non trouvée"
            )
        
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération entreprise: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=List[EntrepriseResponse])
async def list_entreprises(
    verified_only: bool = True,
    skip: int = 0,
    limit: int = 50
):
    """
    📋 Liste des entreprises
    
    Par défaut, n'affiche que les entreprises vérifiées.
    """
    try:
        query = supabase.table("entreprises").select("*")
        
        if verified_only:
            query = query.eq("verified", True)
        
        result = query.eq("actif", True)\
            .range(skip, skip + limit - 1)\
            .execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"❌ Erreur liste entreprises: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{entreprise_id}", response_model=EntrepriseResponse)
async def update_entreprise(
    entreprise_id: UUID,
    entreprise_data: EntrepriseUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    ✏️ Modifier une entreprise
    
    Seul le recruteur lié à l'entreprise peut la modifier.
    """
    try:
        # Vérifier que l'utilisateur est lié à cette entreprise
        recruteur = supabase.table("recruteurs")\
            .select("*")\
            .eq("user_id", current_user["id"])\
            .eq("entreprise_id", str(entreprise_id))\
            .single()\
            .execute()
        
        if not recruteur.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à modifier cette entreprise"
            )
        
        # Mettre à jour l'entreprise
        result = supabase.table("entreprises")\
            .update(entreprise_data.model_dump(exclude_unset=True))\
            .eq("id", str(entreprise_id))\
            .execute()
        
        logger.info(f"✅ Entreprise mise à jour: {entreprise_id}")
        
        return result.data[0]
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour entreprise: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/verify/siret/{siret}")
async def verify_siret(siret: str):
    """
    🔍 Vérifier un SIRET via l'API entreprise.data.gouv.fr
    
    Retourne les informations légales de l'entreprise.
    """
    try:
        import httpx
        
        # Nettoyer le SIRET (enlever espaces)
        siret = siret.replace(" ", "").replace("-", "")
        
        # Appel API entreprise.data.gouv.fr
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://entreprise.data.gouv.fr/api/sirene/v3/etablissements/{siret}",
                timeout=10.0
            )
            
            if response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="SIRET non trouvé"
                )
            
            response.raise_for_status()
            data = response.json()
            
            etablissement = data.get("etablissement", {})
            unite_legale = etablissement.get("unite_legale", {})
            
            return {
                "siret": etablissement.get("siret"),
                "siren": etablissement.get("siren"),
                "nom": unite_legale.get("denomination", ""),
                "forme_juridique": unite_legale.get("categorie_juridique"),
                "siege_social": etablissement.get("geo_adresse"),
                "ville": etablissement.get("libelle_commune"),
                "code_postal": etablissement.get("code_postal"),
                "actif": etablissement.get("etat_administratif") == "A"
            }
            
    except httpx.HTTPError as e:
        logger.error(f"❌ Erreur API SIRET: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service de vérification SIRET temporairement indisponible"
        )
    except Exception as e:
        logger.error(f"❌ Erreur vérification SIRET: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
