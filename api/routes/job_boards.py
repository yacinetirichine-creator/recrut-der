"""
Routes API pour l'intégration des job boards externes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from api.database.supabase_client import supabase
from api.services.job_board_service import JobBoardIntegrationService
from api.routes.auth import get_current_user


router = APIRouter(prefix="/job-boards", tags=["job-boards"])


# ================================================
# MODELS
# ================================================

class SyncRequest(BaseModel):
    sources: Optional[List[str]] = None  # None = toutes les sources
    keywords: Optional[str] = ""
    location: Optional[str] = "France"
    limit: Optional[int] = 100


class ConvertToLocalRequest(BaseModel):
    external_job_id: str
    entreprise_id: str


class ExternalJobResponse(BaseModel):
    id: str
    source: str
    external_id: str
    titre: str
    entreprise_nom: str
    description: Optional[str]
    localisation: Optional[str]
    type_contrat: Optional[str]
    url_offre: Optional[str]
    imported_at: datetime
    is_active: bool
    offre_id: Optional[str]


class SyncStatsResponse(BaseModel):
    source: str
    total_fetched: int
    total_imported: int
    total_updated: int
    total_errors: int


# ================================================
# ENDPOINTS - SYNCHRONISATION
# ================================================

@router.post("/sync", response_model=Dict[str, Any])
async def sync_job_boards(
    sync_request: SyncRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    🔄 Synchroniser les offres depuis les job boards externes (Indeed, LinkedIn)
    
    **Admin uniquement**
    
    - Lance la synchronisation en arrière-plan
    - Retourne immédiatement avec un statut
    - Les offres seront disponibles dans `/job-boards/external` après sync
    
    **Sources disponibles:**
    - `indeed`: Indeed.com
    - `linkedin`: LinkedIn Jobs
    
    **Exemple:**
    ```json
    {
        "sources": ["indeed", "linkedin"],
        "keywords": "développeur python",
        "location": "Paris",
        "limit": 100
    }
    ```
    """
    # Vérifier que l'utilisateur est admin
    user_data = supabase.table("utilisateurs")\
        .select("role")\
        .eq("id", current_user["id"])\
        .single()\
        .execute()
    
    if not user_data.data or user_data.data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Créer le service
    job_board_service = JobBoardIntegrationService(supabase)
    
    # Lancer la sync en arrière-plan
    async def run_sync():
        try:
            results = await job_board_service.sync_all_sources(
                sources=sync_request.sources
            )
            await job_board_service.close()
            return results
        except Exception as e:
            await job_board_service.close()
            raise e
    
    background_tasks.add_task(run_sync)
    
    return {
        "status": "sync_started",
        "message": "Job board synchronization started in background",
        "sources": sync_request.sources or ["indeed", "linkedin"],
        "check_status_at": "/job-boards/sync-logs"
    }


@router.get("/sync-logs", response_model=List[Dict[str, Any]])
async def get_sync_logs(
    source: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """
    📊 Récupérer l'historique des synchronisations
    
    **Admin uniquement**
    
    - Affiche les logs de sync avec statistiques
    - Permet de vérifier le statut des imports
    """
    # Vérifier admin
    user_data = supabase.table("utilisateurs")\
        .select("role")\
        .eq("id", current_user["id"])\
        .single()\
        .execute()
    
    if not user_data.data or user_data.data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Récupérer les logs
    query = supabase.table("job_board_sync_logs")\
        .select("*")\
        .order("started_at", desc=True)\
        .limit(limit)
    
    if source:
        query = query.eq("source", source)
    
    result = query.execute()
    return result.data


# ================================================
# ENDPOINTS - OFFRES EXTERNES
# ================================================

@router.get("/external", response_model=List[ExternalJobResponse])
async def list_external_jobs(
    source: Optional[str] = None,
    is_active: bool = True,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    """
    📋 Lister les offres importées depuis les job boards externes
    
    - Filtrer par source (indeed, linkedin)
    - Voir les offres actives ou toutes
    - Pagination disponible
    """
    query = supabase.table("external_job_postings")\
        .select("*")\
        .order("imported_at", desc=True)\
        .range(offset, offset + limit - 1)
    
    if source:
        query = query.eq("source", source)
    
    if is_active:
        query = query.eq("is_active", True)
    
    result = query.execute()
    return result.data


@router.get("/external/{job_id}", response_model=ExternalJobResponse)
async def get_external_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    🔍 Détails d'une offre externe
    
    - Affiche toutes les informations de l'offre importée
    - Inclut les données brutes (raw_data) si besoin
    """
    result = supabase.table("external_job_postings")\
        .select("*")\
        .eq("id", job_id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="External job not found")
    
    return result.data


# ================================================
# ENDPOINTS - CONVERSION
# ================================================

@router.post("/external/{job_id}/convert")
async def convert_external_to_local(
    job_id: str,
    convert_request: ConvertToLocalRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    🔄 Convertir une offre externe en offre locale
    
    **Recruteurs uniquement**
    
    - Importe l'offre externe dans vos offres
    - Permet de la modifier et gérer comme une offre normale
    - Lie l'offre à votre entreprise
    
    **Exemple:**
    ```json
    {
        "entreprise_id": "uuid-de-votre-entreprise"
    }
    ```
    """
    # Vérifier que l'utilisateur est recruteur
    user_data = supabase.table("utilisateurs")\
        .select("id")\
        .eq("id", current_user["id"])\
        .single()\
        .execute()
    
    recruteur = supabase.table("recruteurs")\
        .select("id")\
        .eq("utilisateur_id", current_user["id"])\
        .single()\
        .execute()
    
    if not recruteur.data:
        raise HTTPException(status_code=403, detail="Recruteur access required")
    
    # Vérifier que l'entreprise appartient au recruteur
    entreprise = supabase.table("entreprises")\
        .select("id")\
        .eq("id", convert_request.entreprise_id)\
        .eq("recruteur_id", recruteur.data["id"])\
        .single()\
        .execute()
    
    if not entreprise.data:
        raise HTTPException(
            status_code=403,
            detail="Entreprise not found or doesn't belong to you"
        )
    
    # Convertir l'offre
    job_board_service = JobBoardIntegrationService(supabase)
    
    try:
        local_offer_id = await job_board_service.convert_to_local_offer(
            external_job_id=job_id,
            recruteur_id=recruteur.data["id"],
            entreprise_id=convert_request.entreprise_id
        )
        
        await job_board_service.close()
        
        if not local_offer_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to convert external job"
            )
        
        return {
            "status": "converted",
            "external_job_id": job_id,
            "local_offer_id": local_offer_id,
            "message": "External job successfully converted to local offer"
        }
        
    except Exception as e:
        await job_board_service.close()
        raise HTTPException(status_code=500, detail=str(e))


# ================================================
# ENDPOINTS - CONFIGURATION
# ================================================

@router.get("/configs", response_model=List[Dict[str, Any]])
async def get_job_board_configs(
    current_user: dict = Depends(get_current_user),
):
    """
    ⚙️ Récupérer la configuration des job boards
    
    **Admin uniquement**
    
    - Voir les sources activées
    - Fréquence de synchronisation
    - Dernière sync
    """
    # Vérifier admin
    user_data = supabase.table("utilisateurs")\
        .select("role")\
        .eq("id", current_user["id"])\
        .single()\
        .execute()
    
    if not user_data.data or user_data.data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = supabase.table("job_board_configs")\
        .select("*")\
        .execute()
    
    return result.data


@router.patch("/configs/{source}")
async def update_job_board_config(
    source: str,
    enabled: Optional[bool] = None,
    sync_frequency_hours: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    ⚙️ Mettre à jour la configuration d'une source
    
    **Admin uniquement**
    
    - Activer/désactiver une source
    - Modifier la fréquence de sync
    """
    # Vérifier admin
    user_data = supabase.table("utilisateurs")\
        .select("role")\
        .eq("id", current_user["id"])\
        .single()\
        .execute()
    
    if not user_data.data or user_data.data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Préparer les updates
    updates = {}
    if enabled is not None:
        updates["enabled"] = enabled
    if sync_frequency_hours is not None:
        updates["sync_frequency_hours"] = sync_frequency_hours
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    updates["updated_at"] = datetime.utcnow().isoformat()
    
    # Mettre à jour
    result = supabase.table("job_board_configs")\
        .update(updates)\
        .eq("source", source)\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Source not found")
    
    return {
        "status": "updated",
        "source": source,
        "updates": updates
    }


# ================================================
# ENDPOINTS - STATS
# ================================================

@router.get("/stats", response_model=Dict[str, Any])
async def get_job_board_stats(
    current_user: dict = Depends(get_current_user),
):
    """
    📊 Statistiques des imports job boards
    
    **Admin uniquement**
    
    - Total d'offres par source
    - Offres actives vs converties
    - Derniers imports
    """
    # Vérifier admin
    user_data = supabase.table("utilisateurs")\
        .select("role")\
        .eq("id", current_user["id"])\
        .single()\
        .execute()
    
    if not user_data.data or user_data.data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Récupérer les stats depuis la vue
    stats = supabase.table("job_board_import_stats")\
        .select("*")\
        .execute()
    
    return {
        "sources": stats.data,
        "total_external_jobs": sum(s.get("total_jobs", 0) for s in stats.data),
        "total_active": sum(s.get("active_jobs", 0) for s in stats.data),
        "total_converted": sum(s.get("converted_to_local", 0) for s in stats.data)
    }
