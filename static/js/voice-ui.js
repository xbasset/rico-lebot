function handleTrackSubscribed(
    track, // : LivekitClient.RemoteTrack,
    publication, //: LivekitClient.RemoteTrackPublication,
    participant, //: LivekitClient.RemoteParticipant,
) {
    if (track.kind === LivekitClient.Track.Kind.Video || track.kind === LivekitClient.Track.Kind.Audio) {
        // attach it to a new HTMLVideoElement or HTMLAudioElement
        const element = track.attach();
        agentAudio = document.getElementById('agent-audio');
        agentAudio.appendChild(element);
    }
}

function handleTrackUnsubscribed(
    track, //: LivekitClient.RemoteTrack,
    publication, //: LivekitClient.RemoteTrackPublication,
    participant, //: LivekitClient.RemoteParticipant,
) {
    // remove tracks from all attached elements
    track.detach();
}

function handleLocalTrackUnpublished(
    publication, //: LivekitClient.LocalTrackPublication,
    participant, //: LivekitClient.ocalParticipant,
) {
    // when local tracks are ended, update UI to remove them from rendering
    publication.track.detach();
}

function setTranscriptions(updateFn) {
    transcriptions = updateFn(transcriptions);
}

function handleDisconnect() {
    console.log('disconnected from room');
}



function voiceUIComponent() {
    return {
        state: UI_STATE.IDLE,
        transcript: '',
        userInput: '',
        testing: false,
        transcriptions: {},
        stateMessage: UI_STATE_MESSAGES[UI_STATE.IDLE],
        summary: null,
        isSummaryLoading: false,
        live_info: null,
        live_info_history: [],

        init() {
            // Initialization code
            this.updateDisplay();

            // debug mode
            this.testing = true;

        },
        setState(newState) {
            this.state = newState;
            this.updateDisplay();
        },
        setTranscript(newTranscript) {
            this.transcript = newTranscript;
        },

        setUserInput(newUserInput) {
            this.userInput = newUserInput;
        },


        setAgentTranscript(newTranscript) {
            this.transcript = newTranscript;
            this.setState(UI_STATE.SPEAKING);
        },

        leaveRoom() {
            if (this.currentRoom) {
                this.currentRoom.disconnect();
                this.setState(UI_STATE.IDLE);
            } else {
                console.log('No room to disconnect from');
            }
        },

        handleClick() {
            this.setState(this.state === UI_STATE.IDLE ? UI_STATE.CONNECTING : UI_STATE.IDLE);
            if (this.state === UI_STATE.CONNECTING) {
                this.connectToRoom().then(room => {
                    console.log('Room connected: ', room.name);
                    this.currentRoom = room;
                    this.setState(UI_STATE.LISTENING);
                }).catch(error => {
                    console.error('Error connecting to room:', error);
                });
            } else {
                this.setUserInput('');
                this.setAgentTranscript('');
                this.leaveRoom();

                // Fetch the /api/match_tags POST route to retrieve the matched tags
                const transcriptionsText = Object.values(this.transcriptions)
                    .sort((a, b) => a.firstReceivedTime - b.firstReceivedTime)
                    .map(segment => `${segment.participant.identity.startsWith('agent') ? '🤖' : '😁'} ${segment.text}`)
                    .join('\n');
                this.isSummaryLoading = true;


                fetch('/api/recap', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        transcription: transcriptionsText
                    })
                }).then(response => response.json()).then(data => {
                    if (data.error) {
                        console.error('Error:', data.error);
                        return;
                    }
                    this.summary = marked.parse(data.summary);
                    this.isSummaryLoading = false;
                    
                });
            }
        },


        updateDisplay() {
            // Update element classes based on state
            const element = this.$refs.voiceUIElement;
            const icon = this.$refs.voiceUIIcon;

            // Define the dynamic classes for the current state
            const elementDynamicClasses = UI_STATE_CLASSES[this.state];
            const iconDynamicClasses = ICON_STATE_CLASSES[this.state];

            // Remove previous dynamic classes from element and icon
            Object.values(UI_STATE_CLASSES).forEach(classes => {
                element.classList.remove(...classes);
            });
            Object.values(ICON_STATE_CLASSES).forEach(classes => {
                icon.classList.remove(...classes);
            });

            // Add new dynamic classes
            element.classList.add(...elementDynamicClasses);
            icon.classList.add(...iconDynamicClasses);

            // state message
            this.stateMessage = UI_STATE_MESSAGES[this.state];
        },

        handleTranscriptionReceived(segments, participant, publication) {
            // Update transcriptions
            segments.forEach((segment) => {
                this.transcriptions[segment.id] = {
                    ...segment,
                    participant,
                    publication,
                };
            });


            // Process transcriptions to update userInput and transcript
            const transcriptionsArray = Object.values(this.transcriptions);

            const agentSegments = [];
            const userSegments = [];
            let currentAgentGroup = [];
            let currentUserGroup = [];

            transcriptionsArray.forEach((segment) => {
                if (segment.participant.identity.startsWith('agent')) {
                    if (currentUserGroup.length > 0) {
                        userSegments.push(currentUserGroup);
                        currentUserGroup = [];
                    }
                    currentAgentGroup.push(segment.text);
                } else {
                    if (currentAgentGroup.length > 0) {
                        agentSegments.push(currentAgentGroup);
                        currentAgentGroup = [];
                    }
                    currentUserGroup.push(segment.text);
                }
            });

            if (currentAgentGroup.length > 0) agentSegments.push(currentAgentGroup);
            if (currentUserGroup.length > 0) userSegments.push(currentUserGroup);

            if (agentSegments.length > 0) {
                const lastAgentGroup = agentSegments[agentSegments.length - 1];
                this.setAgentTranscript(lastAgentGroup.join(' '));
            }

            if (userSegments.length > 0) {
                const lastUserGroup = userSegments[userSegments.length - 1];
                this.setUserInput(lastUserGroup.join(' '));
            }
        },

        handleActiveSpeakerChange(
            speakers, //: LivekitClient.Participant[]
        ) {

            // show UI indicators when participant or agent is speaking
            // if speakers.length > 0, if the first speaker.identity starts with 'agent', set state to SPEAKING else set state to LISTENING
            if (speakers.length > 0) {
                if (speakers[0].identity.startsWith('agent')) {
                    this.setState(UI_STATE.SPEAKING);
                } else {
                    this.setState(UI_STATE.LISTENING);
                }
            }

        },

        async connectToRoom() {
            try {

                // fetch auth data from server                
                const authData = await fetch('/api/agent/auth').then(response => response.json());
                // console.log('auth data', authData);

                const room = new LivekitClient.Room();
                await room.connect(authData.url, authData.token);
                // console.log('connected to room', room.name);
                const p = room.localParticipant;
                // turn on the local user's camera and mic, this may trigger a browser prompt
                // to ensure permissions are granted
                await p.setMicrophoneEnabled(true);

                // load the role from the run.html hidden field with id 'role'
                const role = document.getElementById('role').value;
                // console.log('role:', role);
                p.setAttributes({
                    role: role,
                })

                // set up event listeners
                room
                    .on(LivekitClient.RoomEvent.TrackSubscribed, handleTrackSubscribed)
                    .on(LivekitClient.RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed)
                    .on(LivekitClient.RoomEvent.ActiveSpeakersChanged, this.handleActiveSpeakerChange.bind(this))
                    .on(LivekitClient.RoomEvent.Disconnected, handleDisconnect)
                    .on(LivekitClient.RoomEvent.LocalTrackUnpublished, handleLocalTrackUnpublished)
                    .on(LivekitClient.RoomEvent.TranscriptionReceived, this.handleTranscriptionReceived.bind(this));

                p.registerRpcMethod(
                    'greet',
                    async (data) => {
                        // console.log(`Received greeting from ${data.callerIdentity}: ${data.payload}`);
                        return `Hello, ${data.callerIdentity}!`;
                    }
                );

                p.registerRpcMethod(
                    'terminate',
                    async (data) => {
                        console.log(`Received greeting from ${data.callerIdentity}: ${data.payload}`);
                        this.handleClick(); // disconnect from room
                        return `Client session terminated!`;
                    }
                );

                p.registerRpcMethod(
                    'save',
                    async (data) => {
                        console.log('saving data:', data);
                        fetch('/api/save', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                information_to_save: data.payload,
                                agent_id: data.callerIdentity,
                            })
                        }).then(response => response.json()).then(data => {
                            if (data.error) {
                                console.error('Error:', data.error);
                                return `🔴 error see console.log`;
                            }
                            this.summary = marked.parse(data.summary);
                            this.isSummaryLoading = false;
                            return `✅ saving success`;
                            
                        });

                    }
                );

                p.registerRpcMethod(
                    'show',
                    async (data) => {
                        console.log('showing data:', data.payload);
                        this.live_info_history.push(data.payload);
                        // show the last live info
                        this.live_info = marked.parse(this.live_info_history[this.live_info_history.length - 1]) + '<br/>';
                    }
                )

                return room;
            } catch (err) {
                console.error('error connecting to room', err);
                throw err;
            }
        },

        copyTranscriptionsToClipboard() {
            const transcriptionsText = Object.values(this.transcriptions)
                .sort((a, b) => a.firstReceivedTime - b.firstReceivedTime)
                .map(segment => `${segment.participant.identity.startsWith('agent') ? '🤖' : '😁'} ${segment.text}`)
                .join('\n');
            navigator.clipboard.writeText(transcriptionsText).then(() => {
                const modal = document.getElementById('copied-to-clipboard');
                const copyButton = document.getElementById('copy-to-clipboard');
                copyButton.classList.add('hidden');
                modal.classList.remove('hidden');
                setTimeout(() => {
                    modal.classList.add('hidden');
                    copyButton.classList.remove('hidden');
                }, 1500);
            }).catch(err => {
                console.error('Failed to copy transcriptions: ', err);
            });
        },

    }
}