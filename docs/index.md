# Building a Real-time Voice Interface with OpenAI: From Prototype to MVP

A toolkit inspired by the OpenAI Builders Lab to simplify creating real-time, web-based voice interfaces powered by OpenAI's Realtime API and function calls.

## ✨ Challenges and Solutions

* **WebSockets not well suited for longform connections:** The official OpenAI Realtime API toolkit relies on WebSockets, which proved unstable for long-term sessions over HTTP.  The OpenAI team suggested using WebRTC bridges for better stability. The toolkit implements WebRTC with a LiveKit integration.

* **Dynamic UI:** I wanted a dynamic UI that could respond to user input in real-time. This meant connecting the function calls from the model to the front-end functions using remote procedure calls (RPC) over WebRTC. This brings the voice interface to life, allowing users to interact with different functions of the app seamlessly.

* **Architecture:**  A clear separation was needed between the web app's backend, the AI agent's backend, and the front-end.  The toolkit achieves a lightweight design that is modular, has few dependencies, and is easy to use.

* **Roles:** To quickly iterate on the user experience, you need to refine the prompts / instructions of the agent very frequently. That's implemented through an architecture where the 'roles' are separated from the code, and allows to add and modify them very quickly

## 📚 Documentation
| URL   | content   |
|---|---|
|  https://github.com/xbasset/rico-lebot/tree/main/docs/index.md | Main Documentation page  |
|  https://github.com/xbasset/rico-lebot/tree/main/docs/getting_started.md | Getting Started: Install and run the Demo  |
|  https://github.com/xbasset/rico-lebot/tree/main/docs/agent_architecture.md | Technical Architecture Documentation  |
|  https://github.com/xbasset/rico-lebot/tree/main/docs/roles.md | Create, Update and Customize Roles Documentation  |
|  https://github.com/xbasset/rico-lebot/tree/main/CONTRIBUTING | Developer Documentation to contribute to the project  |

