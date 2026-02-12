from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict


class Event(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    class MessageContent(BaseModel):
        color: Optional[str] = None
        fields: Optional[List[Dict[str, Any]]] = None
        text: Optional[str] = None

    channels: Optional[Union[List[str], str]] = None  # The Slack notifications Lambda converts this to a list
    component: str 
    counter: Optional[int] = None
    emoji: Optional[str] = None
    exception: Optional[str] = None
    message_content: Optional[MessageContent] = None
    monitoring_slack_channel: str = "team-infra-alerts"
    pager_duty_description: Optional[str] = None
    pager_duty_event_type: Optional[str] = None
    notify_pager_duty: Optional[bool] = None
    recycle_success: Optional[bool] = None
    status: Optional[Union[bool, str]] = None 
    success_channel: str
    team: Optional[str] = None
    text: Optional[str] = None
    username: Optional[str] = None
