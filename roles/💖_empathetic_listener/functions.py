from __future__ import annotations
from dotenv import load_dotenv
load_dotenv(override=True)

import logging
from typing import Annotated

from livekit.agents import (
    JobContext,
    llm,
)
from livekit.api import LiveKitAPI, DeleteRoomRequest


logger = logging.getLogger("")
logger.setLevel(logging.INFO)




class ActorAgentFunctions(llm.FunctionContext):
    def __init__(self, ctx: JobContext):
        self.ctx = ctx
        self.remote_identity = next(iter(ctx.room.remote_participants.values()), None).identity
        super().__init__() 

    def _call_remote(self, method: str, payload: dict):
        try:
            return self.ctx.room.local_participant.perform_rpc(
                destination_identity=self.remote_identity,
                method=method,
                payload=payload
            )
        except Exception as e:
            logger.error(f"Error calling remote method {method}: {e}")
            return None


    @llm.ai_callable()
    async def greet(self):
        """Called as soon as entering in a conversation. This function starts the conversation."""
        try:
            logger.info(f"👋 Greeting user")
            return "Hello! How can I help you today?"
        except Exception as e:
            logger.error(f"Error: {e}")

    @llm.ai_callable()
    async def save_idea(
        self,
        idea: Annotated[str, llm.TypeInfo(description="The idea formulated by the user or slightly enhanced for clarity.")],
    ):
        """Called when there is an information that is relevant enough to be saved."""
        logger.info(f"🛠️ Saving idea: {idea}")
        return await self._call_remote('save', idea)
    
    @llm.ai_callable()
    async def show(
        self,
        information: Annotated[str, llm.TypeInfo(description="The information to display or show written in Markdown format.")],
    ):
        """Display information to the user."""
        # return f"Section '{section_title}' outlined with key points: {key_points}"
        logger.info(f"🛠️ Displaying information {information}")
        return await self._call_remote('show', information)

    ## Functions that matches the agent.instruct:
    ## 
    # function:
    # """
    # {
    #   "name": "stay_silent",
    #   "description": "Use this function to give the user an opportunity to finish their thought.",
    #   "parameters": {
    #     "type": "object",
    #     "properties": {},
    #     "required": []
    #   }
    # }
    # """
    @llm.ai_callable()
    async def stay_silent(self):
        """Use this function to give the user an opportunity to finish their thought."""
        try:
            message = "🤫 Staying silent..."
            logger.info(message)
            return message
        except Exception as e:
            logger.error(f"Error: {e}")