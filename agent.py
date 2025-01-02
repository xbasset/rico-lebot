from __future__ import annotations
from dotenv import load_dotenv
load_dotenv(override=True)

import os
import asyncio
import logging
import uuid
from dataclasses import asdict, dataclass
from typing import Annotated, Literal

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    WorkerPermissions,
    WorkerType,
    cli,
    llm,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai
from livekit.api import LiveKitAPI, DeleteRoomRequest

from jinja2 import Template

from core.config import OPENAI_API_KEY

from rich import print



logger = logging.getLogger("")
logger.setLevel(logging.INFO)



@dataclass
class SessionConfig:
    openai_api_key: str
    instructions: str
    voice: openai.realtime.api_proto.Voice
    temperature: float
    max_response_output_tokens: str | int
    modalities: list[openai.realtime.api_proto.Modality]
    turn_detection: openai.realtime.ServerVadOptions

    def __post_init__(self):
        if self.modalities is None:
            self.modalities = self._modalities_from_string("text_and_audio")

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if k != "openai_api_key"}

    @staticmethod
    def _modalities_from_string(modalities: str) -> list[str]:
        modalities_map = {
            "text_and_audio": ["text", "audio"],
            "text_only": ["text"],
        }
        return modalities_map.get(modalities, ["text", "audio"])

    def __eq__(self, other: SessionConfig) -> bool:
        return self.to_dict() == other.to_dict()


class AgentFunctions(llm.FunctionContext):
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
    async def terminate_session(self):
        """Called when the user ask to terminate the conversation. This function will end the conversation."""
        try:
            logger.info("🛑 Terminating session...")
            await self._call_remote("terminate", "end_session")
            lkapi = LiveKitAPI()
            await lkapi.room.delete_room(DeleteRoomRequest(
                room=self.ctx.room.name,
                ))
        except Exception as e:
            logger.error(f"Error: {e}")

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

class Agent:
    def __init__(self):
        self.role = ''
        self.ctx = None
        super().__init__()

    def load_agent_instructions(self) -> str:
        # check if there is a `data.py` file in the role folder. If so, load the variables to pass them to the template
        if os.path.exists(f"roles/{self.role}/data.py"):
            # import the variables from the data.py file
            module = __import__(f"roles.{self.role}.data", fromlist=["*"])
            data = {key: value for key, value in module.__dict__.items() if not key.startswith("__")}
        else:
            data = {}

        print(f"data: {data}")

        with open(f"roles/{self.role}/agent.instruct") as f:
            instructions = Template(f.read()).render(data=data)

        return instructions

    def get_session_config(self) -> SessionConfig:

        # default voice to coral
        voice = "coral"
        # check if there is a config.py in the role folder. If so, load the config from there
        if os.path.exists(f"roles/{self.role}/config.py"):
            # import the variables from the config.py file
            module = __import__(f"roles.{self.role}.config", fromlist=["*"])
            voice = module.voice if hasattr(module, "voice") else "coral"

        config = SessionConfig(
            openai_api_key=OPENAI_API_KEY,
            instructions=self.load_agent_instructions(),
            voice=voice,
            temperature=0.8,
            max_response_output_tokens= 2048,
            modalities=["text", "audio"],
            turn_detection=openai.realtime.DEFAULT_SERVER_VAD_OPTIONS,
        )
        return config

    async def call_rpc(self, participant: rtc.LocalParticipant, remote_identity: str):
        try:
            logger.info(f"👋 calling RPC greet to {remote_identity}")
            response = await participant.perform_rpc(
                destination_identity=remote_identity,
                method='greet',
                payload='Hello from RPC!'
            )
            print(f"RPC response: {response}")
        except Exception as e:
            print(f"RPC call failed: {e}")

    async def entrypoint(self, ctx: JobContext):
        logger.info(f"connecting to room {ctx.room.name}")
        self.ctx = ctx

        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        participant = await ctx.wait_for_participant()

        logger.info(f"<<<--•••-->>> participant attributes: {participant.attributes}")

        self.role = participant.attributes.get("role", None)

        remote_identity = participant.identity

        await self.call_rpc(ctx.room.local_participant, remote_identity)

        self.run_multimodal_agent(ctx, participant)

        logger.info("agent started")


    def run_multimodal_agent(self, ctx: JobContext, participant: rtc.Participant):

        logger.info(f"participant {participant.identity} joined the room")

        config = self.get_session_config()
        logger.info(f"starting omni assistant with config: {config.to_dict()}")

        model = openai.realtime.RealtimeModel(
            api_key=config.openai_api_key,
            instructions=config.instructions,
            voice=config.voice,
            temperature=config.temperature,
            max_response_output_tokens=config.max_response_output_tokens,
            modalities=config.modalities,
            turn_detection=config.turn_detection,
        )

        functions : llm.FunctionContext = AgentFunctions(ctx)

        # if there is a functions.py in the role folder, override the functions
        if self.role:
            if os.path.exists(f"roles/{self.role}/functions.py"):
                logger.info(f"🧙👋 Loading custom functions from {self.role}/functions.py")
                # first check if there is only one class in the file
                with open(f"roles/{self.role}/functions.py") as f:
                    lines = f.readlines()
                    class_lines = [line for line in lines if "class" in line]
                    if len(class_lines) != 1:
                        raise Exception("There should be only one class in the functions.py file")
                    class_name = class_lines[0].split("(")[0].split(" ")[-1]

                # import the class
                module = __import__(f"roles.{self.role}.functions", fromlist=[class_name])
                functions = getattr(module, class_name)(ctx)
                logger.info(f"🧙✅ Custom functions loaded from {self.role}/functions.py")


        assistant = MultimodalAgent(
            model=model,
            fnc_ctx=functions,
            )
        assistant.start(ctx.room)
        session = model.sessions[0]



        if config.modalities == ["text", "audio"]:
            session.conversation.item.create(
                llm.ChatMessage(
                    role="user",
                    content="Please begin the interaction with the user in a manner consistent with your instructions.",
                )
            )
            session.response.create()

        @session.on("response_done")
        def on_response_done(response: openai.realtime.RealtimeResponse):
            variant: Literal["warning", "destructive"]
            description: str | None = None
            title: str
            if response.status == "incomplete":
                if response.status_details and response.status_details["reason"]:
                    reason = response.status_details["reason"]
                    if reason == "max_output_tokens":
                        variant = "warning"
                        title = "Max output tokens reached"
                        description = "Response may be incomplete"
                    elif reason == "content_filter":
                        variant = "warning"
                        title = "Content filter applied"
                        description = "Response may be incomplete"
                    else:
                        variant = "warning"
                        title = "Response incomplete"
                else:
                    variant = "warning"
                    title = "Response incomplete"
            elif response.status == "failed":
                if response.status_details and response.status_details["error"]:
                    error_code = response.status_details["error"]["code"]
                    if error_code == "server_error":
                        variant = "destructive"
                        title = "Server error"
                    elif error_code == "rate_limit_exceeded":
                        variant = "destructive"
                        title = "Rate limit exceeded"
                    else:
                        variant = "destructive"
                        title = "Response failed"
                else:
                    variant = "destructive"
                    title = "Response failed"
            else:
                return

            logger.warning(f"response failed: {title} > {description}")

        async def send_transcription(
            ctx: JobContext,
            participant: rtc.Participant,
            track_sid: str,
            segment_id: str,
            text: str,
            is_final: bool = True,
        ):
            transcription = rtc.Transcription(
                participant_identity=participant.identity,
                track_sid=track_sid,
                segments=[
                    rtc.TranscriptionSegment(
                        id=segment_id,
                        text=text,
                        start_time=0,
                        end_time=0,
                        language="en",
                        final=is_final,
                    )
                ],
            )
            await ctx.room.local_participant.publish_transcription(transcription)

        last_transcript_id = None

        # send three dots when the user starts talking. will be cleared later when a real transcription is sent.
        @session.on("input_speech_started")
        def on_input_speech_started():
            nonlocal last_transcript_id
            remote_participant = next(iter(ctx.room.remote_participants.values()), None)
            if not remote_participant:
                return

            track_sid = next(
                (
                    track.sid
                    for track in remote_participant.track_publications.values()
                    if track.source == rtc.TrackSource.SOURCE_MICROPHONE
                ),
                None,
            )
            if last_transcript_id:
                asyncio.create_task(
                    send_transcription(
                        ctx, remote_participant, track_sid, last_transcript_id, ""
                    )
                )

            new_id = str(uuid.uuid4())
            last_transcript_id = new_id
            asyncio.create_task(
                send_transcription(
                    ctx, remote_participant, track_sid, new_id, "…", is_final=False
                )
            )

        @session.on("input_speech_transcription_completed")
        def on_input_speech_transcription_completed(
            event: openai.realtime.InputTranscriptionCompleted,
        ):
            nonlocal last_transcript_id
            if last_transcript_id:
                remote_participant = next(iter(ctx.room.remote_participants.values()), None)
                if not remote_participant:
                    return

                track_sid = next(
                    (
                        track.sid
                        for track in remote_participant.track_publications.values()
                        if track.source == rtc.TrackSource.SOURCE_MICROPHONE
                    ),
                    None,
                )
                asyncio.create_task(
                    send_transcription(
                        ctx, remote_participant, track_sid, last_transcript_id, ""
                    )
                )
                last_transcript_id = None

        @session.on("input_speech_transcription_failed")
        def on_input_speech_transcription_failed(
            event: openai.realtime.InputTranscriptionFailed,
        ):
            nonlocal last_transcript_id
            if last_transcript_id:
                remote_participant = next(iter(ctx.room.remote_participants.values()), None)
                if not remote_participant:
                    return

                track_sid = next(
                    (
                        track.sid
                        for track in remote_participant.track_publications.values()
                        if track.source == rtc.TrackSource.SOURCE_MICROPHONE
                    ),
                    None,
                )

                error_message = "⚠️ Transcription failed"
                asyncio.create_task(
                    send_transcription(
                        ctx,
                        remote_participant,
                        track_sid,
                        last_transcript_id,
                        error_message,
                    )
                )
                last_transcript_id = None

    def run_agent(self):
        try:
            print("[bold green]✨🧙 Starting agent...[/bold green]")
            cli.run_app(
                WorkerOptions(
                    entrypoint_fnc=self.entrypoint, 
                    worker_type=WorkerType.ROOM,
                    permissions=WorkerPermissions(
                        can_update_metadata=True,
                    )
                    )
                )
        finally:
            print("[bold red]✨🧙 Agent stopped...[/bold red]")



if __name__ == "__main__":
    agent = Agent()
    agent.run_agent()

