from pydantic import BaseModel, ConfigDict


class HealthCheckResponse(BaseModel):
    status: str

    model_config = ConfigDict(from_attributes=True)
