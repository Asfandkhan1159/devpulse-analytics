from pydantic import BaseModel
from datetime import datetime

class MetricsBase(BaseModel):
    project_id: int
    start_date: datetime
    end_date:datetime
    calculated_at: datetime

class DeploymentFrequencyResponse(MetricsBase):
    total_deployments: int
    
    daily_average: float
    frequency_label: str


class LeadTimeResponse(MetricsBase):
   
    average_lead_time_hours: float
 

class ChangeFailureRateResponse(MetricsBase):

    failure_rate_percentage: float
    

class MeanTimeToRecoveryResponse(MetricsBase):
   avg_mttr: float
   