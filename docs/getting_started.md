# Getting started

The fastest way to start and try Rico Lebot is using Docker

## 🛠️ Configuration

### Pre-requisites:
- **LiveKit Account**: Sign up for LiveKit to obtain API credentials. [LiveKit Realtime API Quickstart](https://docs.livekit.io/agents/quickstarts/s2s/)
- **OpenAI API Key**: Obtain your API key from [OpenAI](https://platform.openai.com/account/api-keys).

### Clone the Repository

```bash
git clone https://github.com/xbasset/rico-lebot.git
cd rico-lebot
```


### Configure Environment Variables

Create a `.env` file in the root directory based on the provided `.env.example`:

```bash
cp .env.example .env
```

Open the `.env` file and populate it with your credentials:

```env
# .env

# OpenAI Credentials
OPENAI_API_KEY=your_openai_api_key

# LiveKit Credentials
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=your_livekit_server_url
```

## 🚀 Run with Docker

You can build the Docker image named `rico` and run it using the following commands.

### Build the Docker Image

```bash
docker build -t rico .
```

### Run the Docker Container

```bash
docker run -p 5001:5001 --name rico rico
```
> **Congratz**.
> 🎉 You're all set!
> Start using Rico Lebot: 👉 http://localhost:5001



## 🧑‍💻 As a developer

If you want to start each component and dive deeper, use the following.



### Setup Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
```

#### Python Dependencies

```bash
pip install -r requirements.txt
```
### Run each component

#### Running the Application

Start the Flask application with SocketIO enabled.

```bash
python app.py
```

The application will be accessible at `http://localhost:5001`.

#### Running the Agent

In a separate terminal window, ensure your virtual environment is activated and run the agent script.

```bash
python agent.py dev
```

The agent connects to the LiveKit room and starts interacting based on the defined role.

