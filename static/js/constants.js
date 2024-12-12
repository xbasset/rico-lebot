const UI_STATE = {
    IDLE: 'idle',
    CONNECTING: 'connecting',
    LISTENING: 'listening',
    SPEAKING: 'speaking',
};

const UI_STATE_CLASSES = {
    'idle': ['bg-gray-500', 'hover:bg-gray-400'],
    'connecting': ['bg-blue-800'],
    'speaking': ['bg-indigo-500', 'hover:bg-red-400'],
    'listening': ['bg-blue-500', 'hover:bg-red-400'],
};

const ICON_STATE_CLASSES = {
    'idle': ['bg-gray-400', 'group-hover:bg-gray-300'],
    'connecting': ['bg-blue-600'],
    'speaking': ['bg-indigo-600', 'group-hover:bg-red-500'],
    'listening': ['bg-blue-600', 'group-hover:bg-red-500'],
};


const BACKGROUND_TEXT_STATE_CLASSES = {
    'agent': {
        'idle': ['bg-gray-200'],
        'connecting': ['bg-gray-200'],
        'speaking': ['bg-gray-200'],
        'listening': ['bg-gray-200'],
    },
    'user': {
        'idle': ['bg-gray-200'],
        'connecting': ['bg-gray-200'],
        'speaking': ['bg-blue-300'],
        'listening': ['bg-blue-500'],
    },
}

const UI_STATE_MESSAGES = {
    'idle': 'Click to start',
    'connecting': 'Connecting...',
    'listening': 'Listening...',
    'speaking': 'Speaking...',
}
