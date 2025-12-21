"""
Service d'intégration avec les job boards externes (LinkedIn, Indeed, etc.)
"""
import os
import httpx
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from loguru import logger


class JobBoardIntegrationService:
    """Service pour intégrer les offres depuis les job boards externes"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Clés API depuis les variables d'environnement
        self.indeed_api_key = os.getenv("INDEED_API_KEY")
        self.linkedin_client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.linkedin_client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        self.linkedin_access_token = None
    
    async def close(self):
        """Fermer le client HTTP"""
        await self.http_client.aclose()
    
    # ================================================
    # INDEED INTEGRATION
    # ================================================
    
    async def fetch_indeed_jobs(
        self,
        query: str = "",
        location: str = "France",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Récupérer les offres depuis Indeed API
        
        API Docs: https://opensource.indeedeng.io/api-documentation/docs/job-search/
        """
        if not self.indeed_api_key:
            logger.warning("Indeed API key not configured")
            return []
        
        try:
            url = "https://api.indeed.com/ads/apisearch"
            params = {
                "publisher": self.indeed_api_key,
                "q": query,
                "l": location,
                "limit": limit,
                "format": "json",
                "v": "2",
                "co": "fr"  # Country: France
            }
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for result in data.get("results", []):
                job = {
                    "source": "indeed",
                    "external_id": result.get("jobkey"),
                    "titre": result.get("jobtitle"),
                    "entreprise_nom": result.get("company"),
                    "description": result.get("snippet"),
                    "localisation": result.get("formattedLocation"),
                    "type_contrat": self._parse_indeed_contract_type(result.get("formattedRelativeTime")),
                    "url_offre": result.get("url"),
                    "raw_data": result
                }
                jobs.append(job)
            
            logger.info(f"Fetched {len(jobs)} jobs from Indeed")
            return jobs
            
        except httpx.HTTPError as e:
            logger.error(f"Error fetching Indeed jobs: {e}")
            return []
    
    def _parse_indeed_contract_type(self, relative_time: str) -> str:
        """Parser le type de contrat depuis Indeed (approximatif)"""
        # Indeed ne fournit pas toujours le type de contrat
        # On peut essayer de le déduire du titre ou description
        return "CDI"  # Valeur par défaut
    
    # ================================================
    # LINKEDIN INTEGRATION
    # ================================================
    
    async def get_linkedin_access_token(self) -> Optional[str]:
        """
        Obtenir un access token LinkedIn via OAuth 2.0
        
        API Docs: https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication
        """
        if not self.linkedin_client_id or not self.linkedin_client_secret:
            logger.warning("LinkedIn credentials not configured")
            return None
        
        try:
            url = "https://www.linkedin.com/oauth/v2/accessToken"
            data = {
                "grant_type": "client_credentials",
                "client_id": self.linkedin_client_id,
                "client_secret": self.linkedin_client_secret
            }
            
            response = await self.http_client.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            self.linkedin_access_token = token_data.get("access_token")
            logger.info("LinkedIn access token obtained")
            return self.linkedin_access_token
            
        except httpx.HTTPError as e:
            logger.error(f"Error getting LinkedIn token: {e}")
            return None
    
    async def fetch_linkedin_jobs(
        self,
        keywords: str = "",
        location: str = "France",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Récupérer les offres depuis LinkedIn Jobs API
        
        API Docs: https://learn.microsoft.com/en-us/linkedin/talent/job-postings
        """
        if not self.linkedin_access_token:
            await self.get_linkedin_access_token()
        
        if not self.linkedin_access_token:
            logger.warning("Cannot fetch LinkedIn jobs without access token")
            return []
        
        try:
            url = "https://api.linkedin.com/v2/jobPostings"
            headers = {
                "Authorization": f"Bearer {self.linkedin_access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            params = {
                "q": "criteria",
                "keywords": keywords,
                "location": location,
                "count": limit
            }
            
            response = await self.http_client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for element in data.get("elements", []):
                # Parser les données LinkedIn
                job = {
                    "source": "linkedin",
                    "external_id": str(element.get("id")),
                    "titre": element.get("title"),
                    "entreprise_nom": element.get("companyName"),
                    "description": element.get("description", {}).get("text"),
                    "localisation": self._parse_linkedin_location(element.get("location")),
                    "type_contrat": self._parse_linkedin_contract_type(element.get("employmentType")),
                    "experience_requise": element.get("experienceLevel"),
                    "url_offre": element.get("applyUrl"),
                    "logo_url": element.get("companyLogo"),
                    "raw_data": element
                }
                
                # Parser les compétences si disponibles
                if "skills" in element:
                    job["competences_requises"] = [
                        skill.get("name") for skill in element.get("skills", [])
                    ]
                
                jobs.append(job)
            
            logger.info(f"Fetched {len(jobs)} jobs from LinkedIn")
            return jobs
            
        except httpx.HTTPError as e:
            logger.error(f"Error fetching LinkedIn jobs: {e}")
            return []
    
    def _parse_linkedin_location(self, location_data: Dict) -> str:
        """Parser la localisation LinkedIn"""
        if not location_data:
            return ""
        
        parts = []
        if "city" in location_data:
            parts.append(location_data["city"])
        if "country" in location_data:
            parts.append(location_data["country"])
        
        return ", ".join(parts)
    
    def _parse_linkedin_contract_type(self, employment_type: str) -> str:
        """
        Mapper les types d'emploi LinkedIn vers nos types
        
        LinkedIn types: FULL_TIME, PART_TIME, CONTRACT, TEMPORARY, INTERNSHIP, VOLUNTEER
        """
        mapping = {
            "FULL_TIME": "CDI",
            "PART_TIME": "Temps partiel",
            "CONTRACT": "CDD",
            "TEMPORARY": "Intérim",
            "INTERNSHIP": "Stage",
            "VOLUNTEER": "Bénévolat"
        }
        return mapping.get(employment_type, "CDI")
    
    # ================================================
    # IMPORT & SYNC
    # ================================================
    
    async def import_jobs_to_database(
        self,
        jobs: List[Dict[str, Any]],
        source: str
    ) -> Dict[str, int]:
        """
        Importer les offres dans la base de données
        
        Returns: {"imported": X, "updated": Y, "errors": Z}
        """
        stats = {"imported": 0, "updated": 0, "errors": 0}
        
        for job in jobs:
            try:
                # Vérifier si l'offre existe déjà
                existing = self.supabase.table("external_job_postings")\
                    .select("id")\
                    .eq("source", source)\
                    .eq("external_id", job["external_id"])\
                    .execute()
                
                if existing.data:
                    # Mise à jour
                    self.supabase.table("external_job_postings")\
                        .update({
                            **job,
                            "last_synced_at": datetime.utcnow().isoformat()
                        })\
                        .eq("id", existing.data[0]["id"])\
                        .execute()
                    stats["updated"] += 1
                else:
                    # Insertion
                    self.supabase.table("external_job_postings")\
                        .insert(job)\
                        .execute()
                    stats["imported"] += 1
                
            except Exception as e:
                logger.error(f"Error importing job {job.get('external_id')}: {e}")
                stats["errors"] += 1
        
        return stats
    
    async def sync_all_sources(
        self,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, int]]:
        """
        Synchroniser toutes les sources configurées
        
        Args:
            sources: Liste des sources à synchroniser (None = toutes)
        
        Returns: Dict avec stats par source
        """
        if sources is None:
            sources = ["indeed", "linkedin"]
        
        results = {}
        
        for source in sources:
            logger.info(f"Starting sync for {source}")
            
            # Créer un log de sync
            sync_log = self.supabase.table("job_board_sync_logs").insert({
                "source": source,
                "status": "running"
            }).execute()
            sync_log_id = sync_log.data[0]["id"]
            
            try:
                # Récupérer les offres selon la source
                if source == "indeed":
                    jobs = await self.fetch_indeed_jobs()
                elif source == "linkedin":
                    jobs = await self.fetch_linkedin_jobs()
                else:
                    logger.warning(f"Unknown source: {source}")
                    continue
                
                # Importer dans la BDD
                stats = await self.import_jobs_to_database(jobs, source)
                
                # Mettre à jour le log de sync
                self.supabase.table("job_board_sync_logs").update({
                    "status": "success",
                    "completed_at": datetime.utcnow().isoformat(),
                    "total_fetched": len(jobs),
                    "total_imported": stats["imported"],
                    "total_updated": stats["updated"],
                    "total_errors": stats["errors"]
                }).eq("id", sync_log_id).execute()
                
                results[source] = stats
                logger.info(f"Sync completed for {source}: {stats}")
                
            except Exception as e:
                logger.error(f"Sync failed for {source}: {e}")
                
                # Marquer le log comme failed
                self.supabase.table("job_board_sync_logs").update({
                    "status": "failed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "error_message": str(e)
                }).eq("id", sync_log_id).execute()
                
                results[source] = {"error": str(e)}
        
        return results
    
    # ================================================
    # CONVERSION VERS OFFRES LOCALES
    # ================================================
    
    async def convert_to_local_offer(
        self,
        external_job_id: str,
        recruteur_id: str,
        entreprise_id: str
    ) -> Optional[str]:
        """
        Convertir une offre externe en offre locale dans notre système
        
        Returns: ID de l'offre créée
        """
        try:
            # Récupérer l'offre externe
            external = self.supabase.table("external_job_postings")\
                .select("*")\
                .eq("id", external_job_id)\
                .single()\
                .execute()
            
            if not external.data:
                logger.error(f"External job {external_job_id} not found")
                return None
            
            ext_job = external.data
            
            # Créer l'offre locale
            local_offer = {
                "recruteur_id": recruteur_id,
                "entreprise_id": entreprise_id,
                "titre": ext_job["titre"],
                "description": ext_job["description"],
                "localisation": ext_job["localisation"],
                "type_contrat": ext_job.get("type_contrat", "CDI"),
                "salaire_min": ext_job.get("salaire_min"),
                "salaire_max": ext_job.get("salaire_max"),
                "competences_requises": ext_job.get("competences_requises", []),
                "experience_requise": ext_job.get("experience_requise"),
                "publiee": True
            }
            
            result = self.supabase.table("offres").insert(local_offer).execute()
            local_offer_id = result.data[0]["id"]
            
            # Lier l'offre externe à l'offre locale
            self.supabase.table("external_job_postings")\
                .update({"offre_id": local_offer_id})\
                .eq("id", external_job_id)\
                .execute()
            
            logger.info(f"Converted external job {external_job_id} to local offer {local_offer_id}")
            return local_offer_id
            
        except Exception as e:
            logger.error(f"Error converting external job: {e}")
            return None
