from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from app.engines.tige import tige
from app.engines.dtdfe import dtdfe
from app.engines.tek import tek
from app.database import db_store
from app.models.genome import TenantGenome

router = APIRouter(prefix="/tenants", tags=["Tenants & Genomes"])

class CreateTenantRequest(BaseModel):
    tenant_id: str
    gym_name: str
    tier: str = "Free"

@router.post("", response_model=TenantGenome)
def create_tenant(payload: CreateTenantRequest):
    if db_store.get_genome(payload.tenant_id):
        raise HTTPException(status_code=400, detail=f"Tenant {payload.tenant_id} already exists.")
    genome = tige.initialize_tenant_genome(payload.tenant_id, payload.gym_name, payload.tier)
    # Construct initial dependency fabric
    dtdfe.construct_fabric(genome)
    return genome

@router.get("", response_model=List[TenantGenome])
def list_tenants():
    return db_store.list_genomes()

@router.get("/{tenant_id}", response_model=TenantGenome)
def get_tenant_genome(tenant_id: str):
    genome = db_store.get_genome(tenant_id)
    if not genome:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found.")
    return genome

@router.get("/{tenant_id}/fabric")
def get_tenant_dependency_fabric(tenant_id: str):
    fabric = dtdfe.get_fabric(tenant_id)
    return {"tenant_id": tenant_id, "dependency_edges": [e.model_dump() for e in fabric]}

@router.post("/{tenant_id}/evolve")
def evolve_tenant(tenant_id: str):
    result = tek.run_evolution_cycle(tenant_id)
    return result
