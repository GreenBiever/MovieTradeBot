from services.project_var import ProjectVarService
from app_dependency import get_bot
import config


def get_project_var_service() -> ProjectVarService:
    from databases.models import ProjectVar
    return ProjectVarService(ProjectVar)
